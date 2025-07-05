import time, threading, config, string, secrets, utils, controllerFastApi, keyboards
from connect import db, logging, bot, engine
from telebot import types
from telebot.apihelper import ApiTelegramException

from enum import Enum

from enums.invite import CallbackKeys
from enums.keyCall import KeyCall
from enums.parse_mode import ParseMode

from psycopg2.extras import DictCursor

from protocols import getNameProtocolById

from managers.subscription.renewal_of_subscription import renewalOfSubscription

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from tables import User, ServersTable
from users.methods import get_user_by_id

from servers.server_list import Servers, Country
from servers.methods import get_server_list


class StatusSearch(Enum):
    
    one = 0
    all = 1
    search = 2

class UserList:
    
    def __init__(self, message = None):
        self.mes_arr = []
        self.start = 0
        self.one_active = True
        self.statusSearch: StatusSearch
        if message:
            self.search_user(message)


    def __del__(self):
        if len(self.mes_arr) != 0:
            for item in self.mes_arr:
                bot.delete_message(config.ADMINCHAT, item)

    def search_all_user(self, message):
        self.statusSearch = StatusSearch.all

        if self.one_active:
            option_where = " WHERE action = True  ORDER BY exit_date ASC "
        else:
            option_where = " ORDER BY name ASC "
        with db.cursor() as cursor:
            cursor.execute("SELECT name, telegram_id, action, exit_date, server_id, paid, statistic FROM users_subscription " +
                           option_where +
                           " LIMIT " +
                           str(config.COUNT_PAGE) +
                           " OFFSET " + str(self.start))
            self.manager_users_list(message, cursor.fetchall())
    

    def search_user(self, message):
        self.statusSearch = StatusSearch.search
        option_where = ""
        search_text = str(message.text).split(" ", 1)[1]
        if self.one_active:
            option_where = ", action = True"
        with db.cursor() as cursor:
            cursor.execute("SELECT name, telegram_id, action, exit_date, server_id, paid, statistic FROM users_subscription WHERE (name || telegram_id) ILIKE '%" + search_text + "%'" + option_where + " LIMIT  " + str(config.COUNT_PAGE) + " OFFSET " + str(self.start))
            self.data_cur = cursor.fetchall()
        self.manager_users_list(message)


    def manager_users_list(self, message: types.Message, data_cur=None) -> None:

        server: str = ""

        if data_cur:
            self.data_cur = data_cur
        a = 0
        text_key_where = "Показать только активные"
        if self.one_active:
            text_key_where = "Показать все"
        if len(self.data_cur) == 0:
            self.start -= config.COUNT_PAGE
            return
        if len(self.data_cur) < config.COUNT_PAGE:
            res = config.COUNT_PAGE - len(self.data_cur)
            for b in range(res):
                self.data_cur.append((None, '-'))
            button_nav = [types.InlineKeyboardButton(text="<", callback_data='{"key": "page_client_back"}')]
        if self.start == 0:
            button_nav = [types.InlineKeyboardButton(text=">", callback_data='{"key": "page_client_next"}')]
        else:
            button_nav = [types.InlineKeyboardButton(text="<", callback_data='{"key": "page_client_back"}'),
                          types.InlineKeyboardButton(text=">", callback_data='{"key": "page_client_next"}')]
        if len(self.mes_arr) == 0:
            for i in self.data_cur:
                if i[0] != None:
                    keyboard_offer_one = self.addButtonKeyForUsersList(str(i[1]), int(i[2]), a, button_nav, text_key_where, i[4])
                try:
                    status = textCheckActive(int(i[2]))
                except:
                    return
                
                if i[0] != None:
                    if len(i) == 5:
                        server = str(i[4])

                m: types.Message = bot.send_message(message.chat.id,
                                    paidCheckActive(i[5]) + status + "[" + utils.form_text_markdownv2(i[0]) +
                                    "](tg://user?id\=" + str(i[1]) + ") " +
                                    utils.form_text_markdownv2(str(i[3])[:-3]) + server + "\n" +
                                    utils.form_text_markdownv2(str(i[6])),
                                    parse_mode="MarkdownV2",
                                    reply_markup=keyboard_offer_one,
                                    disable_notification=True)
                self.mes_arr.append(m.id)
                a+=1
        else:
            for i in self.data_cur:
                if i[0] != None:
                    keyboard_offer_one = self.addButtonKeyForUsersList(str(i[1]), int(i[2]), a, button_nav, text_key_where, i[4])
                try:
                    status = textCheckActive(int(i[2]))
                except Exception:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=self.mes_arr[a], text="\-", parse_mode="MarkdownV2", reply_markup=keyboard_offer_one)
                try:
                    if len(i) == 5:
                        server = str(i[4])

                    bot.edit_message_text(chat_id=message.chat.id,
                                          message_id=self.mes_arr[a],
                                          text = paidCheckActive(i[5]) + status + "[" +
                                          utils.form_text_markdownv2(i[0]) +
                                          "](tg://user?id\=" + str(i[1]) +
                                          ") " + utils.form_text_markdownv2(str(i[3])[:-3]) + server + "\n" +
                                          utils.form_text_markdownv2(str(i[6])),
                                          parse_mode="MarkdownV2",
                                          reply_markup=keyboard_offer_one)
                except Exception as e:
                    continue
                a+=1
        
    @classmethod
    def addButtonKeyForUsersList(self, user_id: str, user_status: bool, a: int = 0, buttonNav: list = None, textKeyWhere: str = None, server: str = None) -> object:
        keyboard_offer_one = types.InlineKeyboardMarkup()
        if user_id:
            if user_status:
                if not server:
                    user: User = get_user_by_id(int(user_id))
                    server = user.server_id

                inlineKeyConnect = types.InlineKeyboardButton(
                        text="+",
                        callback_data='{"key": "connect", "id": ' + user_id + ', "serverId": ' + str(server) + '}'
                    )

                keyboard_offer_one.add(
                    inlineKeyConnect,
                    types.InlineKeyboardButton(
                        text="Отключить", 
                        callback_data='{"key": "deaction", "id": "' + user_id + '"}'
                    ),
                    types.InlineKeyboardButton(
                        text="Данные", 
                        callback_data='{"key": "data_user", "id": "' + user_id + '"}'
                    ),
                    types.InlineKeyboardButton(
                        text="Отправить конфиг", 
                        callback_data='{"key": "sendConf", "id": "' + user_id + '"}'
                    )
                )
                
            else:
                keyboard_offer_one.add(
                    types.InlineKeyboardButton(
                        text="Германия", 
                        callback_data='{"key": "connect", "id": "' + user_id + '", "serverId": ' + str(utils.get_very_free_server(Country.deutsche)) + '}'
                    ),
                    types.InlineKeyboardButton(
                        text="Нидерланды", 
                        callback_data='{"key": "connect", "id": "' + user_id + '", "serverId": ' + str(Servers.niderlands2.value) + '}'
                    ),
                    types.InlineKeyboardButton(
                        text="Данные", 
                        callback_data='{"key": "data_user", "id": "' + user_id + '"}'
                    )
                )
        if a == config.COUNT_PAGE - 1:
            keyboard_offer_one.row(*buttonNav)
            keyboard_offer_one.add(types.InlineKeyboardButton(text=textKeyWhere, callback_data='{"key": "option_where"}'))
        return keyboard_offer_one


