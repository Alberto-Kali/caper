from PyQt6 import *
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import QMessageBox, QDialog, QTableWidgetItem
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtCore import Qt

from PyQt6.uic import *

from random import *
from math import *
from time import *
import threading
import os
import sqlite3
from datetime import datetime


def numss(n: int):
    style = ""
    if n == 1:
        style = " color: #5A9BD5;"
    elif n == 2:
        style = " color: #70AD47;"
    elif n == 3:
        style = " color: #FF6B6B;"
    elif n == 4:
        style = " color: #9966CC;"
    elif n == 5:
        style = " color: #FFC107;"
    elif n == 6:
        style = " color: #4ECDC4;"
    elif n == 7:
        style = " color: #8E44AD;"
    elif n == 8:
        style = " color: #95A5A6;"

    return "font-weight: bold;" + style

# Классы
class GameDatabase:
    def __init__(self, db_name='game_history.db'):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    result TEXT,
                    bombs INTEGER,
                    rows INTEGER,
                    columns INTEGER
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    rows INTEGER,
                    columns INTEGER,
                    bombs INTEGER
                )
            ''')
            # Вставляем начальные настройки, если таблица пуста
            cursor.execute('SELECT COUNT(*) FROM settings')
            if cursor.fetchone()[0] == 0:
                cursor.execute('INSERT INTO settings (id, rows, columns, bombs) VALUES (1, 9, 9, 10)')
            conn.commit()

    def add_game(self, result, bombs, rows, columns):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO games 
                (date, result, bombs, rows, columns) 
                VALUES (?, ?, ?, ?, ?)
            ''', (current_date, result, bombs, rows, columns))
            conn.commit()

    def get_all_games(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM games ORDER BY date DESC')
            return cursor.fetchall()

    def delete_game(self, game_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM games WHERE id = ?', (game_id,))
            conn.commit()

    def get_settings(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT columns, rows, bombs FROM settings WHERE id = 1')
            return cursor.fetchone()

    def save_settings(self, rows, columns, bombs):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE settings SET rows = ?, columns = ?, bombs = ? WHERE id = 1', (rows, columns, bombs))
            conn.commit()

    def update_game_info(self, game_id, date, result, bombs, rows, columns):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE games 
                SET date = ?, result = ?, bombs = ?, rows = ?, columns = ? 
                WHERE id = ?
            ''', (date, result, bombs, rows, columns, game_id))
            conn.commit()


class DatabaseEditorDialog(QDialog):
    def __init__(self):
        super().__init__()
        loadUi('ui/db.ui', self)
        
        self.db = GameDatabase()
        self.load_games()

        # Подключаем кнопки
        self.deleteButton.clicked.connect(self.delete_selected_game)
        self.updateButton.clicked.connect(self.save_changes)

        # Делаем таблицу редактируемой
        self.tableWidget.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)

    def load_games(self):
        games = self.db.get_all_games()
        self.tableWidget.setRowCount(len(games))
        
        for row, game in enumerate(games):
            for col, value in enumerate(game):
                item = QTableWidgetItem(str(value))
                # Первый столбец (ID) делаем нередактируемым
                if col == 0:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tableWidget.setItem(row, col, item)

    def delete_selected_game(self):
        current_row = self.tableWidget.currentRow()
        if current_row >= 0:
            game_id = self.tableWidget.item(current_row, 0).text()
            self.db.delete_game(int(game_id))
            self.load_games()

    def save_changes(self):
        # Проходим по всем строкам таблицы
        for row in range(self.tableWidget.rowCount()):
            # Получаем ID игры (первый столбец)
            game_id = self.tableWidget.item(row, 0).text()
            
            # Собираем новые данные об игре
            date = self.tableWidget.item(row, 1).text()
            result = self.tableWidget.item(row, 2).text()
            bombs = int(self.tableWidget.item(row, 3).text())
            rows = int(self.tableWidget.item(row, 4).text())
            columns = int(self.tableWidget.item(row, 5).text())

            # Обновляем информацию в базе данных
            self.db.update_game_info(int(game_id), date, result, bombs, rows, columns)

        # Перезагружаем данные из базы
        self.load_games()
        
        # Показываем сообщение об успешном сохранении
        QMessageBox.information(self, "Успех", "Изменения сохранены")


class about(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("ui/about.ui", self)
        with open("ui/style.css", "r") as fh:
            self.setStyleSheet(fh.read())
        self.setWindowIcon(QIcon("./icons/information.png"))
        self.setWindowTitle("Информация")
        self.ok.clicked.connect(lambda: self.close())


class opt(QDialog):
    settings_changed = pyqtSignal(int, int, int)
    def __init__(self, game_db, parent=None):
        super().__init__()
        self.game_db = game_db  # Передаем экземпляр базы данных

        self.pos_x = 0
        self.pos_y = 0
        self.bombs = 0

        loadUi("ui/option.ui", self)
        self.setFixedSize(QSize(365, 197))
        self.setWindowIcon(QIcon("./icons/settings.png"))

        self.GoBack.clicked.connect(lambda: self.close())

        self.rb1.toggled.connect(lambda: self.radio(1))
        self.rb2.toggled.connect(lambda: self.radio(2))
        self.rb3.toggled.connect(lambda: self.radio(3))
        self.rb4.toggled.connect(lambda: self.radio(4))
        self.rb5.toggled.connect(lambda: self.radio(5))

        self.s1.valueChanged.connect(lambda: self.slider_ch(1))
        self.s2.valueChanged.connect(lambda: self.slider_ch(2))
        self.s3.valueChanged.connect(lambda: self.slider_ch(3))

        self.s1.setMinimum(5)
        self.s2.setMinimum(5)
        self.s3.setMinimum(9)

        self.s2.setMaximum(27)
        self.s3.setMaximum(50)

        self.s2.setValue(9)
        self.s3.setValue(9)
        self.s1.setMinimum(10)
        self.rb1.setChecked(1)

        # Добавляем обработчик для кнопки Apply
        self.apply.clicked.connect(self.save_settings)

    def save_settings(self):
        # Сохраняем настройки в базу данных
        self.game_db.save_settings(
            rows=self.pos_y, 
            columns=self.pos_x, 
            bombs=self.bombs
        )
        
        # Испускаем сигнал с новыми настройками
        self.settings_changed.emit(self.pos_x, self.pos_y, self.bombs)
        self.close()

    def slider1_update(self):
        max = (self.pos_x * self.pos_y) // 3
        self.s1.setMinimum(5)
        self.s1.setMaximum(max)
        if max < self.bombs:
            self.bombs = max
            self.s1.setValue(max)

    def update_lcd(self):
        self.lcd1.display(self.bombs)
        self.lcd2.display(self.pos_y)
        self.lcd3.display(self.pos_x)

    def update_slider(self, b, x, y):
        self.s2.setValue(y)
        self.s3.setValue(x)
        self.s1.setMinimum(5)
        self.s1.setMaximum((x * y) // 3)
        self.s1.setValue(b)

    def slider_ch(self, s):
        if s == 1:
            self.bombs = self.s1.value()
            self.lcd1.display(self.bombs)

        elif s == 2:
            self.pos_y = self.s2.value()
            self.slider1_update()
            self.update_lcd()
        elif s == 3:
            self.pos_x = self.s3.value()
            self.slider1_update()
            self.update_lcd()

    def radio(self, n: int):
        if n in [1, 2, 3, 4]:
            if n == 1:
                self.pos_x, self.pos_y, self.bombs = 9, 9, 10
            elif n == 2:
                self.pos_x, self.pos_y, self.bombs = 16, 16, 40
            elif n == 3:
                self.pos_x, self.pos_y, self.bombs = 30, 16, 99
            elif n == 4:
                self.pos_x, self.pos_y, self.bombs = 36, 25, 150
            self.update_slider(self.bombs, self.pos_x, self.pos_y)
            self.slider_state(0)
            self.update_lcd()

        else:
            self.slider_state(1)
            self.slider1_update()
            self.update_slider(self.bombs, self.pos_x, self.pos_y)

    def slider_state(self, n):
        if n:
            self.s1.setEnabled(True)
            self.s2.setEnabled(True)
            self.s3.setEnabled(True)

            self.l1.setEnabled(True)
            self.l2.setEnabled(True)
            self.l3.setEnabled(True)
        else:
            self.s1.setEnabled(False)
            self.s2.setEnabled(False)
            self.s3.setEnabled(False)

            self.l1.setEnabled(False)
            self.l2.setEnabled(False)
            self.l3.setEnabled(False)


class ResetButton(QPushButton):
    def __init__(self):
        super().__init__()

        self.setIcon(QIcon("./icons/game.png"))

        self.setIconSize(QtCore.QSize(60, 26))
        self.clicked.connect(self.Reset)

    def Reset(self, btns=1):
        if btns:
            pass
        for y in range(window.sizeY):
            for x in range(window.sizeX):
                window.items[y][x].SetVal(None)
                window.items[y][x].setText(" ")
                window.items[y][x].setEnabled(True)
                window.items[y][x].Flag(0)

        window.FirstMove = 1
        window.ingame = 1
        window.BombRest = window.sizeY * window.sizeX - window.sizeBomb
        window.FlagRest = window.sizeBomb
        window.DispBomb.display(window.FlagRest)
        window.ClearBombs()
        window.DispTime.reset()
        self.setIcon(QIcon("./icons/game.png"))

    def win(self):
        self.setIcon(QIcon("./icons/win.png"))

    def lose(self):
        self.setIcon(QIcon("./icons/lose.png"))


class lcd(QLCDNumber):
    def __init__(self):
        super().__init__()


class timer(lcd):
    def __init__(self):
        super().__init__()
        self.__counter = 0

    def reset(self):
        self.display(0)
        self.__counter = 0

    def GetScore(self):
        return self.__counter

    def inc(self):
        while (not window.FirstMove) and window.ingame:
            sleep(1)
            self.__counter += 1
            self.display(self.__counter)


class btn(QPushButton):
    def __init__(self, x, y):
        super().__init__()
        self.__value = None
        self.__flag = 0
        self.x, self.y = x, y

        self.setText(" ")
        self.setEnabled(True)
        self.setFixedSize(25, 25)

    def mousePressEvent(self, event):
        if window.ingame:
            if event.button() == Qt.MouseButton.LeftButton:
                window.rec_reveal(self.x, self.y, 1)

            elif event.button() == Qt.MouseButton.RightButton:
                if not self.__flag:
                    window.FlagRest -= 1
                    window.DispBomb.display(window.FlagRest)
                    self.Flag(1)
                else:
                    window.FlagRest += 1
                    window.DispBomb.display(window.FlagRest)
                    self.Flag(0)

    def Flag(self, b):
        if b:
            self.__flag = 1
            self.setText("")
            self.setIcon(QIcon("./icons/flag.png"))
            self.setIconSize(QtCore.QSize(20, 20))
        else:
            self.__flag = 0
            self.setText(" ")
            self.setIcon(QIcon(""))

    def GetFlag(self):
        return self.__flag

    def SetVal(self, val):
        self.__value = val
        self.setStyleSheet(numss(val))

    def GetVal(self):
        return self.__value


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Переменные
        self.FirstMove = 1
        self.ingame = 1
        self.option_window = 0

        self.game_db = GameDatabase()

        # Загрузка настроек из базы данных
        settings = self.game_db.get_settings()
        self.sizeX, self.sizeY, self.sizeBomb = settings if settings else (9, 9, 10)
        self.BombRest = self.sizeX * self.sizeY - self.sizeBomb
        self.FlagRest = self.sizeBomb

        self.items = [[btn(x, y) for x in range(self.sizeX)] for y in range(self.sizeY)]
        self.__bombs = []
        
        # Динамическое определение размера окна
        self.setFixedSize(self.calculateWindowSize())
        
        self.setWindowTitle("Сапёр")
        self.setWindowIcon(QIcon("./icons/mine.png"))

        with open("ui/style.css", "r") as fh:
            self.setStyleSheet(fh.read())
        self.toolbar = QToolBar("Главное меню")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        self.settings = QAction("Настройки", self)
        self.settings.triggered.connect(self.optins_win)
        self.toolbar.addAction(self.settings)
        self.about = QAction("Помощь", self)
        self.about.triggered.connect(lambda: os.system(".\\какиграть.html"))
        self.toolbar.addAction(self.about)
        self.about = QAction("Инфо", self)
        self.about.triggered.connect(self.about_win)
        self.toolbar.addAction(self.about)
        self.DispTime = timer()
        self.MButton = ResetButton()

        self.DispBomb = lcd()
        self.DispBomb.display(str(self.FlagRest))

        self.spacer1 = QSpacerItem(
            20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.spacer2 = QSpacerItem(
            20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        layout1 = QGridLayout()
        layout1.addWidget(self.DispTime, 0, 0)
        layout1.addWidget(self.MButton, 0, 2)
        layout1.addWidget(self.DispBomb, 0, 4)
        layout1.setObjectName("l1")

        layout1.addItem(self.spacer1, 0, 1)
        layout1.addItem(self.spacer2, 0, 3)

        # layout 2
        self.layout2 = QGridLayout()
        self.layout2.setSpacing(0)
        self.layout2.setContentsMargins(0, 0, 0, 0)
        self.layout2.setObjectName("l2")

        for x in range(self.sizeX):
            for y in range(self.sizeY):
                self.layout2.addWidget(self.items[y][x], y + 1, x + 1)

        # layout 3
        self.MainLayout = QVBoxLayout()
        self.MainLayout.addLayout(layout1)
        self.MainLayout.addLayout(self.layout2)
        self.MainLayout.setObjectName("l3")

        widget = QWidget()
        widget.setLayout(self.MainLayout)
        self.setCentralWidget(widget)

        self.game_db = GameDatabase()

        db_action = QAction('История игр', self)
        db_action.triggered.connect(self.open_database_editor)
        self.toolbar.addAction(db_action)
    
    # Функции

    def calculateWindowSize(self):
        # Метод для динамического расчета размера окна в зависимости от количества строк и столбцов
        width = 50 + (self.sizeX * 25)   # Базовая ширина + ширина кнопок
        height = 120 + (self.sizeY * 25)  # Базовая высота + высота кнопок
        return QSize(width, height)

    def NewSettings(self, NewX, NewY, NewB):
        if NewB == self.sizeBomb and NewX == self.sizeX and NewY == self.sizeY:
            self.MButton.Reset()
            return

        # Сохранение новых настроек в базу данных
        # Важно: передаем параметры в правильном порядке (rows, columns, bombs)
        self.game_db.save_settings(NewY, NewX, NewB)

        for x in range(self.sizeX):
            for y in range(self.sizeY):
                self.layout2.removeWidget(self.items[y][x])
                self.items[y][x].deleteLater()
        self.items.clear()
        self.sizeX, self.sizeY, self.sizeBomb = NewX, NewY, NewB
        self.BombRest = self.sizeX * self.sizeY - self.sizeBomb
        self.FlagRest = self.sizeBomb
        
        self.items = [[btn(x, y) for x in range(self.sizeX)] for y in range(self.sizeY)]
        for x in range(self.sizeX):
            for y in range(self.sizeY):
                self.layout2.addWidget(self.items[y][x], y + 1, x + 1)
        
        self.MButton.Reset()
        
        # Динамическое изменение размера окна
        self.setFixedSize(self.calculateWindowSize())
        self.move(QPoint())

    def open_database_editor(self):
        editor = DatabaseEditorDialog()
        editor.exec()

    def save_game_result(self, result, bombs, rows, columns):
        self.game_db.add_game(result, bombs, rows, columns)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_F7 and not self.option_window:
            self.optins_win()

    def NewSettings(self, NewX, NewY, NewB):
        if NewB == self.sizeBomb and NewX == self.sizeX and NewY == self.sizeY:
            self.MButton.Reset()
            return

        for x in range(self.sizeX):
            for y in range(self.sizeY):
                self.layout2.removeWidget(self.items[y][x])
                self.items[y][x].deleteLater()
        self.items.clear()
        self.sizeX, self.sizeY, self.sizeBomb = NewX, NewY, NewB
        self.items = [[btn(x, y) for x in range(self.sizeX)] for y in range(self.sizeY)]
        for x in range(self.sizeX):
            for y in range(self.sizeY):
                self.layout2.addWidget(self.items[y][x], y + 1, x + 1)
        self.MButton.Reset()
        self.setFixedSize(QSize())
        self.move(QPoint())

    # ----------------------------------------------------------------------
    def optins_win(self):
        self.option_window = 1
        self.OptWin = opt(self.game_db)
        
        # Подключаем сигнал к методу NewSettings
        self.OptWin.settings_changed.connect(self.NewSettings)
        
        self.OptWin.exec()
        self.option_window = 0

    def about_win(self):
        self.option_window = 1
        self.AboutWin = about()
        self.AboutWin.exec()
        self.option_window = 0

    # ----------------------------------------------------------------------

    def rec_reveal(self, x=0, y=0, first_call=0):

        if self.FirstMove:
            self.FirstMove = 0
            self.MakeBombs(x, y)
            self.SetValues()
            ThTime = threading.Thread(target=self.DispTime.inc).start()

        if self.items[y][x].GetFlag():
            return

        if self.items[y][x].GetVal() == "*":
            if first_call:
                self.lose()
            return

        if self.items[y][x].text() != " ":
            return

        elif int(self.items[y][x].GetVal()) > 0:
            self.items[y][x].setText(str(self.items[y][x].GetVal()))
            self.items[y][x].setEnabled(False)
            window.BombRest -= 1
            if not window.BombRest:
                self.win()
            return

        elif self.items[y][x].GetVal() == 0:
            self.items[y][x].setText("  ")
            self.items[y][x].setEnabled(False)
            window.BombRest -= 1
            if not window.BombRest:
                self.win()

            if x + 1 < self.sizeX:
                self.rec_reveal(x + 1, y)
            if x - 1 >= 0:
                self.rec_reveal(x - 1, y)
            if y + 1 < self.sizeY:
                self.rec_reveal(x, y + 1)
            if y - 1 >= 0:
                self.rec_reveal(x, y - 1)

            if x - 1 >= 0 and y - 1 >= 0:
                self.rec_reveal(x - 1, y - 1)
            if x + 1 < self.sizeX and y + 1 < self.sizeY:
                self.rec_reveal(x + 1, y + 1)
            if x - 1 >= 0 and y + 1 < self.sizeY:
                self.rec_reveal(x - 1, y + 1)
            if x + 1 < self.sizeX and y - 1 >= 0:
                self.rec_reveal(x + 1, y - 1)

    def SetValues(self):
        for y in range(self.sizeY):
            for x in range(self.sizeX):

                if self.items[y][x].GetVal() == "*":
                    continue
                count = 0

                if y >= 1 and x >= 1 and self.items[y - 1][x - 1].GetVal() == "*":
                    count += 1

                if y >= 1 and self.items[y - 1][x].GetVal() == "*":
                    count += 1

                if (
                    y >= 1
                    and (x + 1) < self.sizeX
                    and self.items[y - 1][x + 1].GetVal() == "*"
                ):
                    count += 1

                # ----------------------------------------------------------------------

                if (
                    (y + 1) < self.sizeY
                    and x >= 1
                    and self.items[y + 1][x - 1].GetVal() == "*"
                ):
                    count += 1

                if (y + 1) < self.sizeY and self.items[y + 1][x].GetVal() == "*":
                    count += 1

                if (
                    (y + 1) < self.sizeY
                    and (x + 1) < self.sizeX
                    and self.items[y + 1][x + 1].GetVal() == "*"
                ):
                    count += 1

                # ----------------------------------------------------------------------

                if x >= 1 and self.items[y][x - 1].GetVal() == "*":
                    count += 1

                if (x + 1) < self.sizeX and self.items[y][x + 1].GetVal() == "*":
                    count += 1

                self.items[y][x].SetVal(count)

    def MakeBombs(self, x, y):
        c = self.sizeBomb
        while c:
            tempx, tempy = randint(0, self.sizeX - 1), randint(0, self.sizeY - 1)

            if abs(tempy - y) <= 1 and abs(tempx - x) <= 1:
                continue
            if self.items[tempy][tempx].GetVal() != "*":
                self.items[tempy][tempx].SetVal("*")
                self.__bombs.append([tempy, tempx])
                c -= 1

    def ClearBombs(self):
        window.__bombs.clear()

    def lose(self):
        self.ingame = 0
        for x in self.__bombs:
            window.items[x[0]][x[1]].setText("")
            window.items[x[0]][x[1]].setIcon(QIcon("./icons/mine.png"))
            window.items[x[0]][x[1]].setIconSize(QtCore.QSize(16, 16))
        self.MButton.lose()
        
        # Сохранение результата игры
        self.save_game_result("Проигрыш", self.sizeBomb, self.sizeY, self.sizeX)

    def win(self):
        self.ingame = 0
        for x in self.__bombs:
            self.DispBomb.display(0)
            window.items[x[0]][x[1]].setText("")
            window.items[x[0]][x[1]].setIcon(QIcon("./icons/flag.png"))
            window.items[x[0]][x[1]].setIconSize(QtCore.QSize(20, 20))
            self.MButton.win()
        
        # Сохранение результата игры
        self.save_game_result("Победа", self.sizeBomb, self.sizeY, self.sizeX)


# Main
app = QApplication([])
window = MainWindow()
window.show()
app.exec()
