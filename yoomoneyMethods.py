import config

from connect import token

from yoomoney import Quickpay, Client, Authorize



test = "https://api.telegram.org/bot" + token + "/getMe"



def getInfoLastPayment(label: str) -> dict:
    """
    Получает информацию о последнем платеже по идентификатору платежа
    """
    client = Client(config.TOKEN_YOOMONEY)
    history = client.operation_history(label=label)
    
    for operation in history.operations:

        return {
            "status": operation.status,
            "message": "{}\nstatus: {}\ndatetime: {}\nсумма: {}".format(operation.title,
                                                                        operation.status,
                                                                        operation.datetime,
                                                                        operation.amount)
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
    quickpay = Quickpay(
                receiver=config.WALLET_YOOMONEY_ID,
                quickpay_form="shop",
                targets="Оплата VPN",
                paymentType="SB",
                sum=config.PRICE * month,
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