import json, connect, config, os, getPayLink, game
from connect import bot, db, logging, form_text_markdownv2
from telebot import types
from managment_user import referal, add_token, del_user, UserList, data_user, edit_mes_users_list
                  
manager_users_list = UserList()


def successfully_paid(id, datetime_exit):
    cur = db.cursor()
    cur.execute("SELECT link_server, paid FROM users_subscription WHERE t_id=" + str(id))
    data_cur = cur.fetchone()
    link_server = data_cur[0]
    paid = data_cur[1]
    keyboard = types.InlineKeyboardMarkup()
    #keyboard.add(types.InlineKeyboardButton(text="Видеоинструкция подключения", callback_data='{"key": "faq_video"}'))
    keyboard.add(types.InlineKeyboardButton(text="Авто вкл/откл с инстаграмм", callback_data='{"key": "comands_video"}'))
    keyboard.add(types.InlineKeyboardButton(text="Кнопка включения VPN с домашнего экрана", callback_data='{"key": "home_key_faq"}'))
    keyboard.add(types.InlineKeyboardButton(text="Купить", callback_data='{"key": "sale"}'))
    if paid != None:
        keyboard_ref = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard_ref.add(types.KeyboardButton(text="Реферальная программа"))
        bot.send_message(id, "Открыт доступ к реферальной программе. Вы можете пригласить нового пользователя и получить за это 1 мес. подписки бесплатно. Для того чтоб использовать такую возможность, нажмите на соответсвующую кнопку.", reply_markup=keyboard_ref)
    bot.send_photo(id, open(config.FILE_URL + "vpn_on.jpg", "rb"),"*Спасибо что выбрали наш сервис\.*\n\n Ваш VPN готов к работе\. Для доступы необходимо скачать приложение для вашей платформы \(ссылки ниже по сообщению\), вставить в приложение ваш персональную ссылку\-ключ и нажать подключиться\.\n\nСсылка\-ключ: \n`" + form_text_markdownv2(link_server) + "`\n\nНажмите на ссылку для ее копирования и вставьте в приложение\.\n\nДата и время окончания подписки: " + form_text_markdownv2(str(datetime_exit)) + 
                   "\n\nПрямые ссылки для скачивания простого приложения:\n[📱 iOS\(iPhone\)](https://apps.apple.com/ru/app/outline-app/id1356177741) \| [📱 Android](https://play.google.com/store/apps/details?id=org.outline.android.client) \| [💻 MacOS](https://apps.apple.com/us/app/outline-secure-internet-access/id1356178125?mt=12) \| [💻 Windows](https://s3.amazonaws.com/outline-releases/client/windows/stable/Outline-Client.exe) \| [💻 Linux](https://s3.amazonaws.com/outline-releases/client/linux/stable/Outline-Client.AppImage)" +
                   "\n\nПрямые ссылки для более функционального приложения\. Только через него работает авто вкл откл с инстаграмм:\n[📱 iOS\(iPhone\)](https://apps.apple.com/ru/app/v2box-v2ray-client/id6446814690)", reply_markup=keyboard, parse_mode="MarkdownV2")

def add_key_admin(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="/597730754"),
                 types.KeyboardButton(text="/action_users_count"),
                 types.KeyboardButton(text="/restart"))
    bot.send_message(message.from_user.id, "add_key", reply_markup=keyboard)
    manager_users_list.mes_arr = []
    manager_users_list.start = 0

@bot.message_handler(commands=["597730754"])
def d(message):
    if message.chat.id == config.ADMINCHAT:
        add_key_admin(message)
        manager_users_list.search_all_user(message)
    else:
        logging.error("доступ заблокирован")



@bot.message_handler(commands=["restart"])
def restart(message):
    if message.chat.id == config.ADMINCHAT:
        os.system("systemctl restart bot_vpn.service")
    else:
        bot.send_message(message.from_user.id, "отказано в доступе")
        logging.error("доступ заблокирован")



@bot.message_handler(commands=["поиск","найти", "search"])
def create_table(message):
    if message.chat.id == config.ADMINCHAT:
        add_key_admin(message)
        manager_users_list.search_user(message)
    else:
        logging.error("доступ заблокирован")


@bot.message_handler(commands=["action_users_count"])
def define(message):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM users_subscription WHERE action=1")
    bot.send_message(message.chat.id, "Активных подписок: " + str(cur.fetchone()[0]))


