from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

#--- Main Menu ---

#mainMenu
btnAdress = KeyboardButton('📍 Где находимся?')
btnPrice = KeyboardButton('🧾 Прайс-лист')
btnExample = KeyboardButton('☝🏻 Примеры работ')
telNumber = KeyboardButton('📱 Контакты')
btnInfo = KeyboardButton('⏳ Статус заказа')
btnReviews = KeyboardButton('📝 Отзывы')

#reviewsMenu
btnWrite = KeyboardButton('✏️ Написать отзыв')
btnWatch = KeyboardButton('⭐ Посмотреть отзывы')
btnBack = KeyboardButton('↩ Назад')

# #adminMenu
# btnPassw = KeyboardButton('Ввести пароль')
# btnTwo = KeyboardButton('1')

#adminPanel
btnCreateApplication = KeyboardButton('✍️Создать заявку')
btnListApplication = KeyboardButton('📊Список активных заявок')
btnApplication = KeyboardButton('🗒История заявок')
btnChange = KeyboardButton('🖊Изменить статус заявки')
btnBack_admin = KeyboardButton('↩ Назад')

#change_status
btn_change_status_ready = KeyboardButton("📬Изменить статус на 'Заказ готов'")
btn_change_Status_otdan = KeyboardButton("📫Изменить статус на 'Заказ получен'")
btnBack_admin_change = KeyboardButton('🔙Назад')

#Status application
btn_application_send = KeyboardButton('📞Отправить номер телефона', request_contact=True)

mainMenu = ReplyKeyboardMarkup(resize_keyboard=True)
reviewsMenu = ReplyKeyboardMarkup(resize_keyboard=True)
# adminMenu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
adminPanel = ReplyKeyboardMarkup(resize_keyboard=True)
change_status = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
back_application_send = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

mainMenu.row(btnInfo)
mainMenu.row(btnAdress, btnPrice)
mainMenu.add(btnExample)
mainMenu.add(telNumber, btnReviews)

reviewsMenu.add(btnWrite)
reviewsMenu.add(btnWatch)
reviewsMenu.add(btnBack)

change_status.add(btn_change_status_ready, btn_change_Status_otdan)
change_status.add(btnBack_admin_change)

# adminMenu.add(btnPassw)

back_application_send.add(btn_application_send)

adminPanel.add(btnCreateApplication, btnChange)
adminPanel.add(btnApplication, btnListApplication)
adminPanel.add(btnBack_admin)