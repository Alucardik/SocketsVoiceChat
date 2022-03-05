import typing as t
from dataclasses import dataclass
from enum import Enum


# uint8 type
class MessageType(Enum):
    CLIENT_CONNECT = 1
    CLIENT_INFO = 2
    CLIENT_DISCONNECT = 3
    PEER_CONNECT = 4
    PEER_DISCONNECT = 5


@dataclass
class ClientInfo:
    name: str = ''

    def setName(self, name: str):
        self.name = name

    def toBytes(self) -> bytes:
        return self.name.encode()

    @staticmethod
    def fromBytes(payload: bytes) -> 'ClientInfo':
        return ClientInfo(payload.decode())


@dataclass
class Message:
    type: MessageType
    payload: t.Union[ClientInfo, bytes]

    def toBytes(self) -> bytes:
        if self.type == MessageType.CLIENT_CONNECT:
            return self.type.value.to_bytes(1, byteorder='little') + self.payload.toBytes()
        elif self.type == MessageType.PEER_CONNECT:
            # sending only the name of the connected user to the peers
            return (self.type.value.to_bytes(1, byteorder='little') +
                    b'User' + self.payload.name.encode() + b' has connected')

    @staticmethod
    def fromBytes(msg: bytes) -> t.Tuple[MessageType, t.Optional[ClientInfo]]:
        msg_type = MessageType(int.from_bytes(msg[0:1], byteorder='little', signed=False))
        res = None
        if msg_type == MessageType.CLIENT_CONNECT:
            res = ClientInfo.fromBytes(msg[1:])
        elif msg_type == MessageType.PEER_CONNECT:
            res = msg[1:].decode()

        return msg_type, res


MessageBufSize = 512
