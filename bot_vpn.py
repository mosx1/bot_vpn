# -*- coding: utf-8 -*-

import json, config, os, utils, pytz, datetime, time, managment_user

from connect import bot, db, logging

from telebot import types

from managment_user import add_user, del_user, UserList, data_user, StatusSearch

from filters import onlyAdminChat

from psycopg2.extras import DictCursor
                  
from enums.server_list import Servers, getServerNameById

from yoomoneyMethods import getInfoLastPayment, getLinkPayment

from telebot.util import quick_markup

from threading import Thread

from enums.comands import Comands

from controllerFastApi import add_vpn_user

from statistic import updateStatistic

from enums.content_types import ContentTypes
from enums.parse_mode import ParseMode
from enums.keyCall import KeyCall

from giftUsers import genGiftCode, checkGiftCode


def successfully_paid(id, oldMessageId=None, optionText="") -> bool:

    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT server_link, paid, exit_date, name FROM users_subscription WHERE telegram_id=" + str(id))
        data_cur = cursor.fetchone()

        keyboard = types.InlineKeyboardMarkup()

        keyboard.add(types.InlineKeyboardButton(text="Завершить настройку", url='https://kuzmos.ru/mobile?link={}'.format(str(data_cur["server_link"]))))
        keyboard.add(types.InlineKeyboardButton(text="Ручная настройка(если ничего не подключается)", callback_data='{"key": "manualSettings", "id": "' + str(id) + '"}'))
        keyboard.add(types.InlineKeyboardButton(text="Авто вкл/выкл на iPhone", callback_data='{"key": "comands_video"}'))
        keyboard.add(
            types.InlineKeyboardButton(text="Продлить", callback_data='{"key": "sale"}'),
            types.InlineKeyboardButton(
                text=config.KeyboardForUser.gift.value,
                callback_data='{"key": "' + KeyCall.pollCountMonth.value + '", "server": '+ str(config.DEFAULTSERVER) + ', "gift": true}')
        )
        
        if oldMessageId == None:
            if data_cur["paid"] == True:
                keyboard_ref = types.ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard_ref.add(types.KeyboardButton(text=config.KeyboardForUser.refProgram.value))
                keyboard_ref.add(types.KeyboardButton(text=config.KeyboardForUser.balanceTime.value))
                keyboard_ref.add(types.KeyboardButton(text=config.KeyboardForUser.gift.value))
                bot.send_message(id, "Реферальная программа",
                                reply_markup=keyboard_ref,
                                parse_mode= ParseMode.mdv2.value)
        
            if bot.send_photo(chat_id=id, photo=open(config.FILE_URL + "4rrr.jpg", "rb"),
                              caption=optionText + config.TextsMessages.successfullySubscriptionAutomatic.value.format(
                                utils.replaceMonthOnRuText(str(data_cur["exit_date"]))),
                            reply_markup=keyboard, parse_mode=ParseMode.mdv2.value):
                return True
            else:
                return False
        else:
            bot.edit_message_caption(chat_id=id, message_id=oldMessageId,
                                caption=optionText + config.TextsMessages.successfullySubscriptionAutomatic.value.format(
                                utils.replaceMonthOnRuText(str(data_cur["exit_date"]))),
                                reply_markup=keyboard, parse_mode=ParseMode.mdv2.value)



def pollingInfoLastPayment(*args) -> dict:
    """
    args - label, server, day, userId, messageId
    """
    label = args[0]
    server = args[1]
    month = args[2]
    userId = args[3]
    messageId = args[4]
    try:
        userName: str = args[5]
    except Exception:
        userName = userId

    stopDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(hours=1)

    while True:

        time.sleep(3)
        currentDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
        res = getInfoLastPayment(label)

        if res:

            bot.edit_message_caption("Оплата получена, идет настройка конфигурации(это может занять несколько минут)...", userId, messageId)
            
            add_user(userId, month, server=server)

            bot.send_message(config.ADMINCHAT,
                             "[" + userName + "](tg://user?id\=" + str(userId) + ") оплатил",
                             parse_mode=ParseMode.mdv2.value)
            bot.delete_message(userId, messageId)

            successfully_paid(userId, optionText="Оплата успешно прошла\n\n")

            return res
        
        if currentDateTime > stopDateTime:
            bot.delete_message(userId, messageId)
            return 
        


