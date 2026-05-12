import config, utils, keyboards

from enums.content_types import ContentTypes
from enums.parse_mode import ParseMode
from enums.chat_types import ChatTypes

from telebot import types

from tables import User

from filters import only_user_chat, only_user_chat_and_text, only_admin_chat_reply

from keyboards import get_inline_web_page

from users.methods import get_user_by_id, get_jwt_by_id

from core.telebot import TeleBotMod

from configparser import ConfigParser



def register_message_handlers(bot: TeleBotMod) -> None:
    
    @bot.message_handler(
        func= only_user_chat_and_text(),
        content_types=[ContentTypes.text.value],
        chat_types=['private']
    )
    def _(message: types.Message) -> bool | types.Message:

        conf = ConfigParser()
        conf.read('config.ini')
        user: User = get_user_by_id(message.from_user.id)

        if message.text.lower().find('не работает') != -1:
            bot.reply_to(
                message,
                "Поробуйте сменить сервер или протокол в личном кабинете."
            )
        bot.send_message(
            config.ADMINCHAT,
            "[" + utils.form_text_markdownv2(str(message.from_user.full_name)) +
            "](tg://user?id\=" + str(message.from_user.id) +
            "):\n" +
            utils.form_text_markdownv2(message.text) +
            "\nid:" + str(message.from_user.id),
            parse_mode=ParseMode.mdv2.value,
            reply_markup=keyboards.get_inline_for_users_list(user)
        )
        return bot.reply_to(
            message,
            conf['MessagesText'].get('reply_to_message'),
            reply_markup=get_inline_web_page(
                get_jwt_by_id(
                    user.telegram_id
                )
            )
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
            caption="server: " + utils.form_text_markdownv2(str(user.server_desired)) + 
            f"\nСообщение от пользователя: {utils.form_text_markdownv2(message.caption)}" +
            "user: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ")\nid:" + str(message.from_user.id),
            reply_markup=keyboards.get_inline_for_users_list(user),
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
                f"\nСообщение от пользователя: {utils.form_text_markdownv2(message.caption)}" +
                "\nuser: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ") \n\nid:" + str(message.from_user.id),
                reply_markup=keyboards.get_inline_for_users_list(user),
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
        func=only_admin_chat_reply(),
        content_types=[
            ContentTypes.text.value,
            ContentTypes.photo.value,
            ContentTypes.video.value,
            ContentTypes.document.value,
            ContentTypes.sticker.value
        ]
    )
    def _(message: types.Message) -> None:
        
        if message.reply_to_message.content_type == "text":
            user_id: str | int = str(message.reply_to_message.text).split('id:', -1)[1].strip()
        else:
            user_id: str | int = str(message.reply_to_message.caption).split('id:', -1)[1].strip()
        
        try:
            bot.copy_message(
                chat_id=user_id, 
                from_chat_id=config.ADMINCHAT, 
                message_id=message.id
            )
        except Exception as e:
            bot.send_message(
                config.ADMINCHAT,
                reply_to_message_id=message.id,
                text='```error\n' + utils.form_text_markdownv2(str(e)) + '\n```',
                parse_mode=ParseMode.mdv2.value
            )