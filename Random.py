import random
import string
import time
import itertools

# Функция для генерации уникального номера заявки
def generate_application_number():
    # Используем время в миллисекундах для генерации уникального номера
    return int(round(time.time() * 1000))

# Создаем генератор последовательных чисел
sequence_number = itertools.count(1)

def generate_string_with_conditions():
    # Получаем следующее число в последовательности
    number = next(sequence_number)
    # Генерируем строку с заглавной буквой и номером, дополненным нулями до 4 знаков
    return f"{random.choice(string.ascii_uppercase)}{number:04d}"