@bot.message_handler(commands=["spam"])
def all_mes(message):
    if message.chat.id == config.ADMINCHAT:
        cur = db.cursor()
        cur.execute("SELECT t_id FROM users_subscription")
        for i in cur.fetchall():
            try:
                bot.copy_message(chat_id=i[0], from_chat_id=message.reply_to_message.chat.id, message_id=message.reply_to_message.id, disable_notification=False)
            except Exception as e:
                logging.error("Не удалось отправить spam сообщение пользователю", e)

@bot.message_handler(commands=["gg"])
def gg(message):
    connect.session[message.from_user.id] = game.Game(message)

@bot.message_handler(commands=["start"])
def start(message):
    cur = db.cursor()
    cur.execute("SELECT action FROM users_subscription WHERE t_id=" + str(message.from_user.id))
    status = cur.fetchone()
    logging.info("Бот запущен пользователем со статусом " + str(status))
    keyboard = types.InlineKeyboardMarkup()
    if status == None:
        keyboard.add(types.InlineKeyboardButton(text="Попробовать", callback_data='{"key": "try"}'))
        keyboard.add(types.InlineKeyboardButton(text="Политика по обработке персональных данных", callback_data='{"key": "pppd"}'))
        keyboard.add(types.InlineKeyboardButton(text="Условия использования", callback_data='{"key": "termsOfUse"}'))
        option_text = "\n\n_Нажимая кнопку \"Попробовать\", Вы автоматически соглашаетесь с политикой обработки персональных данных и условиями использования сервиса\._" 
    elif status[0] == 0:
        keyboard.add(
            types.InlineKeyboardButton(text="Купить", callback_data='{"key": "sale"}')
        )
        option_text = ""
    elif status[0] == 1:
        successfully_paid(message.from_user.id, "данные не получены")
        return
    bot.send_message(message.chat.id, "*Выгоднова Полина Николаевна приветствует вас в сервисе VPN для свободного интернета без границ\.*" + option_text, reply_markup=keyboard, parse_mode="MarkdownV2")

@bot.message_handler(commands=["status_bot"])
def oss(message):
    if message.chat.id == config.ADMINCHAT:
        bot.send_message(message.chat.id, str(os.system("systemctl status bot_vpn.service")))


@bot.message_handler(content_types=["text"])
def text_handler(message):
    if message.chat.id == config.ADMINCHAT:
        try:
            user_id = str(message.reply_to_message.text).split('id:', -1)[1]
            bot.copy_message(chat_id=config.ADMINCHAT, from_chat_id=user_id, message_id=message.id)
        except Exception:
            pass
        try:
            user_id = str(message.reply_to_message.caption).split('id:', -1)[1]
            bot.copy_message(chat_id=config.ADMINCHAT, from_chat_id=user_id, message_id=message.id)
        except Exception:
            pass
    if message.text == "Реферальная программа":
        referal(message)
    if message.text == "test":
        getPayLink.getOrderList()
    else:
        bot.send_message(config.ADMINCHAT,
                         "[" + str(message.from_user.first_name) +
                         " " + str((message.from_user.last_name or "")) +
                         "](tg://user?id\=" + str(message.from_user.id) +
                         "):\n" +
                         connect.form_text_markdownv2(message.text) +
                         "\nid:" + str(message.from_user.id), parse_mode="MarkdownV2")
    logging.info(message.text)

@bot.message_handler(content_types=["photo"])
def photo_chek(message):
    bot.send_message(chat_id=message.from_user.id, reply_to_message_id=message.id, text="Отправлено администраторам на проверку. Вы получите уведомление с результатом, ожидайте...")
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton(text="США", callback_data='{"key": "connectUSA", "id": "' + str(message.from_user.id) + '"}'),
            types.InlineKeyboardButton(text="Нидерланды", callback_data='{"key": "connectNID", "id": "' + str(message.from_user.id) + '"}'))
    
    bot.send_photo(config.ADMINCHAT, photo=message.photo[0].file_id, caption="user: [" + form_text_markdownv2(message.from_user.first_name) + " " + str(form_text_markdownv2(message.from_user.last_name) or "") + "](tg://user?id\=" + str(message.from_user.id) + ") \n\nid: " + str(message.from_user.id), reply_markup=key, parse_mode="MarkdownV2")

