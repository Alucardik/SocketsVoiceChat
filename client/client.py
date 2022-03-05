import socket
import sys
import threading
from enum import Enum
from pyaudio import PyAudio
# from pyaudio_wrapper import pyaudio

import config
import protocol as pr


# a utility type for the client handler
class ActionType(Enum):
    RCV = 'receive'
    SEND = 'send'


class Client:
    def __init__(self, server_address, server_port):
        self._lock = threading.Lock()
        self._shutdown_flag = threading.Event()
        self._server_addr = server_address
        self._server_port = server_port
        self._voice_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._util_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._rcv_thread = None
        self._send_thread = None
        self._p = None
        self._playing_stream = None
        self._recording_stream = None
        self._clientInfo = pr.ClientInfo()

    def _abort(self, intentional: bool = False):
        with self._lock:
            self._shutdown_flag.set()

        if self._voice_channel:
            self._voice_channel.shutdown(socket.SHUT_RDWR)
        if self._util_channel:
            self._util_channel.shutdown(socket.SHUT_RDWR)
        if self._rcv_thread:
            self._rcv_thread.join()
        if self._send_thread:
            self._send_thread.join()
        if self._recording_stream:
            self._recording_stream.close()
        if self._playing_stream:
            self._playing_stream.close()
        if self._p:
            self._p.terminate()
        print('Client interrupted', file=sys.stdout if intentional else sys.stderr)
        exit(0) if intentional else exit(1)

    def _handle_voice_channel(self, mode: ActionType):
        stacked_exceptions = 0
        while not self._shutdown_flag.is_set():
            try:
                if mode == ActionType.RCV:
                    data = self._voice_channel.recv(config.CHUNK_SIZE)
                    self._playing_stream.write(data)
                elif mode == ActionType.SEND:
                    data = self._recording_stream.read(config.CHUNK_SIZE)
                    self._voice_channel.sendall(data)
                stacked_exceptions = 0
            except OSError as exc:
                print('OS Exception occurred in receive: ', exc, file=sys.stderr, flush=True)
                stacked_exceptions += 1
                # function is called in a separate thread, but aborting is reasonable from the main thread only
                if stacked_exceptions > config.EXCEPTION_LIM:
                    return
            except Exception as exc:
                print('Exception occurred in receive', exc, file=sys.stderr, flush=True)

    def _handle_util_channel(self):
        self._util_channel.sendall(pr.Message(pr.MessageType.CLIENT_CONNECT, self._clientInfo).toBytes())

        while True:
            try:
                buf = self._util_channel.recv(pr.MessageBufSize)
                print('GOT INFO', buf, flush=True)
                msg_type, info = pr.Message.fromBytes(buf)
                if msg_type == pr.MessageType.PEER_CONNECT:
                    print(info, flush=True)
            except KeyboardInterrupt:
                self._abort()

    def disconnect(self):
        self._abort(intentional=True)

    def connect(self):
        client_name = input('Enter a desired name:\t')
        self._clientInfo.setName(client_name)

        while True:
            try:
                self._util_channel.connect((self._server_addr, self._server_port))
                self._voice_channel.connect((self._server_addr, self._server_port))
                break
            except KeyboardInterrupt:
                self._abort()
            except Exception as exc:
                print("Couldn't connect to server", exc)

        # initialise microphone recording
        self._p = PyAudio()
        self._playing_stream = self._p.open(format=config.AUDIO_FORMAT,
                                            channels=config.CHANNELS_NUM,
                                            rate=config.SAMPLERATE,
                                            output=True,
                                            frames_per_buffer=config.CHUNK_SIZE)

        self._recording_stream = self._p.open(format=config.AUDIO_FORMAT,
                                              channels=config.CHANNELS_NUM,
                                              rate=config.SAMPLERATE,
                                              input=True,
                                              frames_per_buffer=config.CHUNK_SIZE)

        print('Connected to Server', flush=True)

        # initialise sender / receiver threads
        self._rcv_thread = threading.Thread(target=self._handle_voice_channel, args=(ActionType.RCV,))
        self._send_thread = threading.Thread(target=self._handle_voice_channel, args=(ActionType.SEND,))
        self._rcv_thread.start()
        self._send_thread.start()
        self._handle_util_channel()


def main():
    if len(sys.argv) == 1 or len(sys.argv) > 3:
        print('Usage: python3 client.py SERVER_ADDRESS [PORT]')
        return

    server_address = sys.argv[1]

    if len(sys.argv) == 3:
        server_port = int(sys.argv[2])
    else:
        server_port = config.PORT

    Client(server_address, server_port).connect()


if __name__ == '__main__':
    main()