def add_user(
        userId,
        month,
        name_user=None,
        server=None
) -> config.AddUserMessage:
    
    intervalSql = " + INTERVAL '" + str(month) + " months'"
    
    if name_user == None:
        name_user = str(userId)

    with db.cursor() as cursor:

        cursor.execute("SELECT action, server_id FROM users_subscription WHERE telegram_id=" + str(userId))
        data_cur = cursor.fetchone()

        if server == None:
            if data_cur == None:
                server = config.DEFAULTSERVER
            else:
                server = data_cur[1]

        if data_cur == None:
            logging.info("добавляю user: " + name_user)

            link = controllerFastApi.add_vpn_user(userId, server)

            if link == False:
                bot.send_message(config.ADMINCHAT, "Ошибка добавления конфига пользователя")
                
                return config.AddUserMessage.error
                
            cursor.execute("INSERT INTO users_subscription (telegram_id, name, exit_date, action, server_link, server_id, protocol)" +
                        "\nVALUES ('" + str(userId) + "', '" + str(name_user) + "', now() " + str(intervalSql) + ", True, '" + str(link) + "', '" + str(server) + "', " + str(config.DEFAULTPROTOCOL) + ");")
            db.commit()
            bot.send_message(config.ADMINCHAT, "new user: [" + utils.form_text_markdownv2(name_user) + "](tg://user?id\=" + str(userId) + ")", parse_mode="MarkdownV2" )
            logging.info(name_user + " успешно добавлен")

            return config.AddUserMessage.extended

        elif data_cur[0] == False:

            renewalOfSubscription(userId, data_cur[1], intervalSql, serverNew=server)

            if int(data_cur[1]) == int(server):
                return config.AddUserMessage.extended
            else:
                return config.AddUserMessage.error

        elif data_cur[0]:
            servers: list[ServersTable] = get_server_list()
            if server != data_cur[1]:
                del_user(userId, noUpdate=True)
                add_user(userId, month, server=server)

                return config.AddUserMessage.extended

            cursor.execute("UPDATE users_subscription" + 
                    "\nSET exit_date= exit_date " + intervalSql + ", paid=True" +
                    "\nWHERE telegram_id=" + str(userId))
            db.commit()
            
            return config.AddUserMessage.extended
    