def pollingInfoLastPaymentGift(*args) -> dict:
    """
    args - label, month, userId, messageId
    """
    label = args[0]
    month = args[1]
    userId = args[2]
    messageId = args[3]
    try:
        userName = args[5]
    except Exception:
        userName = userId

    stopDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(hours=1)

    while True:

        time.sleep(2)
        currentDateTime = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
        res = getInfoLastPayment(label)

        if res:

            hash = genGiftCode(month)

            bot.send_message(config.ADMINCHAT,
                             "[" + userName + "](tg://user?id\=" + str(userId) + ") оплатил подарочную подписку",
                             parse_mode=ParseMode.mdv2.value)
            bot.delete_message(userId, messageId)

            photoMessage = bot.send_photo(
                chat_id=userId,
                photo=open(config.FILE_URL + "image/gift.png", "rb"),
                caption=config.TextsMessages.giftPostcard.value.format(code=hash),
                parse_mode=ParseMode.mdv2.value
            )

            bot.reply_to(photoMessage, "Перешлите это сообщение другу в качестве подарка. Спасибо что помогаете нам делать интернет доступнее.")

            return res
        
        if currentDateTime > stopDateTime:
            bot.delete_message(userId, messageId)
            return 



def manualSuccessfullyPaid(id, oldMessageId=None) -> bool:

    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT server_link, paid, exit_date, name FROM users_subscription WHERE telegram_id=" + str(id))
        data_cur = cursor.fetchone()

        keyboard = types.InlineKeyboardMarkup()
        
        keyboard.add(types.InlineKeyboardButton(text="Как подключить ПК", url="https://drive.google.com/file/d/1mSATyhbzILNiMJxnkHMnKZWj_h6LpKIF/view?usp=sharing"))
        keyboard.add(types.InlineKeyboardButton(text="Как подключить Android/iOS/MacOS", callback_data='{"key": "home_key_faq"}'))
        keyboard.add(types.InlineKeyboardButton(text="<<<Назад", callback_data='{"key": "backmanualSettings", "id": "' + str(id) + '"}'))
    

        bot.edit_message_caption(chat_id=id, message_id=oldMessageId,
                              caption=config.TextsMessages.successfullySubscription.value.format(
                            utils.form_text_markdownv2(data_cur["server_link"]),
                            utils.replaceMonthOnRuText(str(data_cur["exit_date"]))),
                            reply_markup=keyboard, parse_mode=ParseMode.mdv2.value)



def add_key_admin(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text='/' + Comands.adminPanel.value),
                 types.KeyboardButton(text='/' + Comands.actionUsersCount.value))
    keyboard.add(types.KeyboardButton(text='/' + Comands.statistic.value),
                 types.KeyboardButton(text='/' + Comands.restart.value))
    
    bot.send_message(message.from_user.id, "add_key", reply_markup=keyboard)



@bot.message_handler(commands=[Comands.statistic.value], func=onlyAdminChat())
def _(message: types.Message):
    treadStat = Thread(target=updateStatistic)
    treadStat.start()


@bot.message_handler(commands=[config.ADMINPASSWORD], func=onlyAdminChat())
def d(message):
    add_key_admin(message)
    managment_user.manager_users_list = UserList()
    managment_user.manager_users_list.search_all_user(message)


@bot.message_handler(commands=[Comands.restart.value], func=onlyAdminChat())
def restart(message):
    os.system("systemctl restart bot_vpn.service")


@bot.message_handler(commands=["поиск", "найти", "search"], func=onlyAdminChat())
def create_table(message):
    add_key_admin(message)
    managment_user.manager_users_list = UserList(message)
    

    
