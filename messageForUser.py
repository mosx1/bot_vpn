import config

from connect import bot
from telebot import types
from telebot.util import quick_markup



def periodSubscription(call: types.CallbackQuery, call_data: dict):
    
    keyboard = quick_markup(
                {
                    '1 мес.| ' + str(config.PRICE) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 1}'},
                    '3 мес.| ' + str(config.PRICE * 3) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 3}'},
                    '6 мес.| ' + str(config.PRICE * 6) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 6}'},
                    '12 мес.| ' + str(config.PRICE * 12) + " руб.": {'callback_data': '{"key": "getLinkPayment", "server": ' + str(call_data['server']) + ', "month": 12}'},
                    '<<< назад': {'callback_data': '{"key": "sale", "back": 1}'}
                },
                row_width=2
            )
    bot.edit_message_caption("На какой срок?", call.message.chat.id, call.message.id, reply_markup=keyboard)