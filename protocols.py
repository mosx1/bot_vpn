from enum import Enum

class Protocol (Enum):

    outline = 1
    xray = 2


def getNameProtocolById(protocolValue: int) -> str:
    for i in Protocol:
        if i.value == protocolValue:
            return i.name