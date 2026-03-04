import customtkinter as ctk
import random
import threading
from plyer import notification
import json
import os

# Настройки по умолчанию
DEFAULT_CONFIG = {
    "min_number": 2,
    "max_number": 9,
    "time_limit": 10,
    "notification_interval": 3600
}

CONFIG_FILE = "config.json"


class MultiplicationApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Умножайка")
        self.geometry("400x550")

        # Загружаем настройки
        self.config = self.load_config()

        # Состояние приложения
        self.notification_active = False
        self.question_active = False
        self.timer_active = False
        self.first_notification = True
        self.notification_trigger = False

        # Данные текущего вопроса
        self.num1 = 0
        self.num2 = 0
        self.correct_answer = 0
        self.time_left = 0
        self.timer_job = None

        # Создаем интерфейс
        self.setup_ui()

        # Привязываем события
        self.bind("<FocusIn>", self.on_focus)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Запускаем проверку уведомлений
        self.check_notification()

    # ========== РАБОТА С НАСТРОЙКАМИ ==========

    def load_config(self):
        """Загрузка настроек из файла"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        """Сохранение настроек в файл"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    # ========== СОЗДАНИЕ ИНТЕРФЕЙСА ==========

    def setup_ui(self):
        """Создание всех элементов интерфейса"""

        # Вкладки
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # Вкладка игры
        self.game_tab = self.tabs.add("Игра")
        self.setup_game_tab()

        # Вкладка настроек
        self.settings_tab = self.tabs.add("Настройки")
        self.setup_settings_tab()

        # Кнопка управления уведомлениями
        self.notification_btn = ctk.CTkButton(
            self,
            text="▶ Запустить уведомления",
            command=self.toggle_notifications,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.notification_btn.pack(pady=10, padx=10, fill="x")

        # Статус уведомлений
        self.status_label = ctk.CTkLabel(
            self,
            text="⏸ Уведомления остановлены",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=5)

    def setup_game_tab(self):
        """Настройка вкладки с игрой"""

        # Статус
        self.game_status = ctk.CTkLabel(
            self.game_tab,
            text="Настройте параметры и запустите уведомления",
            font=("Arial", 12),
            text_color="gray"
        )
        self.game_status.pack(pady=10)

        # Вопрос
        self.question_label = ctk.CTkLabel(
            self.game_tab,
            text="—",
            font=("Arial", 24, "bold")
        )
        self.question_label.pack(pady=20)

        # Поле для ответа
        self.answer_entry = ctk.CTkEntry(
            self.game_tab,
            placeholder_text="Введите ответ",
            width=200,
            height=40,
            font=("Arial", 14)
        )
        self.answer_entry.pack(pady=10)
        self.answer_entry.bind("<Return>", self.check_answer)

        # Кнопка проверки
        self.check_btn = ctk.CTkButton(
            self.game_tab,
            text="Проверить",
            command=self.check_answer,
            height=40,
            font=("Arial", 14)
        )
        self.check_btn.pack(pady=10)

        # Таймер
        self.timer_label = ctk.CTkLabel(
            self.game_tab,
            text="",
            font=("Arial", 16, "bold")
        )
        self.timer_label.pack(pady=10)

        # Результат
        self.result_label = ctk.CTkLabel(
            self.game_tab,
            text="",
            font=("Arial", 14)
        )
        self.result_label.pack(pady=10)

        # Отключаем ввод
        self.disable_game()

    def setup_settings_tab(self):
        """Настройка вкладки с параметрами"""

        # Минимальное число
        ctk.CTkLabel(self.settings_tab, text="Минимальное число:", font=("Arial", 12)).pack(pady=5)
        self.min_entry = ctk.CTkEntry(self.settings_tab, font=("Arial", 12))
        self.min_entry.insert(0, str(self.config["min_number"]))
        self.min_entry.pack(pady=5)

        # Максимальное число
        ctk.CTkLabel(self.settings_tab, text="Максимальное число:", font=("Arial", 12)).pack(pady=5)
        self.max_entry = ctk.CTkEntry(self.settings_tab, font=("Arial", 12))
        self.max_entry.insert(0, str(self.config["max_number"]))
        self.max_entry.pack(pady=5)

        # Время на ответ
        ctk.CTkLabel(self.settings_tab, text="Время на ответ (секунд):", font=("Arial", 12)).pack(pady=5)
        self.time_entry = ctk.CTkEntry(self.settings_tab, font=("Arial", 12))
        self.time_entry.insert(0, str(self.config["time_limit"]))
        self.time_entry.pack(pady=5)

        # Интервал уведомлений
        ctk.CTkLabel(self.settings_tab, text="Интервал уведомлений (секунд):", font=("Arial", 12)).pack(pady=5)
        self.interval_entry = ctk.CTkEntry(self.settings_tab, font=("Arial", 12))
        self.interval_entry.insert(0, str(self.config["notification_interval"]))
        self.interval_entry.pack(pady=5)

        # Кнопка сохранения
        ctk.CTkButton(
            self.settings_tab,
            text="Сохранить настройки",
            command=self.save_settings,
            height=40,
            font=("Arial", 12)
        ).pack(pady=20)

    # ========== УПРАВЛЕНИЕ СОСТОЯНИЕМ ==========

    def disable_game(self):
        """Блокировка ввода в игре"""
        self.answer_entry.configure(state="disabled")
        self.check_btn.configure(state="disabled")

    def enable_game(self):
        """Разблокировка ввода в игре"""
        self.answer_entry.configure(state="normal")
        self.check_btn.configure(state="normal")
        self.answer_entry.focus()

    def disable_settings(self):
        """Блокировка полей настроек"""
        self.min_entry.configure(state="disabled")
        self.max_entry.configure(state="disabled")
        self.time_entry.configure(state="disabled")
        self.interval_entry.configure(state="disabled")

    def enable_settings(self):
        """Разблокировка полей настроек"""
        self.min_entry.configure(state="normal")
        self.max_entry.configure(state="normal")
        self.time_entry.configure(state="normal")
        self.interval_entry.configure(state="normal")

    def stop_timer(self):
        """Остановка таймера"""
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None

    def reset_game(self):
        """Полный сброс игры"""
        self.stop_timer()
        self.question_active = False
        self.timer_active = False
        self.disable_game()
        self.question_label.configure(text="—")
        self.timer_label.configure(text="")
        self.result_label.configure(text="")
        self.game_status.configure(text="Уведомления остановлены")

    # ========== ОБРАБОТКА СОБЫТИЙ ==========

    def toggle_notifications(self):
        """Включение/выключение уведомлений"""
        if not self.notification_active:
            # Включаем
            self.notification_active = True
            self.first_notification = True
            self.notification_btn.configure(
                text="⏸ Остановить уведомления",
                fg_color="red",
                hover_color="darkred"
            )
            self.status_label.configure(text="▶ Уведомления активны")
            self.disable_settings()

            # Запускаем поток
            thread = threading.Thread(target=self.notification_loop, daemon=True)
            thread.start()
        else:
            # Выключаем
            self.notification_active = False
            self.notification_btn.configure(text="▶ Запустить уведомления")
            self.status_label.configure(
                text="⏸ Уведомления остановлены",
                text_color="gray"
            )
            self.enable_settings()
            self.reset_game()

    def save_settings(self):
        """Сохранение настроек"""
        if self.notification_active:
            self.result_label.configure(
                text="Сначала остановите уведомления!",
                text_color="red"
            )
            return

        try:
            self.config["min_number"] = int(self.min_entry.get())
            self.config["max_number"] = int(self.max_entry.get())
            self.config["time_limit"] = int(self.time_entry.get())
            self.config["notification_interval"] = int(self.interval_entry.get())
            self.save_config()
            self.result_label.configure(text="Настройки сохранены!", text_color="green")
        except ValueError:
            self.result_label.configure(text="Ошибка: введите числа!", text_color="red")

    # ========== УВЕДОМЛЕНИЯ ==========

    def notification_loop(self):
        """Цикл отправки уведомлений"""
        while self.notification_active:
            # Пропускаем первое
            if self.first_notification:
                self.first_notification = False
            else:
                self.send_notification()

            # Ждем завершения вопроса
            while self.notification_active:
                threading.Event().wait(0.1)
                if not self.question_active and not self.first_notification:
                    break

            # Ждем интервал
            if self.notification_active:
                threading.Event().wait(self.config["notification_interval"])

    def send_notification(self):
        """Отправка уведомления"""
        try:
            self.notification_trigger = True
            notification.notify(
                title="🧮 Умножайка",
                message="Пора вспомнить таблицу умножения!",
                app_name="Умножайка",
                timeout=10
            )
        except:
            pass

    def check_notification(self):
        """Проверка триггера уведомления"""
        if self.notification_trigger:
            self.notification_trigger = False
            self.show_window()
            if self.notification_active and not self.question_active:
                self.new_question()
        self.after(100, self.check_notification)

    def show_window(self):
        """Показ окна"""
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_focus(self, event):
        """При получении фокуса"""
        pass

    # ========== ИГРОВАЯ ЛОГИКА ==========

    def new_question(self):
        """Создание нового вопроса"""
        self.stop_timer()

        # Генерируем числа
        self.num1 = random.randint(self.config["min_number"], self.config["max_number"])
        self.num2 = random.randint(self.config["min_number"], self.config["max_number"])
        self.correct_answer = self.num1 * self.num2
        self.question_active = True

        # Показываем вопрос
        self.tabs.set("Игра")

        # Форматируем второе число, если оно отрицательное
        num1_str = str(self.num1)
        num2_str = f"({self.num2})" if self.num2 < 0 else str(self.num2)

        self.question_label.configure(text=f"{num1_str} × {num2_str} = ?")
        self.game_status.configure(text="Решай пример!")
        self.enable_game()
        self.answer_entry.delete(0, "end")
        self.result_label.configure(text="")

        # Запускаем таймер
        self.time_left = self.config["time_limit"]
        self.timer_active = True
        self.update_timer()

    def update_timer(self):
        """Обновление таймера"""
        if not self.notification_active or not self.question_active:
            self.stop_timer()
            return

        if self.timer_active and self.time_left > 0:
            self.timer_label.configure(text=f"⏱ {self.time_left} сек")
            self.time_left -= 1
            self.timer_job = self.after(1000, self.update_timer)
        elif self.timer_active and self.time_left <= 0:
            self.timer_active = False
            self.question_active = False

            if self.notification_active:
                self.timer_label.configure(text="⏰ Время вышло!")
                self.result_label.configure(
                    text=f"Правильный ответ: {self.correct_answer}",
                    text_color="red"
                )
            self.disable_game()

    def check_answer(self, event=None):
        """Проверка ответа"""
        if not self.timer_active or not self.question_active or not self.notification_active:
            return

        try:
            answer = int(self.answer_entry.get())
            if answer == self.correct_answer:
                self.result_label.configure(text="✅ Правильно! Молодец!", text_color="green")
                self.timer_label.configure(text="🎉 Отлично!")
            else:
                self.result_label.configure(
                    text=f"❌ Неправильно. Правильный ответ: {self.correct_answer}",
                    text_color="orange"
                )
                self.timer_label.configure(text="😔 Попробуй в следующий раз")

            self.timer_active = False
            self.question_active = False
            self.stop_timer()
            self.disable_game()
        except ValueError:
            self.result_label.configure(text="Введите число!", text_color="red")

    def on_close(self):
        """При закрытии окна"""
        self.notification_active = False
        self.stop_timer()
        self.destroy()

ctk.set_appearance_mode("light")
app = MultiplicationApp()

# Добавить иконку приложению
import pathlib, os.path

appdir = pathlib.Path(__file__).parent.resolve()
app.iconbitmap(os.path.join(appdir, 'icon.ico'))

app.mainloop()