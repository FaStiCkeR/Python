import calendar
import math
import os
import re
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, messagebox, simpledialog

import pandas as pd
from gtts import gTTS


def user_birthdate(birth_date_in_str):
    """
    Функция принимает строку с датой (из модального окна tkinter),
    проверяет формат и существование даты.
    Если дата некорректна — вызывает ValueError.
    :param birth_date_in_str: str — дата в формате YYYY-MM-DD
    :return delta_in_days: int — возраст в днях
    :return weekday_rus: str — день недели с заглавной буквы
    """
    if re.match(r"^\d{4}-\d{2}-\d{2}$", birth_date_in_str):
        try:
            birth_date = datetime.strptime(birth_date_in_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Дата не существует. Попробуйте снова.")
    else:
        raise ValueError("Неправильный формат. Используйте YYYY-MM-DD.")

    today = datetime.now().date()
    delta_in_days = (today - birth_date.date()).days

    # Получаем день недели (0 = понедельник)
    weekday_in_english = calendar.weekday(birth_date.year, birth_date.month, birth_date.day)

    rus_weekdays_dict = {
        0: "понедельник",
        1: "вторник",
        2: "среда",
        3: "четверг",
        4: "пятница",
        5: "суббота",
        6: "воскресенье"
    }

    return delta_in_days, rus_weekdays_dict[weekday_in_english].title()


def loading_and_preparing_info():
    """
    Функция загружает файл `orders.csv` с помощью `pandas.read_csv`, выполняет проверку типов данных,
    обрабатывает пропущенные значения, удаляет некорректные записи и преобразует столбец с датой.
    При ошибках выводит понятное сообщение.
    :return df_prepared: pandas.DataFrame
    """
    try:
        df_orders = pd.read_csv('orders.csv')
        print("Файл orders.csv успешно загружен.")
        print("Первые 5 строк:")
        print(df_orders.head())

        # Преобразование даты
        date_col = 'order_date'
        if date_col not in df_orders.columns:
            raise ValueError(f"Столбец '{date_col}' не найден в файле!")

        df_orders[date_col] = pd.to_datetime(df_orders[date_col], errors='coerce')

        # Проверка типов
        print("\nТипы данных:")
        print(df_orders.dtypes)

        # Обработка пропусков
        print(f"\nПропущенные значения до обработки:\n{df_orders.isnull().sum()}")
        df_orders = df_orders.dropna(subset=[date_col])  # удаляем строки с некорректной датой

        # Удаление некорректных записей
        df_orders = df_orders.drop_duplicates()
        df_orders = df_orders[df_orders['price_per_unit'] >= 0]
        df_orders = df_orders[df_orders['quantity'] > 0]

        print(f"\nПропущенные значения после обработки:\n{df_orders.isnull().sum()}")
        print(f"\nПосле очистки осталось строк: {len(df_orders):,}")

        df_orders.to_csv('orders_prepared.csv', index=False)
        print("Подготовленные данные сохранены в orders_prepared.csv")

        return df_orders

    except FileNotFoundError:
        print("Файл orders.csv не найден!")
        return None
    except Exception as e:
        print(f"Ошибка при подготовке данных: {e}")
        return None


def calculation_of_indicators():
    """
    Функция добавляет три новых столбца и сохраняет результат.
    :return df_calculated: pandas.DataFrame
    """
    try:
        df = pd.read_csv('orders_prepared.csv')

        # 1. Общая стоимость заказа
        df['order_cost'] = (df['quantity'] * df['price_per_unit']).round(2)

        # 2. Итоговая стоимость с учётом скидки
        df['order_cost_with_discount'] = (
                df['order_cost'] * (1 - df['discount_percent'] / 100)
        ).round(2)

        # 3. Признак успешной продажи (числовой 1/0 — важно для анализа!)
        df['successful_sale'] = (df['status'].str.lower() == 'delivered').astype(int)

        df.to_csv('orders_calculated.csv', index=False)
        print("Показатели рассчитаны и сохранены в orders_calculated.csv")
        return df

    except Exception as e:
        print(f"Ошибка при расчёте показателей: {e}")
        raise


def data_analyse():
    """
    Функция выполняет анализ:
    - общий доход
    - доход по категориям
    - топ-10 товаров
    - уровень возвратов
    :return analysis_results: dict
    """
    try:
        df = pd.read_csv('orders_calculated.csv')

        total_income = df['order_cost_with_discount'].sum()

        income_by_category = (
            df.groupby('category')['order_cost_with_discount'].sum()
            if 'category' in df.columns else pd.Series(dtype=float)
        )

        top_products = (
            df.groupby('product_name')['order_cost_with_discount'].sum().nlargest(10)
            if 'product_name' in df.columns else pd.Series(dtype=float)
        )

        return_rate = (1 - df['successful_sale'].mean()) * 100

        analysis_results = {
            'total_income': round(total_income, 2),
            'income_by_category': income_by_category,
            'top_products': top_products,
            'return_rate_percent': round(return_rate, 2)
        }

        print("Анализ данных выполнен")
        return analysis_results

    except Exception as e:
        print(f"Ошибка анализа: {e}")
        raise


def math_calculation():
    """
    Три математических расчёта с использованием math:
    1. Оценка времени доставки (на основе среднего количества товаров)
    2. Нормализация средней стоимости (sqrt)
    3. Проверка и замена NaN
    :return math_results: dict
    """
    try:
        df = pd.read_csv('orders_calculated.csv')

        # 1. Оценка времени доставки
        avg_quantity = df['quantity'].mean()
        distance_km = avg_quantity * 10  # условная формула
        time_delivery_days = math.ceil(distance_km / 50)

        # 2. Нормализация средней стоимости
        mean_cost = df['order_cost_with_discount'].mean()
        normalized_cost = math.sqrt(mean_cost) if mean_cost > 0 else 0

        # 3. Количество NaN (проверка math.isnan на float)
        nan_count = 0
        for col in df.select_dtypes(include='number').columns:
            nan_count += df[col].isna().sum()

        math_results = {
            'delivery_time_days': time_delivery_days,
            'normalized_cost': round(normalized_cost, 2),
            'nan_replaced_count': nan_count
        }

        print("Математические расчёты выполнены")
        return math_results

    except Exception as e:
        print(f"Ошибка математических расчётов: {e}")
        raise


def form_report(delta_in_days, weekday, analysis_results, math_results):
    """
    Формирует текстовый отчёт и сохраняет его в report.txt + CSV сводку.
    :return report_text: str
    """
    try:
        report_text = f"""ИТОГОВЫЙ ОТЧЁТ ПО ЗАКАЗАМ

    ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
Возраст: {delta_in_days} дней
День рождения: {weekday}

    АНАЛИЗ ЗАКАЗОВ
Общий доход: {analysis_results['total_income']} лей
Уровень возвратов: {analysis_results['return_rate_percent']}% 

Доход по категориям:
{analysis_results['income_by_category'].to_string()}

Топ-10 товаров:
{analysis_results['top_products'].to_string()}

    МАТЕМАТИЧЕСКИЕ РАСЧЁТЫ
Примерное время доставки: {math_results['delivery_time_days']} дней
Нормализованная средняя стоимость: {math_results['normalized_cost']}
Найдено NaN значений: {math_results['nan_replaced_count']}

Отчёт сформирован.
"""

        # Сохраняем текст
        with open('report.txt', 'w', encoding='utf-8') as f:
            f.write(report_text)

        # Сохраняем сводку в CSV
        summary = pd.DataFrame({
            'Показатель': ['Общий доход', 'Уровень возвратов %', 'Время доставки (дн)', 'Норм. стоимость'],
            'Значение': [
                analysis_results['total_income'],
                analysis_results['return_rate_percent'],
                math_results['delivery_time_days'],
                math_results['normalized_cost']
            ]
        })
        summary.to_csv('report_summary.csv', index=False)

        print("Отчёт сохранён в report.txt и report_summary.csv")
        return report_text

    except Exception as e:
        print(f"Ошибка формирования отчёта: {e}")
        raise


def voice_report(report_text):
    """
    Преобразует текст отчёта в аудио report.mp3 с помощью gTTS.
    :return audio_path: str
    """
    if not report_text or not report_text.strip():
        raise ValueError("Текст отчёта пустой!")

    try:
        tts = gTTS(text=report_text, lang='ru', slow=False)
        tts.save('report.mp3')
        print("Аудио-отчёт сохранён в report.mp3")
        return 'report.mp3'
    except Exception as e:
        print(f"Ошибка озвучивания: {e}")
        raise


def play_report(filename='report.mp3'):
    """
        Открывает MP3-файл программой, ассоциированной в системе.
        Файл ищется в той же папке, где лежит скрипт.
        Пример: open_mp3("melody.mp3")
        """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, filename)

    if not os.path.exists(full_path):
        print(f"Файл {filename} не найден в папке со скриптом")
        return

    try:
        if sys.platform == "win32":
            os.startfile(full_path)  # Windows
        elif sys.platform == "darwin":
            subprocess.run(["open", full_path])  # macOS
        else:
            subprocess.run(["xdg-open", full_path])  # Linux
        print(f"Открываю: {filename}")
    except Exception as e:
        print(f"Не удалось открыть файл: {e}")