@bot.message_handler(commands=[Comands.actionUsersCount.value])
def define(message):
    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(1)," +
                        "(SELECT COUNT(1) FROM users_subscription WHERE action = True AND paid=True)," +
                        "(SELECT COUNT(1) FROM users_subscription WHERE action = True AND server_id = " + str(Servers.niderlands2.value) + ")," +
                        "(SELECT COUNT(1) FROM users_subscription WHERE action = True AND server_id = " + str(Servers.deutsche.value) + ")" +
                        " FROM users_subscription WHERE action=True")
                
        dataCur = cursor.fetchone()

        bot.send_message(message.chat.id, "Активных подписок: " + str(dataCur[0]) +
                         " платных: " + str(dataCur[1]) +
                        "\nАктивно Нидерланды: " + str(dataCur[2]) + 
                        "\nАктивно Германия: " + str(dataCur[3]))


@bot.message_handler(commands=["del"], func=onlyAdminChat())
def _(message: types.Message):

    """Удаляет текущего пользователя. Для теста"""

    with db.cursor() as cursor:
        cursor.execute("DELETE FROM users_subscription WHERE telegram_id = " + str(message.from_user.id))
        db.commit()

@bot.message_handler(commands=["spam"], func=onlyAdminChat())
def all_mes(message: types.Message):
    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT telegram_id FROM users_subscription")
        for item in cursor.fetchall():
            try:
                bot.copy_message(chat_id=item["telegram_id"],
                                 from_chat_id=message.reply_to_message.chat.id,
                                 message_id=message.reply_to_message.id,
                                 disable_notification=False)
            except Exception:
                logging.error("Не удалось отправить spam сообщение пользователю")



@bot.message_handler(commands=["spamref"])
def _(message: types.Message):
    with db.cursor() as cursor:
        cursor.execute("SELECT telegram_id FROM users_subscription")
        for i in cursor.fetchall():
            try:
                bot.send_message(i[0], "Вы можете пригласить нового пользователя и получить за это 1 мес\. подписки бесплатно\. Для того чтоб использовать такую возможность, отправьте вашу пригласительную ссылку другу\(для копирования достаточно нажать на ссылку\)\n\n"+
                        "Персональная ссылка:\n`https://t.me/open_vpn_sale_bot?start=" + str(i[0]) + "`",
                            parse_mode= ParseMode.mdv2.value)
            except Exception as e:
                logging.error("Не удалось отправить сообщение пользователю", e)



@bot.message_handler(commands=["log", "лог"], func=onlyAdminChat())
def _(message: types.Message):

    bot.send_document(message.chat.id, document=open("logs.txt","rb"))


@bot.message_handler(commands=[Comands.start.value])
def start(message: types.Message):
    jsonIdInvited = ""
    with db.cursor() as cursor:
        cursor.execute("SELECT action FROM users_subscription WHERE telegram_id=" + str(message.from_user.id))
        status = cursor.fetchone()
        keyboard = types.InlineKeyboardMarkup()
        if status == None:
            arrStartMessageText = message.text.split(" ")
            if len(arrStartMessageText) == 2:
                cursor.execute("SELECT EXISTS(SELECT 1 FROM users_subscription WHERE action = true AND telegram_id = " + str(arrStartMessageText[1]) + ")")
                invited = cursor.fetchall()
                if len(invited) > 0:
                    jsonIdInvited = ', "invitedId": ' + str(arrStartMessageText[1])
                    message.text = arrStartMessageText[1]
                    if checkGiftCode(message):
                        return successfully_paid(message.from_user.id, optionText="Подарок активирован\n")

            keyboard.add(types.InlineKeyboardButton(text="Попробовать", callback_data='{"key": "tryServers"' + jsonIdInvited + '}'))
            keyboard.add(types.InlineKeyboardButton(text="Политика по обработке персональных данных", callback_data='{"key": "pppd"}'))
            keyboard.add(types.InlineKeyboardButton(text="Условия использования", callback_data='{"key": "termsOfUse"}'))
            option_text = "\n\n_Нажимая кнопку \"Попробовать\", Вы соглашаетесь с политикой обработки персональных данных и условиями использования сервиса\._" 
        elif status[0] == 0:
            keyboard.add(
                types.InlineKeyboardButton(text="Возобновить", callback_data='{"key": "sale"}')
            )
            option_text = ""
        elif status[0] == 1:
            successfully_paid(message.from_user.id)
            return
        bot.send_message(message.chat.id, "*Приветствую Вас в сервисе VPN для свободного интернета без границ\.*" + option_text,
                        reply_markup=keyboard, parse_mode=ParseMode.mdv2.value)
        

