FROM python:3

WORKDIR /usr/local/sockets-voice-chat

COPY *.py  ./
COPY requirements.txt ./

RUN apt-get update \
    && apt-get install -y portaudio19-dev \
    && apt-get install -y python3-pyaudio \
    && pip install -r requirements.txt

CMD python3 client.py 172.17.0.2
