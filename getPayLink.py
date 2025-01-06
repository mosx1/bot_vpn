from connect import bot
from telebot import types, TeleBot

def startPayment(userID, price) -> None:
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Оплатить звёздами(beta)", pay=True))
    prices = [types.LabeledPrice(label="XTR", amount=price)]
    bot.send_invoice(userID, title="Оплата подписки",  
        description="Оплата звездами поддерживается в тестовом режиме. Звездами в 2 раза дешевле:",  
        prices=prices,  
        provider_token="",  
        invoice_payload="sups",  
        currency="XTR",  
        reply_markup=keyboard)
    