@bot.message_handler(commands=["status_bot"], func=onlyAdminChat())
def oss(message):
    bot.send_message(message.chat.id, str(os.system("systemctl status bot_vpn.service")))



@bot.message_handler(commands=["gift"])
def _(message: types.Message):

    key = quick_markup(
        {
            config.KeyboardForUser.gift.value: {'callback_data': '{"key": "' + KeyCall.pollCountMonth.value + '", "server": '+ str(config.DEFAULTSERVER) + ', "gift": true}'}
        },
        row_width=1
    )

    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT telegram_id FROM users_subscription")
        for item in cursor.fetchall():
            try:
                bot.send_photo(
                    chat_id=item,
                    photo=open(config.FILE_URL + "image/gift.png", "rb"),
                    caption=config.TextsMessages.giftSpamCaption.value,
                    reply_markup=key
                )
            except Exception:
                logging.error("Не удалось отправить spam сообщение пользователю")
        



@bot.message_handler(func=lambda message: message.text == config.KeyboardForUser.balanceTime.value)
def _(message: types.Message):
    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT exit_date FROM users_subscription WHERE telegram_id=" + str(message.from_user.id))
        data_cur = cursor.fetchone()
        
        bot.send_message(message.from_user.id,
                         "Подписка оканчивается: " + str(data_cur['exit_date']),
                         reply_to_message_id=message.id)


@bot.message_handler(func=lambda message: message.text == config.KeyboardForUser.gift.value)
def _(message: types.Message):
    key = quick_markup(
        {
            config.KeyboardForUser.gift.value: {'callback_data': '{"key": "' + KeyCall.pollCountMonth.value + '", "server": '+ str(config.DEFAULTSERVER) + ', "gift": true}'}
        },
        row_width=1
    )
    bot.send_message(
        message.from_user.id,
        "Для оформления подарка нажмите кнопку ниже",
        reply_markup=key
        )



@bot.message_handler(commands=[Comands.resubusa.value])
def _(message: types.Message):
    bot.send_message(config.ADMINCHAT, "выполняется процесс...")
    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT telegram_id, name FROM users_subscription WHERE action = True" +
                        " AND server_id = " + str(Servers.niderlands.value))
        users = cursor.fetchall()
        for i in users:
            link = add_vpn_user(i['telegram_id'], Servers.niderlands2.value)
  
            cursor.execute("UPDATE users_subscription" + 
                        "\nSET server_link='" + link +
                        "\n, server_id = " + str(Servers.niderlands2.value) +
                        ", protocol=" + str(config.DEFAULTPROTOCOL) + 
                        "'\n WHERE telegram_id=" + str(i['telegram_id']))
        db.commit()
        for i in users:
            try:
                successfully_paid(i['telegram_id'], optionText="НЕОБХОДИМО ОБНОВИТЬ КОНФИГУРАЦИЮ\. СТАРАЯ КОНФИГУРАЦИЯ БОЛЬШЕ НЕ РАБОТАЕТ\.")
            except Exception as e:
                bot.send_message(config.ADMINCHAT, "error sendmessage [" + str(i['name']) + "](tg://user?id\=" + str(i['telegram_id']) + ") " + utils.form_text_markdownv2(str(e)),
                                 parse_mode=ParseMode.mdv2.value)
    bot.send_message(config.ADMINCHAT, "commit")



@bot.message_handler(content_types=[ContentTypes.text.value],
                     func= lambda message: message.from_user.id != config.ADMINCHAT)
