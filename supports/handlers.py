import config, utils

from enums.content_types import ContentTypes
from enums.parse_mode import ParseMode

from telebot import types, TeleBot

from psycopg2.extras import DictCursor

from connect import db, engine

from sqlalchemy.orm import Session
from sqlalchemy import select

from giftUsers import checkGiftCode

from managment_user import UserList

from messageForUser import successfully_paid

from tables import User

from filters import only_user_chat, only_user_chat_and_text

from keyboards import KeyboardForUser, get_inline_keyboard_list_countries



def register_message_handlers(bot: TeleBot) -> None:
    
    @bot.message_handler(
        func= only_user_chat_and_text(),
        content_types=[ContentTypes.text.value],
        chat_types=['private']
    )
    def _(message: types.Message) -> bool | types.Message:

        with Session(engine) as session:
            query = select(User).filter(User.telegram_id == message.from_user.id)
            user: User | None = session.execute(query).scalar()
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

                    return bot.send_photo(
                        message.from_user.id,
                        photo = open(config.FILE_URL + "vpn_option.png", "rb"),
                        caption = utils.form_text_markdownv2(config.TextsMessages.select_country.value),
                        parse_mode=ParseMode.mdv2.value,
                        reply_markup = get_inline_keyboard_list_countries()
                    )

                case KeyboardForUser.refProgram.value:

                    return bot.send_message(
                        message.from_user.id,
                        "Вы можете пригласить нового пользователя и получить за это 1 мес\. подписки бесплатно\. Для того чтоб использовать такую возможность, отправьте вашу пригласительную ссылку другу\(для копирования достаточно нажать на ссылку\)\n\n"+
                        "Персональная ссылка:\n`https://t.me/open_vpn_sale_bot?start=" + str(message.from_user.id) + "`",
                        parse_mode= ParseMode.mdv2.value
                    )
                
                case _:

                    bot.send_message(
                        config.ADMINCHAT,
                        "[" + utils.form_text_markdownv2(str(message.from_user.full_name)) +
                        "](tg://user?id\=" + str(message.from_user.id) +
                        "):\n" +
                        utils.form_text_markdownv2(message.text) +
                        "\nid:" + str(message.from_user.id),
                        parse_mode=ParseMode.mdv2.value,
                        reply_markup=UserList.addButtonKeyForUsersList(str(message.from_user.id), user.action)
                    )
                    return bot.send_message(
                        chat_id=message.from_user.id, 
                        reply_to_message_id=message.id,
                        text="Отправлено администраторам. Ожидайте ответ..."
                    )
            


    @bot.message_handler(
        func= only_user_chat(),
        content_types=[ContentTypes.document.value],
        chat_types=['private']
    )
    def _(message: types.Message) -> None:
        
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
                        caption="server: " + utils.form_text_markdownv2(str(dataCur["server_desired"])) + "user: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ")\nid:" + str(message.from_user.id),
                        reply_markup=UserList.addButtonKeyForUsersList(str(message.from_user.id), dataCur["action"]),
                        parse_mode=ParseMode.mdv2.value)
            


    @bot.message_handler(
        func=only_user_chat(),
        content_types=[ContentTypes.photo.value],
        chat_types=['private']
    )
    def photo_chek(message: types.Message):

        bot.send_message(chat_id=message.from_user.id, reply_to_message_id=message.id,
                        text="Отправлено администраторам на проверку. Вы получите уведомление с результатом, ожидайте...")
        with db.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT action, server_desired FROM users_subscription WHERE telegram_id=" + str(message.from_user.id))
            dataCur = cursor.fetchone()
            try:
                bot.send_photo(config.ADMINCHAT, photo=message.photo[0].file_id,
                    caption="server: " + utils.form_text_markdownv2(str(dataCur["server_desired"])) +
                    "\nuser: [" + utils.form_text_markdownv2(message.from_user.full_name) + "](tg://user?id\=" + str(message.from_user.id) + ") \n\nid:" + str(message.from_user.id),
                    reply_markup=UserList.addButtonKeyForUsersList(str(message.from_user.id), dataCur["action"]),
                    parse_mode=ParseMode.mdv2.value)
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
        chat_types=['private']
    )
    def file_chek(message: types.Message):
        bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.id, text="Стикеры не поддреживаются в данном диалоге")