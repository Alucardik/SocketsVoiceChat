# Чекин Игорь, Сервис-ориентированные архитектуры, Домашнее задание 3

## Общая структура проекта
В папке `server` находятся файлы сервера, в папке `client` - клиента. На сервере реализована инфраструктура для поддержания множественных соединений, однако
не выполнены все требования соответствующего пункта, поэтому сервер лучше использовать в качестве эхо-сервера. Для запуска сервера необходимо ввести команду `python3 server.py` в папке сервера,
либо запустить через [докер-образ](https://hub.docker.com/layers/195762484/alucardik/soa-images/sockets-voice-chat_server/images/sha256-87355ad9da0730a17c2986d57b3396d9c3dc0a03ebf4d8b652c31dda24115c5c?context=repo).

Клиент запускается из папки `client` командой `python3 client.py your-server-address`, где `your-server-address` - ip-адрес вашего сервера. После этого клиент попросит указать имя и, при
успешном подключении, будет транслировать звук.
