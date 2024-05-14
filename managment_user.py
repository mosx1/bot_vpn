import os, time, threading, pytz, config, string, secrets, requests
from connect import db, logging, bot, form_text_markdownv2
from telebot import types
from datetime import datetime, timedelta

class UserList:
    def __init__(self):
        self.mes_arr = []
        self.start = 0
        self.one_active = 0


    def search_all_user(self, message):
        option_where = ""
        cur = db.cursor()
        if self.one_active == 1:
            option_where = " WHERE action = 1  ORDER BY datetime ASC "
        else:
            option_where = " ORDER BY id DESC "
        cur.execute("SELECT name, t_id, action, datetime FROM users_subscription " + option_where + " LIMIT " + str(self.start) + ", " + str(config.COUNT_PAGE))
        self.manager_users_list(message, cur.fetchall())
    

    def search_user(self, message):
        option_where = ""
        search_text = str(message.text).split(" ", 1)[1]
        cur = db.cursor()
        if self.one_active == 1:
            option_where = ", action = 1"
        cur.execute("SELECT name, t_id, action, datetime FROM users_subscription WHERE name LIKE '" + search_text + "%'" + option_where + " ORDER BY id DESC  LIMIT " + str(self.start) + ", " + str(config.COUNT_PAGE))
        self.manager_users_list(message, cur.fetchall())


    def manager_users_list(self, message, data_cur):
        a = 0
        text_key_where = "Показать только активные"
        if self.one_active == 1:
            text_key_where = "Показать все"
        if len(data_cur) == 0:
            self.start -= config.COUNT_PAGE
            return
        if len(data_cur) < config.COUNT_PAGE:
            res = config.COUNT_PAGE - len(data_cur)
            for b in range(res):
                data_cur.append((None, '-'))
            button_nav = [types.InlineKeyboardButton(text="<", callback_data='{"key": "page_client_back"}')]
        if self.start == 0:
            button_nav = [types.InlineKeyboardButton(text=">", callback_data='{"key": "page_client_next"}')]
        else:
            button_nav = [types.InlineKeyboardButton(text="<", callback_data='{"key": "page_client_back"}'), types.InlineKeyboardButton(text=">", callback_data='{"key": "page_client_next"}')]
        if len(self.mes_arr) == 0:
            for i in data_cur:
                keyboard_offer_one = types.InlineKeyboardMarkup()
                if len(str(i[1])) > 1:
                    if int(i[2]) == 0:
                        keyboard_offer_one.add(types.InlineKeyboardButton(text="Включить", callback_data='{"key": "action_button", "id": "' + str(i[1]) + '"}'), types.InlineKeyboardButton(text="Данные", callback_data='{"key": "data_user", "id": "' + str(i[1]) + '"}'))
                    else:
                        keyboard_offer_one.add(types.InlineKeyboardButton(text="+", callback_data='{"key": "action_button", "id": "' + str(i[1]) + '"}'), types.InlineKeyboardButton(text="Отключить", callback_data='{"key": "deaction", "id": "' + str(i[1]) + '"}'), types.InlineKeyboardButton(text="Данные", callback_data='{"key": "data_user", "id": "' + str(i[1]) + '"}'))
                if a == config.COUNT_PAGE - 1:
                    keyboard_offer_one.row(*button_nav)
                    keyboard_offer_one.add(types.InlineKeyboardButton(text=text_key_where, callback_data='{"key": "option_where"}'))
                try:
                    if int(i[2]) == 0:
                        status = "🔴"
                    elif int(i[2]) == 1:
                        status = "🟢"
                except Exception:
                    pass
                if i[0] == None:
                    text = "-"
                else:
                    text = status + "[" + form_text_markdownv2(i[0]) + "](tg://user?id\=" + str(i[1]) + ") " + form_text_markdownv2(i[3]) + "\n"
                m = bot.send_message(message.chat.id, text, parse_mode="MarkdownV2", reply_markup=keyboard_offer_one)
                self.mes_arr.append(m.id)
                a+=1
        else:
            for i in data_cur:
                keyboard_offer_one = types.InlineKeyboardMarkup()
                if len(str(i[1])) > 1:
                    if int(i[2]) == 0:
                        keyboard_offer_one.add(types.InlineKeyboardButton(text="Включить", callback_data='{"key": "action_button", "id": "' + str(i[1]) + '"}'), types.InlineKeyboardButton(text="Данные", callback_data='{"key": "data_user", "id": "' + str(i[1]) + '"}'))
                    else:
                        keyboard_offer_one.add(types.InlineKeyboardButton(text="+", callback_data='{"key": "action_button", "id": "' + str(i[1]) + '"}'), types.InlineKeyboardButton(text="Отключить", callback_data='{"key": "deaction", "id": "' + str(i[1]) + '"}'), types.InlineKeyboardButton(text="Данные", callback_data='{"key": "data_user", "id": "' + str(i[1]) + '"}'))
                if a == config.COUNT_PAGE - 1:
                    keyboard_offer_one.row(*button_nav)
                    keyboard_offer_one.add(types.InlineKeyboardButton(text=text_key_where, callback_data='{"key": "option_where"}'))
                try:
                    if int(i[2]) == 0:
                        status = "🔴"
                    elif int(i[2]) == 1:
                        status = "🟢"
                except Exception:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=self.mes_arr[a], text="\-", parse_mode="MarkdownV2", reply_markup=keyboard_offer_one)
                try:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=self.mes_arr[a], text=status + "[" + form_text_markdownv2(i[0]) + "](tg://user?id\=" + str(i[1]) + ") " + form_text_markdownv2(i[3]) + "\n", parse_mode="MarkdownV2", reply_markup=keyboard_offer_one)
                except Exception as e:
                    pass
                a+=1
        


