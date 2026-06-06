import os
import sys

# 1. Находим путь к вашей виртуальной среде (.venv)
venv_path = sys.prefix

# 2. Формируем путь к папке 'plugins', где лежат плагины Qt.
# Путь формируется динамически и зависит от вашей установки PyQt5.
# Пробуем самые частые варианты расположения папки 'plugins'.
possible_paths = [
    os.path.join(venv_path, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins'), # Наиболее частый путь
    os.path.join(venv_path, 'Lib', 'site-packages', 'PyQt5', 'Qt', 'plugins'),   # Альтернативный путь
]
qt_plugins_path = None
for path in possible_paths:
    if os.path.exists(path):
        qt_plugins_path = path
        print(f"Путь к плагинам Qt найден: {qt_plugins_path}")
        break

if qt_plugins_path:
    # Устанавливаем переменные окружения, чтобы Qt знал, где искать плагины
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugins_path
    os.environ['QT_PLUGIN_PATH'] = qt_plugins_path
    print("Переменные QT_QPA_PLATFORM_PLUGIN_PATH и QT_PLUGIN_PATH установлены.")
else:
    print("Путь к плагинам не найден. Ошибка сохранится.")
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer, QTime, Qt
from timer_app_ui import Ui_MainWindow  # сгенерированный из .ui


class TimerApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Инициализация переменных
        self.time = QTime(0, 0, 0, 0)  # текущее отображаемое время
        self.is_running = False  # идёт ли отсчёт
        self.is_timer_mode = False  # False - секундомер, True - таймер
        self.initial_timer_time = QTime(0, 0, 0)

        # Настройка QTimer (обновление каждые 10 мс для сотых долей секунды)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.setInterval(10)  # 10 мс

        # Настройка интерфейса
        self.lcdNumber.setDigitCount(11)  # "00:00:00.00" - 11 символов
        self.lcdNumber.display("00:00:00.00")

        # Привязка сигналов
        self.btnStartPause.clicked.connect(self.start_pause)
        self.btnReset.clicked.connect(self.reset)
        self.comboMode.currentTextChanged.connect(self.mode_changed)

        # Изначально отключаем поле ввода времени (режим секундомера)
        self.lineEditTime.setEnabled(False)
        self.labelHint.setEnabled(False)

    def mode_changed(self, mode):
        """Переключение между секундомером и таймером"""
        self.reset()  # при смене режима сбрасываем всё
        if mode == "Таймер":
            self.is_timer_mode = True
            self.lineEditTime.setEnabled(True)
            self.labelHint.setEnabled(True)
            # Попробуем установить время из lineEditTime
            self.set_timer_from_input()
        else:  # Секундомер
            self.is_timer_mode = False
            self.lineEditTime.setEnabled(False)
            self.labelHint.setEnabled(False)
            self.time = QTime(0, 0, 0, 0)
            self.display_time()

    def set_timer_from_input(self):
        """Считывает время из lineEditTime и устанавливает начальное значение таймера"""
        text = self.lineEditTime.text().strip()
        if not text:
            return
        # Поддерживаем форматы: ММ:СС  или  ЧЧ:ММ:СС
        parts = text.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            self.initial_timer_time = QTime(0, minutes, seconds, 0)
        elif len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            self.initial_timer_time = QTime(hours, minutes, seconds, 0)
        else:
            self.initial_timer_time = QTime(0, 1, 0, 0)  # по умолчанию 1 минута
        self.time = self.initial_timer_time
        self.display_time()

    def display_time(self):
        """Отображает текущее время self.time в формате ЧЧ:ММ:СС.сс"""
        # QTime не хранит сотые доли, но мы можем использовать msec()
        # Для красоты: получаем часы, минуты, секунды и миллисекунды
        h = self.time.hour()
        m = self.time.minute()
        s = self.time.second()
        ms = self.time.msec() // 10  # сотые доли секунды (0-99)
        self.lcdNumber.display(f"{h:02d}:{m:02d}:{s:02d}.{ms:02d}")

    def update_time(self):
        """Вызывается каждые 10 мс по таймеру"""
        if not self.is_running:
            return

        if self.is_timer_mode:
            # Таймер: уменьшаем время на 10 мс
            new_time = self.time.addMSecs(-10)
            if new_time <= QTime(0, 0, 0, 0):
                # Время вышло
                self.time = QTime(0, 0, 0, 0)
                self.display_time()
                self.stop_timer()
                QMessageBox.information(self, "Таймер", "Время вышло!")
                return
            self.time = new_time
        else:
            # Секундомер: увеличиваем время на 10 мс
            self.time = self.time.addMSecs(10)

        self.display_time()

    def start_pause(self):
        """Запуск или остановка отсчёта"""
        if self.is_timer_mode and not self.is_running:
            # При старте таймера перечитываем введённое время
            self.set_timer_from_input()
            if self.time == QTime(0, 0, 0, 0):
                QMessageBox.warning(self, "Таймер", "Установите время больше нуля")
                return

        if self.is_running:
            self.timer.stop()
            self.btnStartPause.setText("Старт")
        else:
            self.timer.start()
            self.btnStartPause.setText("Пауза")
        self.is_running = not self.is_running

    def stop_timer(self):
        """Останавливает таймер и сбрасывает флаг"""
        if self.timer.isActive():
            self.timer.stop()
        self.is_running = False
        self.btnStartPause.setText("Старт")

    def reset(self):
        """Сброс: остановка и обнуление времени в зависимости от режима"""
        self.stop_timer()
        if self.is_timer_mode:
            self.set_timer_from_input()
        else:
            self.time = QTime(0, 0, 0, 0)
        self.display_time()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimerApp()
    window.show()
    sys.exit(app.exec_())