# Telegram homework bot
### Описание
Данный телеграм бот предназначет для проверки статуса домашней работы во время обучения в Яндекс.Практикуме.

Бот свзявается с API Практикума, выясняет статус домашней работы и, если он изменился в сравнение с предыдущим запросом, отправляет сообщение с результатом в чат.

### Технологии
- Python 3.7
- python-telegram-bot 13.7

### Заполнение .env файла
```
YA_TOKEN="Токен от API Практикума"
TELE_TOKEN="Токен от API Телеграм бота"
CHAT="ID чата"
```
### Установка
Клонировать репозиторий и перейти в него в командной строке:

`git clone https://github.com/homework_bot.git`

`cd homework_bot`

Cоздать и активировать виртуальное окружение:

`python3 -m venv venv`

`source venv/Scripts/activate`

Установить зависимости из файла requirements.txt:

`python -m pip install --upgrade pip`

`pip install -r requirements.txt`

