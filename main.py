import logging
import asyncio
import Random as Rn
import re
from prettytable import PrettyTable
from BotToken import token
from AdminPassword import Admin_Password

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import Location
import markups as nav
import mysql.connector
import sqlite3 as sq

from getpass import getpass
from mysql.connector import connect, Error

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import Message


class MyStates(StatesGroup):
    waiting_for_review = State()

class AdminStates(StatesGroup):
    pass_state = State()
    createApplication = State()
    waiting_for_phone_number = State()
    history_application = State()
    change_application = State()
    waiting_for_change = State()
    change_status_ready = State()
    phone_reg = State()
    createTovar = State()
    change_status_one = State()
    change_itog_ready = State()
    change_itog_otdan = State()




# Устанавливаем уровень логов
logging.basicConfig(level=logging.INFO)

# Создаем бота и диспетчер
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    # Код для отправки сообщения пользователю и установки состояния
    await bot.send_message(message.chat.id, 'Пожалуйста, отправьте ваш номер телефона чтобы узнать статус заказов.', reply_markup=nav.back_application_send)
    await AdminStates.phone_reg.set()

# Обработчик состояния phone_reg
@dp.message_handler(state=AdminStates.phone_reg, content_types=types.ContentTypes.CONTACT)
async def save_send_phone_status(message: types.Message, state: FSMContext):
    if message.contact is not None and message.contact.user_id == message.from_user.id:
        user_data = (message.chat.id, message.from_user.last_name, message.from_user.first_name, message.contact.phone_number)
        with sq.connect('sq_baze/Users/users.db') as con:
            cur = con.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY,
                last_name TEXT,
                first_name TEXT,
                phone_number TEXT UNIQUE
            )""")
            cur.execute("INSERT OR IGNORE INTO users (id, last_name, first_name, phone_number) VALUES (?,?,?,?);", user_data)
            con.commit()
        await message.reply("Спасибо, ваш номер телефона сохранен.", reply_markup=nav.mainMenu)
        await state.finish()
    else:
        await message.reply("Пожалуйста, используйте кнопку для отправки вашего номера телефона.")
        await process_start_command(message)

#Admin panel
@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    with sq.connect('sq_baze/Admin/admin.db') as con:
        cur = con.cursor()
        people_id = message.chat.id
        cur.execute("SELECT id FROM users WHERE id = ?", (people_id,))
        data = cur.fetchone()
        if data is None:
            await bot.send_message(message.chat.id, 'Введите пароль!')
            await AdminStates.pass_state.set()
        else:
            await bot.send_message(message.chat.id, 'Добро пожаловать в админ панель!', reply_markup=nav.adminPanel)

#FSM password
@dp.message_handler(state=AdminStates.pass_state)
async def save_admin(message: types.Message, state: FSMContext):
    if message.text == Admin_Password:
            await bot.send_message(message.chat.id,'Пароль введён правильно!')
            await admin_panel_menu(message)
            await state.finish()
    else:
        await bot.send_message(message.chat.id,'Пароль введён неправильно!')
        await state.finish()

#Welcom Admin panel
async def admin_panel_menu(message: types.Message):
    with sq.connect('sq_baze/Admin/admin.db') as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            name TEXT,
            last_name TEXT
        )""")
        con.commit()

        people_id = message.chat.id
        cur.execute("SELECT id FROM users WHERE id = ?", (people_id,))

        data = cur.fetchone()
        if data is None:
            user_data = (message.chat.id, message.from_user.first_name, message.from_user.last_name)
            cur.execute("INSERT INTO users VALUES (?, ?, ?);", user_data)
            con.commit()

    await bot.send_message(message.chat.id, 'Добро пожаловать в админ панель!', reply_markup=nav.adminPanel)

