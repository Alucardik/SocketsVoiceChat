import socket
import sys
import typing as t
from enum import Enum
from threading import Thread

import config
import protocol as pr


# a utility type for the client handler
class ChannelType(Enum):
    UTIL = 'util'
    VOICE = 'voice'


# a pair of socket and an associated thread, responsible for its handling
ChannelInfo = t.Tuple[socket.socket, Thread]
# a pair of voice and util channels
ChannelPair = t.Tuple[ChannelInfo, ChannelInfo]
InfoType = t.Literal['clientInfo', 'channelsInfo']
ConnectionInfo = t.Dict[InfoType, t.Union[ChannelPair, pr.ClientInfo]]


class Server:
    def __init__(self, port: int):
        self._address: str = socket.gethostbyname(socket.gethostname())
        self._port: int = port
        self._listener: t.Optional[socket.socket] = None
        # id for connections
        self._conn_cnt = 0
        # id: ConnectionInfo
        self._connections: t.Dict[int, ConnectionInfo] = {}
        self._voice_connections = []
        self._util_connections = []

        while True:
            try:
                self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                self._listener.bind((self._address, self._port))
                break
            except KeyboardInterrupt:
                self._abort()
            except Exception as exc:
                print(f"Couldn't bind to port: {self._port}\n", exc, file=sys.stderr)

    def _abort(self):
        for client, cur_thread in self._voice_connections:
            client.close()
            cur_thread.join()

        if self._listener:
            self._listener.close()

        print('Server interrupted', file=sys.stderr)
        exit(1)

    def _broadcast(self, ch_type: ChannelType, cur_channel, data):
        channels = [entry['channelsInfo'][0][0] if ch_type == ChannelType.VOICE else entry['channelsInfo'][1][0]
                    for entry in self._connections.values()]
        for channel in channels:
            # if channel != cur_channel:
            try:
                channel.send(data)
            except Exception as exc:
                print('Exception occurred: ', exc, file=sys.stderr)

    def _handle_client_util(self, conn_id: int, util_channel: socket.socket):
        while True:
            try:
                buf = util_channel.recv(pr.MessageBufSize)
                print('GOT MSG util', buf, flush=True)
                msg_type, info = pr.Message.fromBytes(buf)
                print('DESERIALISED', msg_type, info, flush=True)
                if msg_type == pr.MessageType.CLIENT_CONNECT:
                    self._connections[conn_id]['clientInfo'] = info
                    self._broadcast(ChannelType.UTIL,
                                    util_channel,
                                    pr.Message(pr.MessageType.PEER_CONNECT, info).toBytes())
            except OSError:
                util_channel.close()
                break

    def _handle_client_voice(self, voice_channel: socket.socket):
        while True:
            try:
                data = voice_channel.recv(config.CHUNK_SIZE)
                self._broadcast(ChannelType.VOICE, voice_channel, data)
            except OSError:
                voice_channel.close()
                break

    def _accept_connections(self):
        self._listener.listen(config.QUEUE_LIMIT)
        print(f'Running on address: {self._address}:{self._port}', flush=True)

        while True:
            try:
                util_channel, addr = self._listener.accept()
                voice_channel, _ = self._listener.accept()
                if voice_channel != self._listener and util_channel != self._listener:
                    print(f'Client {addr} connected', flush=True)
                    voice_thread = Thread(target=self._handle_client_voice, args=(voice_channel,))
                    util_thread = Thread(target=self._handle_client_util, args=(self._conn_cnt, util_channel,))
                    self._connections[self._conn_cnt] = {
                        'channelsInfo': ((voice_channel, voice_thread), (util_channel, util_thread))
                    }
                    self._conn_cnt += 1
                    voice_thread.start()
                    util_thread.start()
            except KeyboardInterrupt:
                self._abort()

    def serve(self):
        self._accept_connections()


def main():
    if len(sys.argv) > 2:
        print('Usage: python3 server.py [PORT]')
        return

    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = config.PORT

    Server(port).serve()


if __name__ == '__main__':
    main()
