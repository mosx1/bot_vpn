import time, threading, config, string, secrets, utils, keyboards
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

from tables import User

from users.methods import get_user_by_id, get_user_by
from users.entities import UserStates

from servers.server_list import Country
from servers.methods import get_server_name_by_id

from configparser import ConfigParser

from network_service import controllerFastApi


class StatusSearch(Enum):
    
    one = 0
    all = 1
    search = 2

class UserList:
    
    def __init__(self, message = None, filter = None) -> None:

        conf = ConfigParser()
        conf.read(f'{config.FILE_URL}config.ini')

        self.config = conf['UserList']
        self.mes_arr = []
        self.start = 0
        self.one_active: bool = False
        self.statusSearch: StatusSearch
        self.search_text = ""
        self.filters = filter
        if message:
            self.search_user(message)


    def __del__(self):
        if len(self.mes_arr) != 0:
            for item in self.mes_arr:
                bot.delete_message(config.ADMINCHAT, item)

    
    def next_page(self, message) -> None:
        self.start += self.config.getint('items_on_page')
        self.search_user(message)


    def back_page(self, message) -> None:
        self.start -= self.config.getint('items_on_page')
        self.search_user(message)
    

    def search_user(self, message) -> None:

        users: list[User] = get_user_by(
            self.filters,
            self.config.getint('items_on_page'),
            self.start
        )
        self.manager_users_list(message, users)


    def manager_users_list(self, message: types.Message, users: list[User | None]) -> None:

        text_key_where = "Показать только активные"
        if self.one_active:
            text_key_where = "Показать все"
        if len(users) == 0:
            self.start -= self.config.getint('items_on_page')
            return
        if len(users) < self.config.getint('items_on_page'):
            res = self.config.getint('items_on_page') - len(users)
            for b in range(res):
                users.append(None)
            button_nav = [types.InlineKeyboardButton(text="<", callback_data='{"key": "page_client_back"}')]
        if self.start == 0:
            button_nav = [types.InlineKeyboardButton(text=">", callback_data='{"key": "page_client_next"}')]
        else:
            button_nav = [types.InlineKeyboardButton(text="<", callback_data='{"key": "page_client_back"}'),
                          types.InlineKeyboardButton(text=">", callback_data='{"key": "page_client_next"}')]
            
        for a, user in enumerate(users):

            paid = '\-'
            status = '\-'
            name = '\-'
            telegram_id: str = str(message.from_user.id)
            date = '\-'
            statistic = '\-'
            keyboard_offer_one = None

            keyboard_offer_one: types.InlineKeyboardMarkup = self.addButtonKeyForUsersList(
                user,
                a, 
                button_nav, 
                text_key_where
            )

            if user:

                    paid: str = paidCheckActive(user.paid)
                    status: str = textCheckActive(user.action)
                    name: str = utils.form_text_markdownv2(user.name)
                    telegram_id: str = str(user.telegram_id)
                    date: str = utils.replaceMonthOnRuText(user.exit_date)
                    statistic: str = utils.form_text_markdownv2(user.statistic)

            if len(self.mes_arr) < self.config.getint('items_on_page'):

                m: types.Message = bot.send_message(
                    message.chat.id,
                    str(paid) + str(status) + "[" + str(name) + "](tg://user?id\=" + str(telegram_id) + ") " + str(date) + 
                    "\n" + str(statistic),
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard_offer_one,
                    disable_notification=True
                )
                self.mes_arr.append(m.id)
            
            else:

                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=self.mes_arr[a],
                    text = str(paid) + str(status) + "[" + str(name) + "](tg://user?id\=" + str(telegram_id) + ") " + str(date) + 
                    "\n" + str(statistic),
                    parse_mode="MarkdownV2",
                    reply_markup=keyboard_offer_one
                )

        
    @classmethod
    def addButtonKeyForUsersList(self, user: User | None = None, a: int = 0, buttonNav: list = None, textKeyWhere: str = None) -> types.InlineKeyboardMarkup:
        keyboard_offer_one = types.InlineKeyboardMarkup()
        if user:
            if user.action:

                inlineKeyConnect = types.InlineKeyboardButton(
                        text="+",
                        callback_data='{"key": "connect", "id": ' + str(user.telegram_id) + ', "serverId": ' + str(user.server_id) + '}'
                    )

                keyboard_offer_one.add(
                    inlineKeyConnect,
                    types.InlineKeyboardButton(
                        text="Отключить", 
                        callback_data='{"key": "deaction", "id": "' + str(user.telegram_id) + '"}'
                    ),
                    types.InlineKeyboardButton(
                        text="Данные", 
                        callback_data='{"key": "data_user", "id": "' + str(user.telegram_id) + '"}'
                    ),
                    types.InlineKeyboardButton(
                        text="Отправить конфиг", 
                        callback_data='{"key": "sendConf", "id": "' + str(user.telegram_id) + '"}'
                    )
                )
                
            else:
                keyboard_offer_one.add(
                    types.InlineKeyboardButton(
                        text="Германия", 
                        callback_data='{"key": "connect", "id": "' + str(user.telegram_id) + '", "serverId": ' + str(utils.get_very_free_server(Country.deutsche)) + '}'
                    ),
                    types.InlineKeyboardButton(
                        text="Нидерланды", 
                        callback_data='{"key": "connect", "id": "' + str(user.telegram_id) + '", "serverId": ' + str(utils.get_very_free_server(Country.niderlands)) + '}'
                    ),
                    types.InlineKeyboardButton(
                        text="Данные", 
                        callback_data='{"key": "data_user", "id": "' + str(user.telegram_id) + '"}'
                    )
                )
        if a == config.COUNT_PAGE - 1:
            keyboard_offer_one.row(*buttonNav)
            keyboard_offer_one.add(types.InlineKeyboardButton(text=textKeyWhere, callback_data='{"key": "option_where"}'))
        return keyboard_offer_one


