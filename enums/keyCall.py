from enum import Enum

class KeyCall(Enum):
    
    pollCountMonth: str = "pollCountMonth"
    sale: str = "sale"
    tryServers: str = "tryServers"
    refreshtoken: str = "refreshtoken"
    create_cryptio_pay: str = "create_cryptio_pay"
    payment_stars: str = "payment_stars"
    list_servers_for_admin: str = "list_servers_for_admin"
    send_message_for_extension: str = "send_message_for_extension"
    loading: str = "loading"
    deaction: str = "deaction"
    data_user: str = "data_user"
    backmanual_settings: str = "backmanualSettings"