def del_user(id_user, noUpdate=None, no_message=None) -> None:
    
    name = ""

    with db.cursor(cursor_factory=DictCursor) as cursor:
        
        cursor.execute("UPDATE users_subscription SET action=False WHERE telegram_id=" + str(id_user) +
                    "\nRETURNING protocol, server_id, name")
        
        dataCur = cursor.fetchone()
        if noUpdate != True:

            db.commit()

            name = dataCur['name']

            if not no_message:
                try:
                    bot.send_message(id_user, "Подписка окончена.", reply_markup=keyboards.getInlineExtend())
                except ApiTelegramException as e:
                    bot.send_message(config.ADMINCHAT, str(e) + " " + name)
        else:
            db.rollback()

        controllerFastApi.suspendUser(id_user, dataCur["server_id"])




def chek_subscription():
    while True:
        with db.cursor() as cursor:
            cursor.execute("SELECT telegram_id FROM users_subscription WHERE action=True AND exit_date < now()")
            data_cur = cursor.fetchall()
            if len(data_cur) != 0:
                for data in data_cur:
                    del_user(data[0])
                    
            cursor.execute("SELECT telegram_id FROM users_subscription WHERE action=True AND (exit_date - INTERVAL '2 days') = now()")
            data_cur = cursor.fetchall()
            if len(data_cur) != 0:
                for data in data_cur:
                    notificationOverSubscription(data[0], "Через 2 дня окончится Ваша подписка на VPN. Чтобы не потерять доступ, продлите подписку.")
            
            cursor.execute("SELECT telegram_id FROM users_subscription WHERE action=True AND (exit_date - INTERVAL '1 days') = now()")
            data_cur = cursor.fetchall()
            if len(data_cur) != 0:
                for data in data_cur:
                        notificationOverSubscription(data[0], "Завтра в это же время окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку.")
           
            cursor.execute("SELECT telegram_id FROM users_subscription WHERE action=True AND (exit_date - INTERVAL '1 hours') = now()")
            data_cur = cursor.fetchall()
            if len(data_cur) != 0:
                for data in data_cur:
                        notificationOverSubscription(data[0], "Уже через час окончится подписка на VPN. Чтобы не потерять доступ, продлите подписку.")
        time.sleep(60)
        

chek_sub_thread = threading.Thread(target=chek_subscription)
chek_sub_thread.start()


def notificationOverSubscription(user_id, text: str) -> types.Message:
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Продлить", callback_data='{"key": "sale"}'))
    return bot.send_message(user_id,
        text,
        reply_markup=keyboard
    )



def generate_alphanum_crypt_string():
    letters_and_digits = string.ascii_letters + string.digits
    crypt_rand_string = ''.join(secrets.choice(letters_and_digits) for i in range(16))
    return crypt_rand_string
    

def data_user(id: int) -> types.Message:

    m: types.Message = bot.send_message(config.ADMINCHAT, "Загрузка...")

    user: User = get_user_by_id(int(id))
    if not user:
        return bot.edit_message_text(
            chat_id=m.chat.id,
            message_id= m.id,
            text= "Пользователь незарегистрирован"
        )
    keyboard: types.InlineKeyboardMarkup = UserList.addButtonKeyForUsersList(
        str(user.telegram_id),
        user.action,
        server=user.server_id
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text = "Обнулить баланс",
            callback_data = utils.callBackBilder(
                CallbackKeys.resetToZeroBalance,
                userId = id
            )
        )
    )
    keyboard.add(
        types.InlineKeyboardButton(
            text=KeyCall.refreshtoken.value,
            callback_data=utils.callBackBilder(
                KeyCall.refreshtoken,
                user_id = id
            )
        )
    )

    return bot.edit_message_text(
        chat_id=m.chat.id,
        message_id=m.id,
        text = paidCheckActive(user.paid) + textCheckActive(user.action) +
        " [" + utils.form_text_markdownv2(user.name) + "](tg://user?id\=" + str(user.telegram_id) +
        ")\nДата окончания подписки: " + utils.form_text_markdownv2(str(user.exit_date)) +
        "\n" + "\nlink: `" + utils.form_text_markdownv2(user.server_link) +
        "`\nСервер: " + utils.form_text_markdownv2(
            utils.get_server_name_by_id(user.server_id)
        ) +
        "\nprotocol: " + str(getNameProtocolById(user.protocol)) +
        "\nstat: " + utils.form_text_markdownv2(str(user.statistic)) +
        "\nбаланс: " + utils.form_text_markdownv2(str(user.balance)) +
        "\nid:" + str(user.telegram_id),
        parse_mode=ParseMode.mdv2.value,
        reply_markup = keyboard
    )
        


def textCheckActive(item: bool) -> str:
    if item:
        return "🟢"
    return "🔴"
    

def paidCheckActive(item: bool) -> str:
    if item:
        return "💵"
    return ""


def checkAndDeleteNotSubscription() -> None:
    with Session(engine) as session:
        query = select(
            func.json_agg(User.telegram_id).label('user_ids'),
            User.server_id
        ).where(User.action == False).group_by(User.server_id)
        data = session.execute(query).all()
        
        for item in data:
            controllerFastApi.del_users(set(item.user_ids), item.server_id)
            logging.info('Удалены неактивные пользователи с сервера.')