def edit_mes_users_list(message, id):
    key_action = types.InlineKeyboardMarkup()
    key_action.add(*[types.InlineKeyboardButton(text=i, callback_data='{"key": "action", "id": "' + str(id) + '", "month": "' + str(i) + '"}') for i in range(1,13)],types.InlineKeyboardButton(text="Данные", callback_data='{"key": "data_user", "id": "' + str(id) + '"}'))
    bot.edit_message_text(chat_id= message.chat.id, message_id= message.id, text = message.text, reply_markup=key_action)


def add_token(id_user, name_user=None, month=None, time=None, extension=None, niderland=None):
    cur = db.cursor()
    cur.execute("SELECT datetime FROM users_subscription WHERE t_id=" + str(id_user) + " AND action=1")
    data_cur = cur.fetchone()
    if data_cur == None:
        moscow_time = datetime.strptime(str(datetime.now(pytz.timezone('Europe/Moscow')))[:16], "%Y-%m-%d %H:%M")
    else:
        moscow_time = datetime.strptime(data_cur[0][0:16], "%Y-%m-%d %H:%M")
    if (month == None) and (time != None):
        date_time_exit = moscow_time + timedelta(hours=time)
    elif (month != None) and (time == None):
        date_time_exit = moscow_time + timedelta(days=int(month)*30)
    add_user(id_user, date_time_exit, name_user=name_user, niderland=niderland)
    return date_time_exit


