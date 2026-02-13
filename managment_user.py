import config, string, secrets, utils, keyboards

from connect import logging, bot

from telebot.apihelper import ApiTelegramException
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from enums.invite import CallbackKeys
from enums.keyCall import KeyCall, ReduceTime
from enums.parse_mode import ParseMode

from protocols import getNameProtocolById

from managers.subscription.renewal_of_subscription import renewalOfSubscription

from database import (
    User,
    get_user_by_id,
    get_user_by,
    get_server_name_by_id,
    get_very_free_server,
    insert_user,
    update_user_extend_subscription,
    update_user_deactivate,
    get_inactive_users_by_server,
)

from configparser import ConfigParser

from network_service import controllerFastApi
from network_service.entity import NetworkServiceError

class UserList:
    
    def __init__(self, message = None, filter = None) -> None:

        conf = ConfigParser()
        conf.read('config.ini')

        self.config = conf['UserList']
        self.mes_arr = []
        self.start = 0
        self.one_active: bool = False
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


    def manager_users_list(self, message: Message, users: list[User | None]) -> None:

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
            button_nav = [InlineKeyboardButton(text="<", callback_data='{"key": "page_client_back"}')]
        if self.start == 0:
            button_nav = [InlineKeyboardButton(text=">", callback_data='{"key": "page_client_next"}')]
        else:
            button_nav = [
                InlineKeyboardButton(text="<", callback_data='{"key": "page_client_back"}'),
                InlineKeyboardButton(text=">", callback_data='{"key": "page_client_next"}')
            ]
            
        for a, user in enumerate(users):

            paid = '\-'
            status = '\-'
            name = '\-'
            telegram_id: str = str(message.from_user.id)
            date = '\-'
            statistic = '\-'
            keyboard_offer_one = None

            keyboard_offer_one: InlineKeyboardMarkup = self.addButtonKeyForUsersList(
                user,
                a, 
                button_nav, 
                text_key_where
            )

            if user:

                    paid: str = paidCheckActive(user.paid)
                    status: str = utils.bool_in_circle_for_text(user.action)
                    name: str = utils.form_text_markdownv2(user.name)
                    telegram_id: str = str(user.telegram_id)
                    date: str = utils.replaceMonthOnRuText(user.exit_date)
                    statistic: str = utils.form_text_markdownv2(user.statistic)

            if len(self.mes_arr) < self.config.getint('items_on_page'):

                m: Message = bot.send_message(
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
    def addButtonKeyForUsersList(cls, user: User | None = None, a: int = 0, buttonNav: list = None, textKeyWhere: str = None) -> InlineKeyboardMarkup:
        keyboard_offer_one = InlineKeyboardMarkup()
        if user:
            if user.action:

                inlineKeyConnect = InlineKeyboardButton(
                        text="+",
                        callback_data='{"key": "connect", "id": ' + str(user.telegram_id) + ', "serverId": ' + str(user.server_id) + '}'
                    )

                keyboard_offer_one.add(
                    inlineKeyConnect,
                    InlineKeyboardButton(
                        text="-",
                        callback_data=utils.callBackBilder(
                            ReduceTime.timing,
                            id=user.telegram_id
                        )
                    ),
                    InlineKeyboardButton(
                        text="Отключить", 
                        callback_data='{"key": "deaction", "id": "' + str(user.telegram_id) + '"}'
                    ),
                    InlineKeyboardButton(
                        text="Данные", 
                        callback_data='{"key": "data_user", "id": "' + str(user.telegram_id) + '"}'
                    ),
                    InlineKeyboardButton(
                        text="Отправить конфиг", 
                        callback_data='{"key": "sendConf", "id": "' + str(user.telegram_id) + '"}'
                    )
                )
                
            else:

                keyboard_offer_one.add(
                    InlineKeyboardButton(
                        text="Выбрать сервер", 
                        callback_data='{"key": "' + KeyCall.list_servers_for_admin.name + '", "user_id": ' + str(user.telegram_id) + '}'
                    ),
                    InlineKeyboardButton(
                        text="Данные", 
                        callback_data='{"key": "data_user", "id": "' + str(user.telegram_id) + '"}'
                    ),
                    InlineKeyboardButton(
                        text="Отправить кнопку продления",
                        callback_data='{"key": "' + KeyCall.send_message_for_extension.name + '", "user_id": "' + str(user.telegram_id) + '"}'
                    ),
                    row_width=2
                )
        if a == config.COUNT_PAGE - 1:
            keyboard_offer_one.row(*buttonNav)
            keyboard_offer_one.add(InlineKeyboardButton(text=textKeyWhere, callback_data='{"key": "option_where"}'))
        return keyboard_offer_one


def add_user(
        user_id,
        month,
        name_user=None,
        server=None
) -> config.AddUserMessage:
    
    conf = ConfigParser()
    conf.read("config.ini")

    admin_chat_id: int = conf['Telegram'].getint('admin_chat')
    
    intervalSql = " + INTERVAL '" + str(month) + " months'"
    
    if not name_user:
        name_user = str(user_id)

    user: User | None = get_user_by_id(user_id)

    if not server:
        if user:
            server: int = user.server_id
        else:
            server: int = get_very_free_server()

    if not user:

        logging.info("добавляю user: " + name_user)

        result_add_vpn_user: str | controllerFastApi.NetworkServiceError = controllerFastApi.add_vpn_user(user_id, server)

        match result_add_vpn_user:

            case str():
                insert_user(
                    telegram_id=user_id,
                    name=name_user,
                    exit_date_expr=f"now() {intervalSql}",
                    server_link=result_add_vpn_user,
                    server_id=server,
                    protocol=config.DEFAULTPROTOCOL
                )
                bot.send_message(
                    config.ADMINCHAT,
                    "new user: [" + utils.form_text_markdownv2(name_user) + "](tg://user?id\=" + str(user_id) + ")",
                    parse_mode=ParseMode.mdv2.value
                )
                logging.info(name_user + " успешно добавлен")
                return config.AddUserMessage.extended

            case controllerFastApi.NetworkServiceError():
                _text: str = f"{result_add_vpn_user.caption}\nОтвет сервера:\n{result_add_vpn_user.response}"
                bot.send_message(admin_chat_id, _text)
                logging.error(_text)
                return config.AddUserMessage.error

    elif not user.action:
        renewalOfSubscription(user, intervalSql, serverNew=server)
        if int(user.server_id) == int(server):
            return config.AddUserMessage.extended
        else:
            return config.AddUserMessage.error

    elif user.action:
        if server != user.server_id:
            del_users({user_id}, user.server_id, no_update=True)
            add_user(user_id, month, server=server)
            return config.AddUserMessage.extended

        update_user_extend_subscription(user_id, intervalSql)
        return config.AddUserMessage.extended
    


def del_users(
    user_ids: set[int],
    server_id: int,
    no_update: bool = False,
    no_message: bool = False
) -> bool | NetworkServiceError:

    update_user_deactivate(user_ids, commit=not no_update)

    if not no_update and not no_message:
        for user_id in user_ids:
            try:
                bot.send_message(
                    user_id,
                    "Подписка окончена.",
                    reply_markup=keyboards.getInlineExtend()
                )
            except ApiTelegramException as e:
                conf = ConfigParser()
                conf.read('config.ini')
                bot.send_message(
                    conf['Telegram'].getint('admin_chat'),
                    str(e) + " id:" + str(user_id)
                )

    return controllerFastApi.del_users(
        user_ids,
        server_id
    )


def generate_alphanum_crypt_string():
    letters_and_digits = string.ascii_letters + string.digits
    crypt_rand_string = ''.join(secrets.choice(letters_and_digits) for i in range(16))
    return crypt_rand_string
    

def data_user(id: int, old_message: Message | None = None) -> Message:
    """
        Получить информацию о пользователе
    """
    if old_message:
        message: Message = bot.edit_message_reply_markup(
            old_message.chat.id,
            old_message.id,
            reply_markup=keyboards.get_inline_loading()
        )
    else:
        message: Message = bot.send_message(
            config.ADMINCHAT, 
            "Загрузка..."
        )

    user: User | None = get_user_by_id(int(id))

    if not user:
        return bot.edit_message_text(
            chat_id=message.chat.id,
            message_id= message.id,
            text= "Пользователь незарегистрирован"
        )
    
    keyboard: InlineKeyboardMarkup = UserList.addButtonKeyForUsersList(user)

    keyboard.add(
        InlineKeyboardButton(
            text = "Обнулить баланс",
            callback_data = utils.callBackBilder(
                CallbackKeys.resetToZeroBalance,
                userId = id
            )
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text=KeyCall.refreshtoken.value,
            callback_data=utils.callBackBilder(
                KeyCall.refreshtoken,
                user_id = id
            )
        )
    )
    
    return bot.edit_message_text_or_caption(
        message,
        paidCheckActive(user.paid) + utils.bool_in_circle_for_text(user.action) +
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
        parse_mode=ParseMode.mdv2,
        reply_markup=keyboard
    )  
    

def paidCheckActive(item: bool) -> str:
    if item:
        return "💵"
    return ""


def delete_not_subscription() -> None:

    conf = ConfigParser()
    conf.read('config.ini')
    admin_chat_id: int = conf['Telegram'].getint('admin_chat')

    data = get_inactive_users_by_server()

    for item in data:

            server_name: str = get_server_name_by_id(item.server_id)
            
            old_message: Message = bot.send_message(
                admin_chat_id, 
                f'Удаление неактивных пользователей с сервера {server_name}',
                disable_notification=True
            )

            controllerFastApi.del_users(set(item.user_ids), item.server_id)

            text: str = f'Удалены неактивные пользователи с сервера {server_name}'

            logging.info(text)

            bot.edit_message_text(
                text,
                old_message.chat.id,
                old_message.id
            )