# Создание заявки
@dp.message_handler(lambda message: message.text == "✍️Создать заявку")
async def create_application(message: types.Message):
    # Проверка на администратора
    with sq.connect('sq_baze/Admin/admin.db') as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            name TEXT,
            last_name TEXT
        )""")
        con.commit()

        people_id = message.chat.id
        cur.execute("SELECT id FROM users WHERE id = ?", (people_id,))
        data = cur.fetchone()
        if data is None:
            await bot.send_message(message.chat.id, 'Вы не админ!')
        else:
            await bot.send_message(message.chat.id, 'Введите номер телефона клиента! Обязательно нужно поставить в начале номера "+"!')
            await AdminStates.createTovar.set()

# Сохранение номера телефона клиента и переход к запросу названия товара
@dp.message_handler(state=AdminStates.createTovar)
async def save_phone_number(message: types.Message, state: FSMContext):
    # Проверяем, что номер начинается с "+" и содержит только цифры
    if re.match(r"^\+\d+$", message.text):
        async with state.proxy() as data:
            data['phone_number'] = message.text  # Сохраняем номер телефона клиента
        await bot.send_message(message.chat.id, 'Введите название товара!')
        await AdminStates.createApplication.set()  # Переход к следующему состоянию
    else:
        await bot.send_message(message.chat.id, 'Неверный формат номера. Убедитесь, что номер начинается с "+" и содержит только цифры.')
        await state.finish()

# Сохранение заявки
@dp.message_handler(state=AdminStates.createApplication)
async def save_application(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        numberClient = data.get('numberClient')
        phone_number = data.get('phone_number')  # Получаем номер телефона клиента
        # if numberClient is None or phone_number is None:
        #     await bot.send_message(message.chat.id, 'Ошибка: номер клиента не найден.')
        #     await state.finish()
        #     #return

        data['nameTovar'] = message.text  # Сохраняем название товара
        itog = Rn.generate_string_with_conditions()
        await bot.send_message(message.chat.id, 'Заказу клиента присвоен номер: ' + str(itog))

        # Сохранение заявки в базе данных
        info_application = (itog, phone_number, message.text, 'В процессе')
        with sq.connect('sq_baze/Application/applications.db') as con:
            cur = con.cursor()
            cur.execute("INSERT INTO application (applicationNumber, numberCustomer, nameTovar, status) VALUES (?, ?, ?, ?);", info_application)
            cur.execute("INSERT INTO history (applicationNumber, numberCustomer, nameTovar) SELECT applicationNumber, numberCustomer, nameTovar FROM application WHERE NOT EXISTS (SELECT 1 FROM history WHERE history.applicationNumber = application.applicationNumber)")
            con.commit()

        await bot.send_message(message.chat.id, 'Хотите создать ещё одну заявку? Нажмите "Создать заявку".')
        await state.finish()       

# History application
@dp.message_handler(lambda message: message.text == "🗒История заявок")
async def create_an_application(message: types.Message):
        with sq.connect('sq_baze/Admin/admin.db') as con:
            cur = con.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY,
                name TEXT,
                last_name TEXT
            )""")
            con.commit()

            people_id = message.chat.id
            cur.execute("SELECT id FROM users WHERE id = ?", (people_id,))

            data = cur.fetchone()
            if data is None:
                await bot.send_message(message.chat.id, 'Вы не админ!')
            else:
                with sq.connect('sq_baze/Application/applications.db') as con:
                    cur = con.cursor()
                    cur.execute("SELECT applicationNumber, numberCustomer, nameTovar FROM history")
                    rows = cur.fetchall()

                # Создаем объект таблицы PrettyTable
                table = PrettyTable()

                table.field_names = ["Номер заказа", "Номер телефона клиента", "Название товара"]
                table.align = "l"  # Выравнивание всех колонок по левому краю

                # Добавляем строки в таблицу
                for row in rows:
                    # Преобразование числовых значений в строки
                    applicationNumber, numberCustomer, nameTovar = map(str, row)
                    table.add_row([applicationNumber, numberCustomer, nameTovar])

                # Отправка таблицы в виде сообщения
                await bot.send_message(message.chat.id, f"```\n{table}\n```", parse_mode='Markdown')