def main_interface():
    """
    Графический интерфейс tkinter, который объединяет все функции.
    """
    root = tk.Tk()
    root.title("Анализ заказов")
    root.geometry("900x700")

    text_area = scrolledtext.ScrolledText(root, width=100, height=30)
    text_area.pack(pady=10)

    def run_full_analysis():
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, "Запуск полного анализа...\n\n")

        try:
            # 1. Дата рождения через модальное окно tkinter
            delta_days = None
            while delta_days is None:
                birth_date_in_str = tk.simpledialog.askstring(
                    title="Дата рождения пользователя",
                    prompt="Введите свою дату рождения в формате YYYY-MM-DD:"
                )
                if birth_date_in_str is None:  # пользователь нажал Cancel
                    text_area.insert(tk.END, "Ввод даты рождения отменён.\n")
                    return

                try:
                    delta_days, weekday = user_birthdate(birth_date_in_str)
                    text_area.insert(tk.END, f"Данные пользователя: {delta_days} дней, {weekday}\n\n")
                except ValueError as e:
                    messagebox.showerror("Ошибка ввода даты", str(e))
                    # продолжаем цикл — окно появится снова

            # 2. Подготовка данных
            loading_and_preparing_info()
            text_area.insert(tk.END, "Данные подготовлены\n")

            # 3. Расчёт показателей
            calculation_of_indicators()
            text_area.insert(tk.END, "Показатели рассчитаны\n")

            # 4. Анализ
            analysis = data_analyse()
            text_area.insert(tk.END, f"Анализ выполнен. Доход: {analysis['total_income']} лей\n")

            # 5. Мат. расчёты
            math_res = math_calculation()
            text_area.insert(tk.END, f"Мат. расчёты выполнены (доставка: {math_res['delivery_time_days']} дней)\n")

            # 6. Отчёт
            report_text = form_report(delta_days, weekday, analysis, math_res)
            text_area.insert(tk.END, "\n" + report_text)

            # 7. Озвучивание
            voice_report(report_text)
            text_area.insert(tk.END, "\nАудио-отчёт создан (report.mp3)")

            messagebox.showinfo("Готово", "Полный отчёт и аудио созданы!")

            tk.Button(root, text="Прослушать отчет", command=play_report, height=1,
                      font=('Times New Roman', 14, 'bold')).pack(pady=10)


        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    btn = tk.Button(root, text="Запустить полный анализ и сформировать отчёт",
                    command=run_full_analysis, height=2, font=("Arial", 12, "bold"))
    btn.pack(pady=10)
    tk.Button(root, text="Выход", command=root.destroy).pack()

    root.mainloop()


# =============================================
if __name__ == "__main__":
    print("Запуск программы анализа заказов...\n")
    # Интерфейс:
    main_interface()
