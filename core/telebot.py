from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup

from enums.content_types import ContentTypes
from enums.parse_mode import ParseMode


class TeleBotMod(TeleBot):

    def edit_message_text_or_caption(
            self,
            message: Message,
            text_or_caption: str,
            parse_mode: ParseMode | None = None,
            reply_markup: InlineKeyboardMarkup | None = None
    ) -> Message | bool:
        """
            Редактирует текст сообщения
        """
        if parse_mode:
            parse_mode = parse_mode.value
            
        if message.content_type == ContentTypes.text.value:

            return self.edit_message_text(
                text_or_caption,
                message.chat.id,
                message.id,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        
        return self.edit_message_caption(
            text_or_caption,
            message.chat.id,
            message.id,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
    
@property
def text_or_caption(self) -> str:
    if self.content_type == ContentTypes.text.value:
        return self.text
    return self.caption


Message.text_or_caption = text_or_caption