#Change application status
@dp.message_handler(lambda message: message.text == "🖊Изменить статус заявки")
async def list_of_active_applications(message: types.Message):
            with sq.connect('sq_baze/Admin/admin.db') as con:
                cur = con.cursor()
                cur.execute("""CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    last_name TEXT
                )""")
                con.commit()

                people_id = message.chat.id
                cur.execute("SELECT id FROM users WHERE id = ?", (people_id,))

                data = cur.fetchone()
                if data is None:
                    await bot.send_message(message.chat.id, 'Вы не админ!')
                else:
                    with sq.connect('sq_baze/Application/applications.db') as con:
                        cur = con.cursor()

                        cur.execute("SELECT applicationNumber, numberCustomer, nameTovar, status FROM application WHERE status IN ('В процессе', 'Заказ готов')")
                        rows = cur.fetchall()

            # Инициализация переменной для хранения всех записей
            table = PrettyTable()
                
            table.field_names = ["Номер заказа", "Номер телефона клиента", "Название товара", "Статус"]
            table.align = "l"  # Выравнивание всех колонок по левому краю

            # Добавляем строки в таблицу
            for row in rows:
                # Преобразование числовых значений в строки
                applicationNumber, numberCustomer, nameTovar, status = map(str, row)
                table.add_row([applicationNumber, numberCustomer, nameTovar, status])

            #Отправка собранного сообщения
            await bot.send_message(message.chat.id, f"```\n{table}\n```", parse_mode='Markdown')
            await bot.send_message(message.chat.id, 'Введите номер заказа статус которого вы хотите поменять!')
            await AdminStates.change_application.set()

@dp.message_handler(state=AdminStates.change_application)
async def save_change_application(message: types.Message, state: FSMContext):
    order_number = message.text.strip()
    async with state.proxy() as data:
        data['order_number'] = order_number
    with sq.connect('sq_baze/Application/applications.db') as con:
        cur = con.cursor()
        # Используйте SELECT с указанием конкретных столбцов для избежания ошибок
        cur.execute("SELECT applicationNumber, numberCustomer, nameTovar, status FROM application WHERE applicationNumber = ?", (order_number,))
        result = cur.fetchone()
        if result:
            # Создание таблицы
            table = PrettyTable()
            table.field_names = ["Номер заказа", "Номер телефона клиента", "Название товара", "Статус"]
            table.add_row(result)  # Добавление строки в таблицу

            # Отправка таблицы пользователю
            await bot.send_message(message.chat.id, f"```\n{table}\n```", parse_mode='Markdown')
            # Переход к следующему состоянию FSM
            await bot.send_message(message.chat.id, 'Что вы хотите сделать с заказом?', reply_markup=nav.change_status)
            await AdminStates.change_status_one.set()
        else:
            await bot.send_message(message.chat.id, 'Заказ с таким номером не найден')
            await state.finish()

