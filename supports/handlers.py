import config, utils

from enums.content_types import ContentTypes
from enums.parse_mode import ParseMode
from enums.chat_types import ChatTypes
from enums.keyCall import KeyCall

from telebot import types
from telebot.util import quick_markup

from giftUsers import checkGiftCode

from managment_user import UserList

from messageForUser import successfully_paid

from tables import User

from filters import only_user_chat, only_user_chat_and_text

from keyboards import KeyboardForUser

from users.methods import get_user_by_id

from core.telebot import TeleBotMod

from configparser import ConfigParser

from servers.methods import get_very_free_server



def register_message_handlers(bot: TeleBotMod) -> None:
    
    @bot.message_handler(
        func= only_user_chat_and_text(),
        content_types=[ContentTypes.text.value],
        chat_types=['private']
    )
    def _(message: types.Message) -> bool | types.Message:

        user: User = get_user_by_id(message.from_user.id)

        if checkGiftCode(message):
            return successfully_paid(message.from_user.id, optionText="Подарок активирован")

        match message.text:

            case KeyboardForUser.gift.value:

                return bot.send_message(
                    message.from_user.id,
                    "Вы можете пригласить нового пользователя и получить за это 1 мес\. подписки бесплатно\. Для того чтоб использовать такую возможность, отправьте вашу пригласительную ссылку другу\(для копирования достаточно нажать на ссылку\)\n\n Персональная ссылка:\n`https://t.me/open_vpn_sale_bot?start=" + 
                    str(message.from_user.id) + "`",
                    parse_mode = ParseMode.mdv2.value
                )
            
            case KeyboardForUser.buy.value:

                conf = ConfigParser()
                conf.read(config.FILE_URL + 'config.ini')

                server_id: int = get_very_free_server()

                keyboard = quick_markup(
                    {
                        '1 мес.| ' + conf['Price'].get('RUB') + " руб.": {'callback_data': '{"key": "' + KeyCall.get_link_payment.value + '", "server": ' + str(server_id) + ', "month": 1}'},
                        '3 мес.| ' + str(conf['Price'].getint('RUB') * 3) + " руб.": {'callback_data': '{"key": "' + KeyCall.get_link_payment.value + '", "server": ' + str(server_id) + ', "month": 3}'},
                        '6 мес.| ' + str(conf['Price'].getint('RUB') * 6) + " руб.": {'callback_data': '{"key": "' + KeyCall.get_link_payment.value + '", "server": ' + str(server_id) + ', "month": 6}'},
                        '12 мес.| ' + str(conf['Price'].getint('RUB') * 12) + " руб.": {'callback_data': '{"key": "' + KeyCall.get_link_payment.value + '", "server": ' + str(server_id) + ', "month": 12}'},
                        '◀️ назад': {'callback_data': '{"key": "' + KeyCall.backmanual_settings.value + '"}'}
                    },
                    row_width=2
                )
                bot.reply_to(message, "На какой срок?", reply_markup=keyboard)
            
            case _:

                bot.send_message(
                    config.ADMINCHAT,
                    "[" + utils.form_text_markdownv2(str(message.from_user.full_name)) +
                    "](tg://user?id\=" + str(message.from_user.id) +
                    "):\n" +
                    utils.form_text_markdownv2(message.text) +
                    "\nid:" + str(message.from_user.id),
                    parse_mode=ParseMode.mdv2.value,
                    reply_markup=UserList.addButtonKeyForUsersList(user)
                )
                return bot.send_message(
                    chat_id=message.from_user.id, 
                    reply_to_message_id=message.id,
                    text="Отправлено администраторам. Ожидайте ответ..."
                )
            


    @bot.message_handler(
        func= only_user_chat(),
        content_types=[ContentTypes.document.value],
        chat_types=[ChatTypes.private.value]
    )
    def _(message: types.Message) -> None:

        user: User = get_user_by_id(message.from_user.id)

        bot.reply_to(
            message,
            "Отправлено администраторам на проверку. Вы получите уведомление с результатом, ожидайте..."
        )
        
        bot.send_document(
            config.ADMINCHAT, 
            document=message.document.file_id,
            caption="server: " + utils.form_text_markdownv2(str(user.server_desired)) + "user: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ")\nid:" + str(message.from_user.id),
            reply_markup=UserList.addButtonKeyForUsersList(user),
            parse_mode=ParseMode.mdv2.value
        )
        


    @bot.message_handler(
        func=only_user_chat(),
        content_types=[ContentTypes.photo.value],
        chat_types=[ChatTypes.private.value]
    )
    def photo_chek(message: types.Message):
        
        user: User = get_user_by_id(message.from_user.id)

        bot.reply_to(
            message,
            "Отправлено администраторам на проверку. Вы получите уведомление с результатом, ожидайте..."
        )

        try:
            bot.send_photo(
                config.ADMINCHAT, 
                photo=message.photo[0].file_id,
                caption="server: " + utils.form_text_markdownv2(str(user.server_desired)) +
                "\nuser: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ") \n\nid:" + str(message.from_user.id),
                reply_markup=UserList.addButtonKeyForUsersList(user),
                parse_mode=ParseMode.mdv2.value
            )
        except Exception as e:
            bot.send_photo(
                config.ADMINCHAT,
                photo=message.photo[0].file_id,
                caption="\nuser: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ")\nid:" + str(message.from_user.id),
                parse_mode=ParseMode.mdv2.value
            )

            

    @bot.message_handler(
        func=only_user_chat(),
        content_types=[ContentTypes.sticker.value],
        chat_types=[ChatTypes.private.value]
    )
    def file_chek(message: types.Message):
        bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.id, text="Стикеры не поддреживаются в данном диалоге")


    @bot.message_handler(
        func= lambda message: message.chat.id == config.ADMINCHAT and
        message.reply_to_message and message.text[0] != "/"
    )
    def _(message: types.Message) -> None:

        if message.reply_to_message.text:
            user_id: str | int = str(message.reply_to_message.text).split('id:', -1)[1]
        else:
            user_id: str | int = str(message.reply_to_message.caption).split('id:', -1)[1]
        
        try:
            bot.copy_message(chat_id=user_id, from_chat_id=config.ADMINCHAT, message_id=message.id)
        except Exception as e:
            bot.send_message(
                config.ADMINCHAT,
                reply_to_message_id=message.id,
                text='```error\n' + utils.form_text_markdownv2(str(e)) + '\n```',
                parse_mode=ParseMode.mdv2.value
            )