def _(message: types.Message):
    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT action FROM users_subscription WHERE telegram_id = {}".format(message.from_user.id))
        dataCur = cursor.fetchone()

        if checkGiftCode(message):
            return successfully_paid(message.from_user.id, optionText="Подарок активирован")

        if message.text == "Реферальная программа":
            bot.send_message(message.from_user.id, "Вы можете пригласить нового пользователя и получить за это 1 мес\. подписки бесплатно\. Для того чтоб использовать такую возможность, отправьте вашу пригласительную ссылку другу\(для копирования достаточно нажать на ссылку\)\n\n Персональная ссылка:\n`https://t.me/open_vpn_sale_bot?start=" + str(message.from_user.id) + "`",
                            parse_mode = ParseMode.mdv2.value)
            return
        bot.send_message(config.ADMINCHAT,
                            "[" + utils.form_text_markdownv2(str(message.from_user.full_name)) +
                            "](tg://user?id\=" + str(message.from_user.id) +
                            "):\n" +
                            utils.form_text_markdownv2(message.text) +
                            "\nid:" + str(message.from_user.id),
                            parse_mode=ParseMode.mdv2.value,
                            reply_markup=UserList.addButtonKeyForUsersList(str(message.from_user.id), dataCur['action']))



@bot.message_handler(content_types=[ContentTypes.text.value])
def text_handler(message: types.Message):
    if checkGiftCode(message):
        return successfully_paid(message.from_user.id, optionText="Подарок активирован")
    if message.from_user.id == config.ADMINCHAT and message.reply_to_message:
        try:
            user_id = str(message.reply_to_message.text).split('id:', -1)[1]
            bot.copy_message(chat_id=user_id, from_chat_id=config.ADMINCHAT, message_id=message.id)
            return
        except Exception as e:
            bot.send_message(
                config.ADMINCHAT,
                reply_to_message_id=message.id,
                text='message not send ```error\n' + utils.form_text_markdownv2(str(e)) + '\n```',
                parse_mode=ParseMode.mdv2.value)
            return
    



@bot.message_handler(content_types=[ContentTypes.photo.value],
                     func= lambda message: message.from_user.id != config.ADMINCHAT)
def photo_chek(message: types.Message):

    bot.send_message(chat_id=message.from_user.id, reply_to_message_id=message.id,
                     text="Отправлено администраторам на проверку. Вы получите уведомление с результатом, ожидайте...")
    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT action, server_desired FROM users_subscription WHERE telegram_id=" + str(message.from_user.id))
        dataCur = cursor.fetchone()
        try:
            bot.send_photo(config.ADMINCHAT, photo=message.photo[0].file_id,
                   caption="server: " + utils.form_text_markdownv2(str(dataCur["server_desired"])) +
                   "\nuser: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ") \n\nid: " + str(message.from_user.id),
                   reply_markup=UserList.addButtonKeyForUsersList(str(message.from_user.id), dataCur["action"]),
                   parse_mode=ParseMode.mdv2.value)
        except Exception as e:
            bot.send_photo(
                config.ADMINCHAT,
                photo=message.photo[0].file_id,
                caption="\nuser: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ") \n\nid:" + str(message.from_user.id),
                parse_mode=ParseMode.mdv2.value
            )


@bot.message_handler(content_types=[ContentTypes.photo.value],
                     func= lambda message: message.from_user.id == config.ADMINCHAT and message.reply_to_message)
def _(message: types.Message):
    user_id = message.reply_to_message.text.split('id:')[1]
    bot.copy_message(user_id, config.ADMINCHAT, message.id)


@bot.message_handler(func= lambda message: message.chat.id == config.ADMINCHAT and 
                     (message.reply_to_message.caption or message.reply_to_message.text))
def _(message: types.Message):

    user_id = str(message.reply_to_message.caption).split('id:', -1)[1]
    bot.copy_message(chat_id=user_id, from_chat_id=config.ADMINCHAT, message_id=message.id)
    return