#FSM change application ready
@dp.message_handler(lambda message: message.text == "📫Изменить статус на 'Заказ получен'", state=AdminStates.change_status_one)
async def save_change_itog_otdan(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        order_number = data.get('order_number')
    if order_number:
        new_status = 'Заказ получен'
        with sq.connect('sq_baze/Application/applications.db') as con:
            cur = con.cursor()
            cur.execute("UPDATE application SET status = ? WHERE applicationNumber = ?", (new_status, order_number))
            if cur.rowcount == 0:
                await bot.send_message(message.chat.id, 'Заказ с таким номером не найден')
            else:
                con.commit()
                await bot.send_message(message.chat.id, 'Статус заказа изменен на "Заказ получен"')
        await state.finish()
    else:
        await bot.send_message(message.chat.id, 'Произошла ошибка: номер заказа не найден.')
        # Возможно, стоит вернуть пользователя к предыдущему шагу для повторного ввода номера заказа
        await state.finish()

@dp.message_handler(lambda message: message.text == "📬Изменить статус на 'Заказ готов'", state=AdminStates.change_status_one)
async def save_change_ready(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        order_number = data.get('order_number')
    if order_number:
        new_status = 'Заказ готов'
        with sq.connect('sq_baze/Application/applications.db') as con:
            cur = con.cursor()
            cur.execute("UPDATE application SET status = ? WHERE applicationNumber = ?", (new_status, order_number))
            if cur.rowcount == 0:
                await bot.send_message(message.chat.id, 'Заказ с таким номером не найден')
            else:
                con.commit()
                await bot.send_message(message.chat.id, 'Статус заказа изменен на "Заказ готов"')
        await state.finish()
    else:
        await bot.send_message(message.chat.id, 'Произошла ошибка: номер заказа не найден.')
        # Возможно, стоит вернуть пользователя к предыдущему шагу для повторного ввода номера заказа
        await state.finish()

#Change active application
@dp.message_handler(lambda message: message.text == "📊Список активных заявок")
async def list_of_active_applications(message: types.Message):
    with sq.connect('sq_baze/Admin/admin.db') as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            name TEXT,
            last_name TEXT
            )""")
        con.commit()

        people_id = message.chat.id
        cur.execute("SELECT id FROM users WHERE id = ?", (people_id,))

        data = cur.fetchone()
        if data is None:
            await bot.send_message(message.chat.id, 'Вы не админ!')
        else:
            with sq.connect('sq_baze/Application/applications.db') as con:
                cur = con.cursor()
                cur.execute("SELECT applicationNumber, numberCustomer, nameTovar, status FROM application WHERE status IN ('В процессе','Заказ готов')")
                rows = cur.fetchall()

        table = PrettyTable()

        table.field_names = ["Номер заказа", "Номер телефона клиента", "Название товара", "Статус заказа"]
        table.align = "l"  # Выравнивание всех колонок по левому краю

        # Добавляем строки в таблицу
        for row in rows:
            # Преобразование числовых значений в строки
            applicationNumber, numberCustomer, nameTovar, status = map(str, row)
            table.add_row([applicationNumber, numberCustomer, nameTovar, status])
        # Отправка собранного сообщения
        await bot.send_message(message.chat.id, f"```\n{table}\n```", parse_mode='Markdown')

# Обработка команды "Где находимся?"
@dp.message_handler(lambda message: message.text == "📍 Где находимся?")
async def location(message: types.Message):
    # Отправляем инструкцию по использованию бота
    lat = 55.648123
    lon = 37.537254
    location = Location(latitude=lat, longitude=lon)
    await bot.send_location(message.chat.id, latitude=lat, longitude=lon)
    await message.reply("Мы находимся по адресу: г. Москва, метро Беляево ул. Бутлерова д 24")
    
# Обработка команды "Прайс-лист"
@dp.message_handler(lambda message: message.text == "🧾 Прайс-лист")
async def send_file(message: types.Document):
    # Отправляем инструкцию по решению проблем
    await message.reply_document(open('photo\\price.pdf', 'rb'))

@dp.message_handler(lambda message: message.text == "☝🏻 Примеры работ")
async def send_file(message: types.Document):
    # Отправляем инструкцию по решению проблем
    await message.reply_document(open('photo\\work.pdf', 'rb'))

@dp.message_handler(lambda message: message.text == "📱 Контакты")
async def process_start_command(message: types.Message):
    # Отправляем инструкцию по решению проблем
    await message.reply("Наш номер телефона: +7 968 828-60-67")

@dp.message_handler(lambda message: message.text == "⏳ Статус заказа")
async def process_status_application(message: types.Message):
    with sq.connect('sq_baze/Application/applications.db') as con:
        cur = con.cursor()
        cur.execute("SELECT applicationNumber, nameTovar, status FROM application WHERE status IN ('В процессе','Заказ готов')")
        rows = cur.fetchall()

        # Инициализация переменной для хранения всех записей
        table = PrettyTable()

        table.field_names = ["Номер заказа", "Название товара", "Статус заказа"]
        table.align = "l"  # Выравнивание всех колонок по левому краю

        # Добавляем строки в таблицу
        for row in rows:
            # Преобразование числовых значений в строки
            applicationNumber, nameTovar, status = map(str, row)
            table.add_row([applicationNumber, nameTovar, status])
        # Отправка собранного сообщения
        await bot.send_message(message.chat.id, f"```\n{table}\n```", parse_mode='Markdown')

@dp.message_handler(lambda message: message.text == "📝 Отзывы")
async def process_start_command(message: types.Message):
    with sq.connect('sq_baze/Feedback/feedbacks.db') as con:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER,
        last_name TEXT,
        first_name TEXT,
        feedbackClient TEXT
        )""")
        con.commit()

    await message.reply("Тут можете посмотреть наши отзывы, а также оставить свой!", reply_markup=nav.reviewsMenu)

