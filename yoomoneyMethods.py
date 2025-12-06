import config, logging

from connect import token, bot

from yoomoney import History, Quickpay, Client

from configparser import ConfigParser

from requests.exceptions import ReadTimeout


test = "https://api.telegram.org/bot" + token + "/getMe"



def getInfoLastPayment(label: str) -> dict:
    """
        Получает информацию о последнем платеже по идентификатору платежа
    """

    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')

    client = Client(conf['Umani'].get('token'))

    history: History = client.operation_history(label=label)

    for operation in history.operations:

        return {
            "status": operation.status,
            "message": "{}\nstatus: {}\ndatetime: {}\nсумма: {}".format(
                operation.title,
                operation.status,
                operation.datetime,
                operation.amount
            )
        }
        
        # print("Operation:",operation.operation_id)
        # print("\tStatus     -->", operation.status)
        # print("\tDatetime   -->", operation.datetime)
        # print("\tTitle      -->", operation.title)
        # print("\tAmount     -->", operation.amount)


def getLinkPayment(label: str, month: int) -> str:
    """
        Создает ссылку на платеж
    """
    conf = ConfigParser()
    conf.read(config.FILE_URL + 'config.ini')

    quickpay = Quickpay(
        receiver=config.WALLET_YOOMONEY_ID,
        quickpay_form="shop",
        targets="Оплата VPN",
        paymentType="SB",
        sum=conf['Price'].getint('RUB') * month,
        label=label
    )

    return quickpay.redirected_url

    # print(quickpay.base_url)
    # print(quickpay.redirected_url)


# Authorize(
#       client_id="A355809DAE7D025330CF1723EAEE3091D70F79815688CAE45EB97471C8CAFB3C",
#       # client_secret="A355809DAE7D025330CF1723EAEE3091D70F79815688CAE45EB97471C8CAFB3C",
#       redirect_uri="https://t.me/open_vpn_sale_bot",
#       scope=["account-info",
#              "operation-history",
#              "operation-details",
#              "incoming-transfers",
#              "payment-p2p"
#              ]
#       )