def add_user(id_user, date_time:str, name_user=None, niderland=None):
    
    if name_user == None:
        name_user = str(id_user)

    if niderland != None:
        server = config.SERVER_NID
    else:
        server = config.SERVER_USA
    cur = db.cursor()
    cur.execute("SELECT action FROM users_subscription WHERE t_id=" + str(id_user))
    data_cur = cur.fetchone()
    if data_cur == None:
        logging.info("добавляю user: " + name_user)
        hach_user = add_vpn_user(name_user, niderland=niderland)
        cur.execute("INSERT INTO users_subscription (t_id, name, datetime, action, id_server, link_server, server)" +
                    "\nVALUES ('" + str(id_user) + "', '" + str(name_user) + "', '" + str(date_time) + "', 1, '" + str(hach_user['id']) + "', '" + str(hach_user['link']) + "', '" + server + "');")
        db.commit()
        bot.send_message(config.ADMINCHAT, "new user: [" + form_text_markdownv2(name_user) + "](tg://user?id\=" + str(id_user) + ")", parse_mode="MarkdownV2" )
        logging.info(name_user + " успешно добавлен")
    elif data_cur[0] == 0:
        hach_user = add_vpn_user(name_user, niderland=niderland)
        cur.execute("UPDATE users_subscription" + 
                    "\nSET datetime='" + str(date_time) + "',action=1, paid=1, id_server=" + str(hach_user['id']) + ", link_server='" + str(hach_user['link']) + "', server = '" + server + "'" +
                    "\nWHERE t_id=" + str(id_user))
        db.commit()
    elif data_cur[0] == 1:
        cur.execute("UPDATE users_subscription" + 
                    "\nSET datetime='" + str(date_time) + "', paid=1" +
                    "\nWHERE t_id=" + str(id_user))
    return


def del_user(id_user):
    server = config.API_URL
    try:
        cur = db.cursor()
        cur.execute("UPDATE users_subscription SET action=0 WHERE t_id=" + str(id_user) +
                    "\nRETURNING id_server, server")
        dataCur = cur.fetchone()
        db.commit()
        if dataCur[1]:
            if dataCur[1] == config.SERVER_NID:
                server = config.API_URL_NIDERLAND
        requests.Session().delete(f"{server}/access-keys/{dataCur[0]}", verify=False)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Купить еще месяц", callback_data='{"key": "sale"}'))
        bot.send_message(id_user, "Подписка окончена.", reply_markup=keyboard)
    except Exception as e:
        logging.error("не найден пользователь в БД или конфигурации VPN: " + str(e))






def chek_subscription():
    while True:
        moscow_time = str(datetime.now(pytz.timezone('Europe/Moscow')))
        now_time = datetime.strptime(str(moscow_time)[:16], "%Y-%m-%d %H:%M")
        cur = db.cursor()
        cur.execute("SELECT t_id, datetime FROM users_subscription WHERE action=1")
        data_cur = cur.fetchall()
        if len(data_cur) != 0:
            for data in data_cur: 
                finich_time = datetime.strptime(data[1][0:16], "%Y-%m-%d %H:%M")
                if now_time > finich_time:
                    del_user(data[0])
                elif now_time == finich_time - timedelta(days=1):
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton(text="Купить", callback_data='{"key": "sale"}'))
                    bot.send_message(data[0], "Завтра в это же время окончится подписка на VPN, чтобы не потерять доступ, оплатите и отправьте подверждение платежа.", reply_markup=keyboard)
            db.close
        time.sleep(60)
        

chek_sub_thread = threading.Thread(target=chek_subscription)
chek_sub_thread.start()

def add_vpn_user(name_user, niderland=None):
    if niderland != True:
        apiUrl = config.API_URL_NIDERLAND
    else:
        apiUrl = config.API_URL
    response = requests.post(f"{apiUrl}/access-keys/",
                             verify=False,
                             json={"name": name_user},
                             headers={'Content-Type':'application/json'})
    response_json = response.json()
    hach_user = {"id" : response_json.get('id'),
                 "link" : response_json.get("accessUrl")}
    return hach_user



def generate_alphanum_crypt_string():
    letters_and_digits = string.ascii_letters + string.digits
    crypt_rand_string = ''.join(secrets.choice(letters_and_digits) for i in range(16))
    return crypt_rand_string