@dp.message_handler(lambda message: message.text == "⭐ Посмотреть отзывы")
async def process_start_command(message: types.Message):
    with sq.connect('sq_baze/Feedback/feedbacks.db') as con:
        cur = con.cursor()
        cur.execute("SELECT id FROM feedback")
        con.commit()
        data = cur.fetchall()
        if not data:  # Проверка на пустой список
            await bot.send_message(message.chat.id, 'Отзывов нет!')
        else:
            cur.execute("SELECT feedbackClient FROM feedback")  # Нет необходимости открывать новое соединение
            rows = cur.fetchall()

            feedback_message = ""
            for row in rows:
                feedback = row[0]  # Предполагаем, что feedbackClient - это строка
                feedback_message += f"{feedback}\n------------------------------------------------------------------------------------------------------\n"  # Добавление разделительной линии
            if feedback_message.strip():  # Проверка, что сообщение не пустое
                # Отправка собранного сообщения
                await bot.send_message(message.chat.id, feedback_message, parse_mode='Markdown')
            else:
                await bot.send_message(message.chat.id, 'Отзывов нет!')

@dp.message_handler(lambda message: message.text == "✏️ Написать отзыв")
async def process_start_command(message: types.Message, state: FSMContext):
    # Отправляем пользователю сообщение с просьбой оставить отзыв
    # async with state.proxy() as data:
    #         data['review_text'] = message.text  # Сохраняем номер телефона клиента
    await bot.send_message(message.chat.id, "Введите ваш отзыв:")
    await MyStates.waiting_for_review.set()

@dp.message_handler(state=MyStates.waiting_for_review)
async def create_feedback(message: types.Message, state: FSMContext):
    with sq.connect('sq_baze/Feedback/feedbacks.db') as con:
        # async with state.proxy() as data:
        #     # Доступ к данным, сохраненным ранее
        #     some_data = data.get('review_text')
        some_data = message.text
        user_text = (message.chat.id, message.from_user.last_name, message.from_user.first_name, some_data)
        cur = con.cursor()
        cur.execute("INSERT INTO feedback (id, last_name, first_name, feedbackClient) VALUES (?,?,?,?)", user_text)
        con.commit()
        await bot.send_message(message.chat.id, 'Спасибо за отзыв!')
        await state.finish()

@dp.message_handler(lambda message: message.text == "↩ Назад")
async def process_start_command(message: types.Message):
    await message.reply("Главное меню", reply_markup=nav.mainMenu)

@dp.message_handler(lambda message: message.text == "🔙Назад")
async def process_start_command(message: types.Message):
    await message.reply("Админ панель", reply_markup=nav.adminPanel)

@dp.message_handler()
async def bot_message(message: types.Message):
    result = []
    if message.text == '📍 Где находимся?':
        await message.reply("Мы находимся по адресу: г. Москва, метро Беляево ул. Бутлерова д 24")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