@bot.message_handler(content_types=[ContentTypes.document.value])
def file_chek(message: types.Message):
    if message.from_user.id == config.ADMINCHAT:
        try:
            user_id = str(message.reply_to_message.caption).split('id:', -1)[1]
            bot.copy_message(chat_id=user_id, from_chat_id=config.ADMINCHAT, message_id=message.id)
            return
        except Exception as e:
            bot.send_message(config.ADMINCHAT, reply_to_message_id=message.id, text='не удалось отправить сообщение по причине ```\n' + str(e) + '\n```')
            return
    bot.send_message(chat_id=message.from_user.id, reply_to_message_id=message.id,
                     text="Отправлено администраторам на проверку. Вы получите уведомление с результатом, ожидайте...")
    with db.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT action, server_desired FROM users_subscription WHERE telegram_id=" + str(message.from_user.id))
        dataCur = cursor.fetchone()
    
        bot.send_document(config.ADMINCHAT, document=message.document.file_id,
                      caption="server: " + utils.form_text_markdownv2(str(dataCur["server_desired"])) + "user: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ")\n\nid:" + str(message.from_user.id),
                      reply_markup=UserList.addButtonKeyForUsersList(str(message.from_user.id), dataCur["action"]),
                      parse_mode=ParseMode.mdv2.value)
        


@bot.message_handler(content_types=[ContentTypes.sticker.value])
def file_chek(message: types.Message):
    bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.id, text="Стикеры не поддреживаются в данном диалоге")