def add_user(
        user_id,
        month,
        name_user=None,
        server=None
) -> config.AddUserMessage:
    
    conf = ConfigParser()
    conf.read(config.FILE_URL + "config.ini")

    admin_chat_id: int = conf['Telegram'].getint('admin_chat')
    
    intervalSql = " + INTERVAL '" + str(month) + " months'"
    
    if not name_user:
        name_user = str(user_id)

    user: User | None = get_user_by_id(user_id)

    if user:
        server: int = user.server_id

    if (not server) and (not user):
        server: int = utils.get_very_free_server()

    with db.cursor() as cursor:

        if not user:
            
            if bot.get_state(user_id) == UserStates.creation:
                
                return config.AddUserMessage.error
            
            bot.set_state(
                user_id,
                UserStates.creation
            )

            logging.info("добавляю user: " + name_user)
            
            result_add_vpn_user: str | controllerFastApi.NetworkServiceError = controllerFastApi.add_vpn_user(user_id, server)

            match result_add_vpn_user:

                case str():

                    cursor.execute(
                        "INSERT INTO users_subscription (telegram_id, name, exit_date, action, server_link, server_id, protocol)" +
                        "\nVALUES ('" + str(user_id) + "', '" + str(name_user) + "', now() " + str(intervalSql) + ", True, '" + result_add_vpn_user + "', '" + str(server) + "', " + str(config.DEFAULTPROTOCOL) + ");"
                    )

                    db.commit()

                    bot.send_message(
                        config.ADMINCHAT, 
                        "new user: [" + utils.form_text_markdownv2(name_user) + "](tg://user?id\=" + str(user_id) + ")", 
                        parse_mode=ParseMode.mdv2.value 
                    )

                    logging.info(name_user + " успешно добавлен")

                    return config.AddUserMessage.extended

                case controllerFastApi.NetworkServiceError():
                    
                    text: str = f"{result_add_vpn_user.caption}\nЗапрос:\n{result_add_vpn_user.response}"

                    bot.send_message(
                        admin_chat_id,
                        text
                    )
                    logging.error(text)
                    
                    return config.AddUserMessage.error
                
            bot.delete_state(user_id)

        elif not user.action:
            
            renewalOfSubscription(user, intervalSql, serverNew=server)

            if int(user.server_id) == int(server):
                return config.AddUserMessage.extended
            else:
                return config.AddUserMessage.error

        elif user.action:
            # servers: list[ServersTable] = get_server_list()
            if server != user.server_id:
                del_user(user_id, noUpdate=True)
                add_user(user_id, month, server=server)

                return config.AddUserMessage.extended

            cursor.execute(
                "UPDATE users_subscription" + 
                "\nSET exit_date= exit_date " + intervalSql + ", paid=True" +
                "\nWHERE telegram_id=" + str(user_id)
            )
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
    
    return bot.send_message(user_id,
        text,
        reply_markup=keyboards.getInlineExtend()
    )



def generate_alphanum_crypt_string():
    letters_and_digits = string.ascii_letters + string.digits
    crypt_rand_string = ''.join(secrets.choice(letters_and_digits) for i in range(16))
    return crypt_rand_string
    

def data_user(id: int) -> types.Message:

    m: types.Message = bot.send_message(config.ADMINCHAT, "Загрузка...")

    user: User | None = get_user_by_id(int(id))
    if not user:
        return bot.edit_message_text(
            chat_id=m.chat.id,
            message_id= m.id,
            text= "Пользователь незарегистрирован"
        )
    keyboard: types.InlineKeyboardMarkup = UserList.addButtonKeyForUsersList(user)
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
            get_server_name_by_id(user.server_id)
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

    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')
    admin_chat_id: int = conf['Telegram'].getint('admin_chat')

    with Session(engine) as session:
        query = select(
            func.json_agg(User.telegram_id).label('user_ids'),
            User.server_id
        ).where(User.action == False).group_by(User.server_id)
        data = session.execute(query).all()

        for item in data:

            server_name: str = get_server_name_by_id(item.server_id)
            
            old_message: types.Message = bot.send_message(
                admin_chat_id, 
                f'Удаление неактивных пользователей с сервера {server_name}'
            )

            controllerFastApi.del_users(set(item.user_ids), item.server_id)

            text: str = f'Удалены неактивные пользователи с сервера {server_name}'

            logging.info(text)

            bot.edit_message_text(
                text,
                old_message.chat.id,
                old_message.id
            )