@bot.message_handler(content_types=["document"])
def file_chek(message):
    bot.send_message(chat_id=message.from_user.id, reply_to_message_id=message.id, text="Отправлено администраторам на проверку. Вы получите уведомление с результатом, ожидайте...")
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton(text="США", callback_data='{"key": "connectUSA", "id": "' + str(message.from_user.id) + '"}'),
            types.InlineKeyboardButton(text="Нидерланды", callback_data='{"key": "connectNID", "id": "' + str(message.from_user.id) + '"}'))
    
    bot.send_document(config.ADMINCHAT, document=message.document.file_id, caption="user: [" + form_text_markdownv2(message.from_user.first_name) + " " + str(form_text_markdownv2(message.from_user.last_name) or "") + "](tg://user?id\=" + str(message.from_user.id) + ")\n\nid: " + str(message.from_user.id), reply_markup=key, parse_mode="MarkdownV2")


@bot.callback_query_handler(func=lambda call: True)
def callback_woker(call):
    call_data_json = call.data
    call_data = json.loads(call_data_json)
    username = str(call.from_user.first_name) + " " + str((call.from_user.last_name or ""))
    logging.info("chat: " + str(call.message.chat.title) + ", user:" + str(username) + " нажата кнопка с ключем " + call_data['key'])

    if call_data['key'] == "try":
        bot.delete_message(call.message.chat.id, call.message.id)
        datetime_exit = add_token(call.from_user.id, time=config.FIRST_START_DURATION, name_user=username)
        successfully_paid(call.from_user.id, datetime_exit)
    elif call_data['key'] == "sale":
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(text = "Нидерланды",
                                       callback_data='{"key": "sale_NED"}'),
            types.InlineKeyboardButton(text = "США",
                                       callback_data='{"key": "sale_USA"}')
        )
        bot.send_photo(call.from_user.id,
                       photo = open(config.FILE_URL + "num_login.png", "rb"),
                       caption = config.TEXTPAY
        )
    elif call_data['key'] == "sale_USA":
        connect.session[call.from_user.id] = getPayLink.WalletPay(call.from_user.id)
        keyboard = types.InlineKeyboardMarkup()
        url_pay = connect.session[call.from_user.id].getPayLink()
        keyboard.add(types.InlineKeyboardButton(text="Оплатить месяц", url=url_pay))
        bot.send_message(call.from_user.id, config.TEXTPAYUSAMARKDOWNV2, parse_mode="MarkdownV2" ,reply_markup=keyboard)
    elif call_data['key'] == "connectUSA":
        key = types.InlineKeyboardMarkup()
        key.add(*[types.InlineKeyboardButton(text=i, callback_data='{"key": "action", "id": "' + str(call_data['id']) + '", "month": "' + str(i) + '"}') for i in range(1,13)], types.InlineKeyboardButton(text="Назад", callback_data='{"key": "backConnectKey", "id": "' + str(call_data['id']) + '"}'))
        bot.edit_message_caption(chat_id = call.message.chat.id, message_id = call.message.id, caption = call.message.caption, reply_markup = key)
    
    elif call_data['key'] == "connectNID":

        key = types.InlineKeyboardMarkup()
        key.add(*[types.InlineKeyboardButton(text=i, callback_data='{"key": "action", "id": "' + str(call_data['id']) + '", "month": "' + str(i) + '", "server": "nid"}') for i in range(1,13)], types.InlineKeyboardButton(text="Назад", callback_data='{"key": "backConnectKey", "id": "' + str(call_data['id']) + '"}'))
        bot.edit_message_caption(chat_id = call.message.chat.id, message_id = call.message.id, caption = call.message.caption, reply_markup = key)
    
    elif call_data['key'] == "backConnectKey":

        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(text="США", callback_data='{"key": "connectUSA", "id": "' + str(call_data['id']) + '"}'),
                types.InlineKeyboardButton(text="Нидерланды", callback_data='{"key": "connectNID", "id": "' + str(call_data['id']) + '"}'))
                
        bot.edit_message_caption(chat_id = call.message.chat.id, message_id = call.message.id, caption = call.message.caption, reply_markup = key)

    elif call_data['key'] == "action":
        niderland = None
        if call.message.chat.id == config.ADMINCHAT:
            try:
                username = str(call.message.caption).split(": ", 1)[1]
            except Exception:
                username = str(call.message.text).split(" ", -2)[0]
        if call_data['server']:
            if call_data['server'] == "nid":
                niderland = True
        datetime_exit = add_token(call_data['id'], month=call_data["month"], name_user=username, niderland=niderland)
        successfully_paid(call_data['id'], datetime_exit)
        bot.answer_callback_query(callback_query_id=call.id, text="Подписка активирована", show_alert=True)
        manager_users_list.search_user(call.message)
    elif call_data['key'] == "action_button":
        edit_mes_users_list(call.message, call_data["id"])
    elif call_data['key'] == "deaction":
        del_user(call_data['id'])
        manager_users_list.manager_users_list(call.message)
    elif call_data['key'] == "not_action":
        bot.delete_message(call.message.chat.id, call.message.id)
        bot.send_message(call_data['id'], "Покупка отклонена администратором")
    elif call_data['key'] == "faq_video":
        bot.send_video(call.from_user.id, open("/root/bot_vpn/fff.mov", "rb"), width=888, height=1920)
    elif call_data['key'] == "comands_video":
        bot.send_video(call.from_user.id, open("/root/bot_vpn/comands.MP4", "rb"), width=888, height=1920)
    elif call_data['key'] == "page_client_next":
        manager_users_list.start=int(manager_users_list.start) + 6
        manager_users_list.search_all_user(call.message)
    elif call_data['key'] == "page_client_back":
        manager_users_list.start-=6
        manager_users_list.search_all_user(call.message)
    elif call_data['key'] == "home_key_faq":
        bot.send_video(call.from_user.id, open("/root/bot_vpn/faq_key_on_off.MP4", "rb"), width=888, height=1920)
        #bot.send_message(call.from_user.id, config.URL_KEY_COMMAND)
    elif call_data['key'] == "data_user":
        data_user(call_data['id'])
    elif call_data['key'] == "option_where":
        if manager_users_list.one_active == 0:
            manager_users_list.one_active = 1
        else:
            manager_users_list.one_active = 0
        manager_users_list.start = 0
        manager_users_list.search_all_user(call.message)
    elif call_data['key'] == "start_game_zero":
        if int(call_data["id"]) == call.from_user.id:
            bot.answer_callback_query(callback_query_id=call.id, text='Ты уже учавствуешь в этой игре')
            return
        connect.session[int(call_data["id"])].users.append(call.from_user.id)
        connect.session[int(call_data["id"])].game_zero(call)
    elif call_data['key'] == "gz":
        connect.session[int(call_data["id"])].game_zero(call, call_data = call_data)
    elif call_data['key'] == "pppd":
        bot.send_message(call.message.chat.id, """Сбор информации. Наш Telegram бот собирает только необходимую информацию для предоставления запрашиваемых услуг, такую как id и имя пользователя.
Хранение данных. Персональные данные пользователей хранятся на наших защищенных серверах и доступ к ним имеют только уполномоченные сотрудники. Данные хранятся до момента, когда они больше не требуются для оказания услуги или по запросу пользователя. Для удаления данных с сервера, обращайтесь к администраторам.
Использование данных. Персональные данные пользователей могут использоваться для оказания услуг, отправки уведомлений или согласно запросам, полученным от пользователей. Мы не разглашаем персональные данные третьим сторонам без согласия пользователя.
Защита данных. Мы принимаем меры для обеспечения защиты персональных данных и применяем современные технологии для предотвращения несанкционированного доступа к информации.
Права пользователей. Пользователи имеют право запрашивать доступ, исправление или удаление своих персональных данных. Они также имеют право отозвать свое согласие на обработку данных.
Политика обновлений. Мы регулярно обновляем нашу политику хранения и обработки данных, чтобы соответствовать последним требованиям законодательства.
Согласие. Используя наш бот, пользователь автоматически соглашается с нашей политикой хранения и обработки персональных данных.""")
    elif call_data['key'] == "termsOfUse":
        bot.send_message(call.message.chat.id, """Наш сервис предоставляет доступ к ВПН (Virtual Private Network) - это технология, которая позволяет создать безопасное и зашифрованное соединение между вашим устройством и интернетом. Она используется для обхода географических ограничений, защиты личной информации и обеспечения безопасности в интернете.
Далее по тексту используется намиенование сервиса Выгодный ВПН - данный впн сервис.

Условия использования:

- Нельзя использовать данный впн сервис для осуществления раздачи, скачки и распространения torrent - файлов.

- Необходимо соблюдать авторские права при использовании данного впн сервиса.

- Пользователь несет ответственность за свои действия при использовании данного впн сервиса.

- В случае неполадок сети на сервере, сбой работы протокола outline на территории предоставления услуг, а также несоблюдения данных условий использования, поставщик услуг (данный впн сервис) может отказать в предоставлении услуг в одностороннем порядке.

Пользователям следует внимательно ознакомиться с правилами использования данного впн сервиса перед началом пользования услугой.""")

    else:
        bot.answer_callback_query(callback_query_id=call.id, text='Кнопка еще не настроена.')

bot.infinity_polling()