@bot.callback_query_handler(func=lambda call: str(call.data).startswith('{"key":'))
def callback_woker(call: types.CallbackQuery):

    call_data = json.loads(call.data)
    username = call.from_user.full_name
    logging.info("chat: " + str(call.message.chat.title) + ", user:" + str(username) + " нажата кнопка с ключем " + call_data['key'])

    match call_data['key']:

        case "try":

            month = config.FIRST_START_DURATION_MONTH

            bot.delete_message(call.message.chat.id, call.message.id)
            oldMessage = bot.send_photo(chat_id=call.from_user.id, photo=open(config.FILE_URL + "4rrr.jpg", "rb"),
                              caption="Идет формирование конфигурации. Это может занять несколько минут...")
            if 'invitedId' in call_data:

                add_user(call_data['invitedId'], 1)
                
                bot.send_photo(call_data['invitedId'],
                            photo=open(config.FILE_URL + "image/referalYes.png", "rb"),
                            caption="Дата окончания подписки изменена")

            add_user(call.from_user.id,
                month,
                name_user=utils.form_text_markdownv2(username, delete=True),
                server=call_data['server']
            )
            successfully_paid(call.from_user.id, oldMessage.id)
        
        case "sale":
            
            with db.cursor() as cursor:
                cursor.execute("UPDATE users_subscription SET name = '" + call.from_user.full_name + "' WHERE telegram_id =" + str(call.from_user.id))
                db.commit()

            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(types.InlineKeyboardButton(text= "Нидерланды", callback_data='{"key": "pollCountMonth", "server": ' + str(Servers.niderlands2.value) + '}'),
                        types.InlineKeyboardButton(text= "Германия", callback_data='{"key": "pollCountMonth", "server": ' + str(Servers.deutsche.value) + '}'))
            
            if 'back' in call_data:

                return bot.edit_message_caption(
                    utils.form_text_markdownv2(config.TextsMessages.select_country.value),
                    call.message.chat.id,
                    call.message.id,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.mdv2.value
                )

            bot.send_photo(
                call.from_user.id,
                photo = open(config.FILE_URL + "vpn_option.png", "rb"),
                caption = utils.form_text_markdownv2(config.TextsMessages.select_country.value),
                parse_mode=ParseMode.mdv2.value,
                reply_markup=keyboard
            )
        case "tryServers":

            optionText = ""
            if "invitedId" in call_data:
                optionText = ', "invitedId": ' + str(call_data['invitedId'])

            keyboard = quick_markup(
                {
                    "Нидерланды": {'callback_data': '{"key": "try", "server": ' + str(Servers.niderlands2.value) + optionText + '}'},
                    "Германия": {'callback_data': '{"key": "try", "server": ' + str(Servers.deutsche.value) + optionText + '}'}
                },
                row_width=1
            )


            bot.edit_message_text(
                chat_id=call.from_user.id,
                message_id=call.message.id,
                text = utils.form_text_markdownv2(config.TextsMessages.select_country.value),
                parse_mode=ParseMode.mdv2.value,
                reply_markup=keyboard
            )

        case KeyCall.pollCountMonth.value:
            
            if "gift" in call_data:
                key = "getGiftCode"
                keyBack = ""
            else:
                key = "getLinkPayment"
                keyBack = "sale"

            keyboard = quick_markup(
                {
                    '1 мес.| ' + str(config.PRICE) + " руб.": {'callback_data': '{"key": "' + key + '", "server": ' + str(call_data['server']) + ', "month": 1}'},
                    '3 мес.| ' + str(config.PRICE * 3) + " руб.": {'callback_data': '{"key": "' + key + '", "server": ' + str(call_data['server']) + ', "month": 3}'},
                    '6 мес.| ' + str(config.PRICE * 6) + " руб.": {'callback_data': '{"key": "' + key + '", "server": ' + str(call_data['server']) + ', "month": 6}'},
                    '12 мес.| ' + str(config.PRICE * 12) + " руб.": {'callback_data': '{"key": "' + key + '", "server": ' + str(call_data['server']) + ', "month": 12}'},
                    '<<< назад': {'callback_data': '{"key": "' + keyBack + '", "back": 1}'}
                },
                row_width=2
            )
            bot.edit_message_caption("На какой срок?", call.message.chat.id, call.message.id, reply_markup=keyboard)
        
        case "getGiftCode":

            label = (str(call.from_user.id) + 
                     str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))).replace(" ", "").replace("-","").replace("+", "").replace(".", "").replace(":", "")

            keyboard = quick_markup(
                {
                    'Перейти к оплате': {'url': getLinkPayment(label, call_data['month'])},
                    '<<< назад': {'callback_data': '{"key": "pollCountMonth", "server": ' + str(call_data['server']) + ', "gift": true}'}
                },
                row_width=1
            )
            
            bot.edit_message_caption(config.TextsMessages.giftPay.value, call.message.chat.id, call.message.id, reply_markup=keyboard)

            checkPayment = Thread(target=pollingInfoLastPaymentGift, args=(label, call_data['month'], call.from_user.id, call.message.id, call.from_user.full_name))
            checkPayment.start()

        case "getLinkPayment":

            label = (str(call.from_user.id) + 
                     str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))).replace(" ", "").replace("-","").replace("+", "").replace(".", "").replace(":", "")

            keyboard = quick_markup(
                {
                    'Перейти к оплате': {'url': getLinkPayment(label, call_data['month'])},
                    '<<< назад': {'callback_data': '{"key": "pollCountMonth", "server": ' + str(call_data['server']) + '}'}
                },
                row_width=1
            )
            
            bot.edit_message_caption("Вы выбали сервер " + getServerNameById(call_data['server']), call.message.chat.id, call.message.id, reply_markup=keyboard)

            checkPayment = Thread(target=pollingInfoLastPayment, args=(label, call_data['server'], call_data['month'], call.from_user.id, call.message.id, call.from_user.full_name))
            checkPayment.start()

        case "connect":

            key = types.InlineKeyboardMarkup()
            key.add(*[types.InlineKeyboardButton(text=i, callback_data='{"key": "action", "id": "' + str(call_data['id']) + '", "month": "' + str(i) + '", "s":' + str(call_data['serverId']) + '}') for i in range(1,13)],
                    types.InlineKeyboardButton(text="Назад", callback_data='{"key": "backConnectKey", "id": "' + str(call_data['id']) + '"}'))
            if call.message.content_type == "text":
                bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.id, text = call.message.text, reply_markup = key)
            else:
                bot.edit_message_caption(chat_id = call.message.chat.id, message_id = call.message.id, caption = call.message.caption, reply_markup = key)
        
        case "backConnectKey":

            with db.cursor() as cursor:
                cursor.execute("SELECT action FROM users_subscription WHERE telegram_id={}".format(call_data['id']))
                action = cursor.fetchone()[0]
                bot.edit_message_caption(chat_id = call.message.chat.id, message_id = call.message.id, caption = call.message.caption,
                                     reply_markup = UserList.addButtonKeyForUsersList(str(call_data['id']), action))
            return
        
        case "action":

            server = None
            if call.message.chat.id == config.ADMINCHAT:
                try:
                    username = str(call.message.caption).split(": ", 1)[1]
                except Exception:
                    username = str(call.message.text).split(" ", -2)[0]
            if "s" in call_data:
                add_user(call_data['id'], call_data["month"], name_user=username, server=call_data['s'])
            else:
                add_user(call_data['id'], call_data["month"], name_user=username)

            if successfully_paid(call_data['id']):
                bot.answer_callback_query(callback_query_id=call.id, text="Подписка активирована, сообщение пользователю отправлено", show_alert=True)
            else:
                bot.answer_callback_query(callback_query_id=call.id, text="Подписка активирована, но сообщение не отправлено. Требуется оповестить в ручном режиме.")
            
            if managment_user.manager_users_list.statusSearch == StatusSearch.search:
                managment_user.manager_users_list.search_user(call.message)
            elif managment_user.manager_users_list.statusSearch == StatusSearch.all:
                managment_user.manager_users_list.search_all_user(call.message)

        case "deaction":
        
            del_user(call_data['id'])

            if managment_user.manager_users_list.statusSearch == StatusSearch.search:
                managment_user.manager_users_list.search_user(call.message)
            elif managment_user.manager_users_list.statusSearch == StatusSearch.all:
                managment_user.manager_users_list.search_all_user(call.message)

            bot.answer_callback_query(callback_query_id=call.id,
                                    text="Подписка успешно отключена",
                                    show_alert=True)
            
        case "not_action":

            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call_data['id'], "Покупка отклонена администратором")

        case "faq_video":

            bot.send_video(call.from_user.id, open("/root/bot_vpn/video/0809.mp4", "rb"), width=888, height=1920)

        case "faq_ios":
            
            with db.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT server_link FROM users_subscription WHERE telegram_id =" + str(call.from_user.id))
                bot.send_message(call.from_user.id,
                                 config.TextsMessages.faqIos.value.format(utils.form_text_markdownv2(cursor.fetchone()["server_link"])),
                                 parse_mode=config.ParseMode.MarkdownV2.value)

        case "comands_video":

            bot.send_video(call.from_user.id, open("/root/bot_vpn/video/08.mp4", "rb"), width=888, height=1920)

        case "page_client_next":

            managment_user.manager_users_list.start += config.COUNT_PAGE
            managment_user.manager_users_list.search_all_user(call.message)

        case "page_client_back":

            managment_user.manager_users_list.start -= config.COUNT_PAGE
            managment_user.manager_users_list.search_all_user(call.message)

        case "home_key_faq":

            bot.send_video(call.from_user.id, open("/root/bot_vpn/video/999.mp4", "rb"), width=888, height=1920)

        case "data_user":

            data_user(call_data['id'])

        case "option_where":

            if managment_user.manager_users_list.one_active == 0:
                managment_user.manager_users_list.one_active = 1
            else:
                managment_user.manager_users_list.one_active = 0
            managment_user.manager_users_list.start = 0
            managment_user.manager_users_list.search_all_user(call.message)
    
        case "pppd":

            bot.send_message(call.message.chat.id, config.TextsMessages.TEXTPERSONINFO.value)

        case "termsOfUse":

            bot.send_message(call.message.chat.id, config.TextsMessages.TEXTTERMS.value)
    
        case "manualSettings":

            manualSuccessfullyPaid(call_data['id'], oldMessageId=call.message.id)

        case "backmanualSettings":

            successfully_paid(call_data['id'], oldMessageId=call.message.id)

        case "sendConf":

            if successfully_paid(call_data['id']):
                bot.answer_callback_query(callback_query_id=call.id, text='Отправлено', show_alert=True)
            
        case _:

            bot.answer_callback_query(callback_query_id=call.id, text='Кнопка еще не настроена.')


bot.infinity_polling()