def referal(message):
    bot.send_photo(message.from_user.id, open("/root/bot_vpn/num_login.png", "rb"), caption="Введите номер учетной записи человека, который по вашей рекомендации оплатил VPN (пробный период не в счет)")
    bot.register_next_step_handler(message, ref_action)

def ref_action(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Купить на месяц", callback_data='{"key": "sale"}'))
    cur = db.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users_subscription WHERE (t_id=" + str(message.from_user.id) + " OR t_id=" + str(message.text) + ") AND action=1 AND paid=1")
    except Exception:
        bot.send_message(message.from_user.id, "Ошибка. Проверьте:\n- правильно ли вы ввели название файла;\n- оформлена ли подписка у пользователя;\n- оформлена ли у вас подписка", reply_markup=keyboard)
        bot.send_message(config.ADMINCHAT, "[" + form_text_markdownv2(names[0]) + "](tg://user?id\=" + str(message.from_user.id) + ") не активировал рефералку за счет пользователя [" + form_text_markdownv2(names[1]) + "](tg://user?id\=" + str(message.text) + ")", parse_mode="MarkdownV2")
        return
    count = cur.fetchone()[0]
    if int(count) != 2:
        bot.send_message(message.from_user.id, "Ошибка. Проверьте:\n- правильно ли вы ввели название файла;\n- оформлена ли подписка у пользователя;\n- оформлена ли у вас подписка", reply_markup=keyboard)
        bot.send_message(config.ADMINCHAT, "[" + form_text_markdownv2(names[0]) + "](tg://user?id\=" + str(message.from_user.id) + ") не активировал рефералку за счет пользователя [" + form_text_markdownv2(names[1]) + "](tg://user?id\=" + str(message.text) + ")", parse_mode="MarkdownV2")
        return
    cur.execute("SELECT COUT(*) FROM referal WHERE (t_id_who=" + str(message.from_user.id) + " AND t_id_whom=" + str(message.text) + ") OR (t_id_who=" + str(message.text) + " AND t_id_whom=" + str(message.from_user.id) + ");")
    count = cur.fetchone()[0]
    if int(count) == 0:
        cur.execute("INSERT INTO referal (t_id_who, t_id_whom) VALUES ('" + str(message.from_user.id) + "', '" + str(message.text) + "')")
        db.commit()
        datetime_exit = add_token(message.from_user.id, month=1, extension=True)
        bot.send_message(message.from_user.id, "Бонус успешно активирован, доступ к vpn продлен до " + str(datetime_exit))
        cur.execute("SELECT name FROM users_subscription WHERE t_id=" + str(message.from_user.id) + " OR t_id=" + str(message.text))
        names = cur.fetchall()
        bot.send_message(config.ADMINCHAT, "[" + form_text_markdownv2(names[0]) + "](tg://user?id\=" + str(message.from_user.id) + ") добавил пользователя [" + form_text_markdownv2(names[1]) + "](tg://user?id\=" + str(message.text) + ") и получил 1 месяц в подарок", parse_mode="MarkdownV2")
    else:
        bot.send_message(message.from_user.id, "Ошибка. Ранее уже был активирован бонус.", reply_markup=keyboard)
        bot.send_message(config.ADMINCHAT, "[" + form_text_markdownv2(names[0]) + "](tg://user?id\=" + str(message.from_user.id) + ") хотел повторно активировать за счет [" + form_text_markdownv2(names[1]) + "](tg://user?id\=" + str(message.text) + ") рефералку", parse_mode="MarkdownV2")
        return
    

def data_user(id):
    cur = db.cursor()
    cur.execute("SELECT name, datetime, action, id_server, link_server FROM users_subscription WHERE t_id=" + str(id))
    data_cur = cur.fetchone()
    bot.send_message(config.ADMINCHAT, str(data_cur[0]) + "\n" + str(data_cur[1]) + "\n" + str(data_cur[2]) + "\n" + str(data_cur[4]) + "\n" + str(data_cur[3]))