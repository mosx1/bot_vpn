import requests
import json
import time
import pytz
import invite

from configparser import ConfigParser

from datetime import datetime, timedelta

from enum import Enum

from config import AddUserMessage, ADMINCHAT, TextsMessages
from connect import logging, engine, bot

from sqlalchemy.orm import Session
from sqlalchemy import select

from database import User

from servers.server_list import Servers
from enums.parse_mode import ParseMode

from dataclasses import dataclass

from managment_user import add_user

from utils import form_text_markdownv2

from messageForUser import successfully_paid

from threading import Thread

from typing import Any

from giftUsers import genGiftCode

from utils import get_server_name_by_id


class InvoiceStatuses(Enum):
    active: str = "active"
    paid: str = "paid"


class TypeOfPurchase(Enum):
    yourself: str = "yourself"
    gift: str = "gift"


@dataclass(frozen=True)
class PayingUser:
    telegram_id: int
    count_month: int
    server: Servers
    message_id: int
    type: TypeOfPurchase


@dataclass(frozen=True)
class Invoice:
    invoice_id: int
    hash: str
    currency_type: str
    asset: str
    amount: int
    pay_url: str
    bot_invoice_url: str
    mini_app_invoice_url: str
    web_app_invoice_url: str
    status: InvoiceStatuses
    created_at: str
    allow_comments: bool
    allow_anonymous: bool


class CryptoPay:

    _instance = None

    def __init__(self):
        self.ids: dict[PayingUser] = {}

        configInit = ConfigParser()
        configInit.read('config.ini')
        config = configInit['CryptoPay']

        self.token: str = config.get('token')
        self.host: str = config.get('host')
        self.url: str = config.get('url')

        t = Thread(target=self.polling_info_last_payment_cripto)
        t.start()


    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance


    def _get_headers(self, data_json: str) -> dict[str, Any]:

        content_length = str(len(data_json.encode('utf-8')))
        return {
            "Crypto-Pay-API-Token": self.token,
            "Host": self.host,
            "Content-Length": content_length,
            "Content-Type": "application/json"
        }


    def create_invoice(self, month: float) -> dict | None:
        
        data = {
            "amount": month,
            "asset": "USDT"
        }
        data_json: str = json.dumps(data)
        response = requests.post(
            self.url + "createInvoice",
            data=data_json,
            headers=self._get_headers(data_json)
        )
        response_json: dict = response.json()

        if response_json.get('ok', None):
            return response_json.get('result')
            

    def get_invoices(self) -> list:

        data = {
            "invoice_ids": [item for item in self.ids.keys()]
        }
        data_json: str = json.dumps(data)
        response = requests.post(
            self.url + "getInvoices",
            data=data_json,
            headers=self._get_headers(data_json)
        )
        response_json: dict = response.json()

        if response_json.get('ok', None):
            return response_json['result']['items']
        

    def delete_invoice(self, id: int) -> bool:
        
        data = {
            "invoice_id": id
        }
        data_json: str = json.dumps(data)
        response = requests.post(
            self.url + "getInvoices",
            data=data_json,
            headers=self._get_headers(data_json)
        )
        response_json: dict = response.json()

        return response_json.get('ok')


    def polling_info_last_payment_cripto(self) -> None:

        while True:
            if len(self.ids) == 0:
                continue

            stop_datetime: datetime = datetime.now(pytz.timezone('Europe/Moscow')) - timedelta(hours=1)
            invoices: list = self.get_invoices()

            for invoice in invoices:
                
                if invoice['status'] == InvoiceStatuses.paid:

                    paying_user: PayingUser = self.ids[invoice['invoice_id']]

                    with Session(engine) as session:
                        
                        user = select(User).filter(User.telegram_id == paying_user.telegram_id)
                        user: User | None = session.scalar(user)
                        
                        if not user:
                            continue
                        match paying_user.type:
                            case TypeOfPurchase.yourself:

                                logging.info(
                                    f"user_id: {user.telegram_id}; user_name:{user.name}; Оплата подписки {paying_user.count_month} мес. сервер {get_server_name_by_id(paying_user.server)}"
                                )

                                bot.edit_message_caption(
                                    "Оплата получена, идет настройка конфигурации(это может занять несколько минут)...", 
                                    user.telegram_id, 
                                    paying_user.message_id
                                )
                                
                                userMessage: AddUserMessage  = add_user(user.telegram_id, paying_user.count_month, server=paying_user.server)

                                bot.send_message(
                                    ADMINCHAT,
                                    "[" + form_text_markdownv2(user.name) + "](tg://user?id\=" + str(user.telegram_id) + ") оплатил криптой",
                                    parse_mode=ParseMode.mdv2.value
                                )
                                bot.delete_message(user.telegram_id, paying_user.message_id)
                                
                                invite.methods.incrementBalance(user.telegram_id, month=paying_user.count_month)
                                
                                successfully_paid(user.telegram_id, optionText=userMessage.value)

                            case TypeOfPurchase.gift:
                                logging.info(
                                    f"user_id: {user.telegram_id}; user_name:{user.name}; Оплата подарочной подписки {paying_user.count_month} мес."
                                )

                                hash = genGiftCode(paying_user.count_month)

                                bot.send_message(
                                    ADMINCHAT,
                                    f"[{form_text_markdownv2(user.name)}](tg://user?id\={user.telegram_id}) оплатил подарочную подписку",
                                    parse_mode=ParseMode.mdv2.value
                                )
                                bot.delete_message(user.telegram_id, paying_user.message_id)

                                photoMessage = bot.send_photo(
                                    chat_id=user.telegram_id,
                                    photo=open("image/gift.png", "rb"),
                                    caption=TextsMessages.giftPostcard.format(code=hash, date=paying_user.count_month),
                                    parse_mode=ParseMode.mdv2.value
                                )
                                bot.reply_to(photoMessage, "Перешлите это сообщение другу в качестве подарка. Спасибо что помогаете нам делать интернет доступнее.")

                        del self.ids[invoice['invoice_id']]
                        
                if datetime.fromisoformat(invoice['created_at']) < stop_datetime:
                    if self.delete_invoice(invoice['invoice_id']):
                        del self.ids[invoice['invoice_id']]


            time.sleep(2)


crypto_pay = CryptoPay()