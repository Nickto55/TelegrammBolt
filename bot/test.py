import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os


class ExcelParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel Data Parser")
        self.root.geometry("500x400")

        # --- НАСТРОЙКИ СТРУКТУРЫ ---
        # Здесь вы задаете список стандартных столбцов, с которыми будет работать ваша система
        self.standard_columns = [
            "ID", "Название", "Цена", "Количество", "Описание", "Игнорировать"
        ]

        # Словарь-память: сохраняет выбор пользователя (какой столбец к какому типу относится)
        # Например: {"Наименование товара": "Название"}
        self.column_mapping = {}

        # Структура для сохранения итоговых данных
        self.processed_data = {}

        self.setup_ui()

    def setup_ui(self):
        # Кнопка загрузки файлов
        self.btn_load = tk.Button(self.root, text="Выбрать Excel файл(ы)", command=self.load_files, padx=10, pady=5)
        self.btn_load.pack(pady=20)

        # Текстовое поле для логов
        self.log_text = tk.Text(self.root, height=15, width=55, state=tk.DISABLED)
        self.log_text.pack(pady=10)

    def log(self, message):
        """Вывод сообщений в текстовое поле интерфейса."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def load_files(self):
        filepaths = filedialog.askopenfilenames(
            title="Выберите Excel файлы",
            filetypes=(("Excel files", "*.xlsx *.xls"), ("All files", "*.*"))
        )

        if not filepaths:
            return

        for filepath in filepaths:
            self.log(f"--- Начало обработки: {os.path.basename(filepath)} ---")
            self.process_excel_file(filepath)

        self.log("=== Обработка всех файлов завершена ===")

        # После обработки всех файлов вызываем вашу пустую функцию
        self.custom_data_processing(self.processed_data)

    def process_excel_file(self, filepath):
        filename = os.path.basename(filepath)
        self.processed_data[filename] = {}

        try:
            # Считываем все листы файла
            xls = pd.ExcelFile(filepath)

            for sheet_name in xls.sheet_names:
                self.log(f"Чтение листа: {sheet_name}")
                # Читаем лист. Используем строку 0 как заголовки
                df = pd.read_excel(filepath, sheet_name=sheet_name)

                # Если страница пустая, пропускаем
                if df.empty:
                    self.log(f"Лист {sheet_name} пуст. Пропуск.")
                    continue

                # Обработка столбцов
                mapped_columns = {}
                columns_to_drop = []

                for col in df.columns:
                    col_str = str(col).strip()

                    # Если столбец уже известен
                    if col_str in self.standard_columns:
                        mapped_columns[col] = col_str
                    elif col_str in self.column_mapping:
                        if self.column_mapping[col_str] == "Игнорировать":
                            columns_to_drop.append(col)
                        else:
                            mapped_columns[col] = self.column_mapping[col_str]
                    else:
                        # Неизвестный столбец -> спрашиваем пользователя
                        chosen_type = self.ask_user_for_mapping(col_str, filename, sheet_name)

                        # Сохраняем в память приложения
                        self.column_mapping[col_str] = chosen_type

                        if chosen_type == "Игнорировать":
                            columns_to_drop.append(col)
                        else:
                            mapped_columns[col] = chosen_type

                # Удаляем ненужные столбцы
                df.drop(columns=columns_to_drop, inplace=True)
                # Переименовываем столбцы в стандартные
                df.rename(columns=mapped_columns, inplace=True)

                # Очистка от пустых строк (если все значения NaN)
                df.dropna(how='all', inplace=True)

                # Преобразуем датафрейм в список словарей (построчное чтение)
                # Заменяем значения NaN на None для корректной работы в Python
                sheet_data = df.where(pd.notnull(df), None).to_dict(orient='records')

                # Сохраняем структуру
                self.processed_data[filename][sheet_name] = sheet_data
                self.log(f"Успешно обработано строк: {len(sheet_data)}")

        except Exception as e:
            self.log(f"Ошибка при обработке {filename}: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось обработать файл {filename}.\n{str(e)}")

    def ask_user_for_mapping(self, unknown_col, filename, sheet_name):
        """Создает всплывающее окно для выбора типа неизвестного столбца."""
        top = tk.Toplevel(self.root)
        top.title("Неизвестный столбец")
        top.geometry("400x200")

        # Делаем окно модальным (блокирует основное окно до получения ответа)
        top.transient(self.root)
        top.grab_set()

        lbl = tk.Label(top,
                       text=f"Файл: {filename}\nЛист: {sheet_name}\n\nНайден неизвестный столбец:\n«{unknown_col}»",
                       justify=tk.LEFT)
        lbl.pack(pady=10, padx=20)

        lbl2 = tk.Label(top, text="Выберите, к какому типу его отнести:")
        lbl2.pack()

        # Выпадающий список
        selected_option = tk.StringVar()
        combo = ttk.Combobox(top, textvariable=selected_option, values=self.standard_columns, state="readonly")
        combo.current(0)  # Значение по умолчанию
        combo.pack(pady=10)

        result = [self.standard_columns[0]]

        def on_ok():
            result[0] = combo.get()
            top.destroy()

        btn_ok = tk.Button(top, text="Принять", command=on_ok, width=15)
        btn_ok.pack(pady=10)

        # Ожидаем, пока пользователь закроет окно
        self.root.wait_window(top)

        return result[0]

    def custom_data_processing(self, data):
        """
        ПУСТАЯ ФУНКЦИЯ ДЛЯ ВАШЕЙ ОБРАБОТКИ
        Сюда передается переменная data со всеми считанными таблицами.
        """
        self.log("Запуск пользовательской функции обработки данных...")

        # Пример того, как выглядит структура data (для вашего понимания):
        """
        data = {
            "Таблица1.xlsx": {
                "Лист1": [
                    {"ID": 1, "Название": "Товар А", "Цена": 100},
                    {"ID": 2, "Название": "Товар Б", "Цена": 250}
                ],
                "Лист2": [
                    {"ID": 3, "Название": "Товар В", "Цена": 300}
                ]
            },
            "Таблица2.xlsx": {
                ...
            }
        }
        """

        # Здесь вы можете писать свой код для интеграции с БД, отправки по API и т.д.
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelParserApp(root)
    root.mainloop()
