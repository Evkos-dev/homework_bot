import os
import sys
import time
import telegram
import telegram.ext
import requests
import logging

from http import HTTPStatus
from exceptions import TokensAreNotGiven, HomeworkStatusNotCorrect
from dotenv import load_dotenv

load_dotenv()

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)

logger.addHandler(handler)
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('YA_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELE_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция для отправки сообщения ботом."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение "{message}" отправлено')
    except Exception as error:
        logger.error(f'Сообщение "{message}" не отправлено из-за {error}')


def get_api_answer(current_timestamp):
    """Функция для запроса ресурса с API Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logger.error(f'Ошибка доступа к API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise Exception('Нет ответа от API')
    return response.json()


def check_response(response):
    """Функция для проверки формата ответа от API Практикума."""
    if not isinstance(response, dict):
        raise TypeError('Ошибка типа')
    if 'homeworks' not in response or 'current_date' not in response:
        logger.error('Ошибка доступа по ключу')
        raise KeyError('Отсутствует Один из ключей')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Ошибка типа')
    return homeworks


def parse_status(homework):
    """Определение статуса домашней работы."""
    keys = ['homework_name', 'status']
    for key in keys:
        if key not in homework.keys():
            logger.error(f'В ответе API не обнаружен ключ "{key}"')
            raise KeyError('Не обнаружены необходимые ключи в ответе API')
    homework_status = homework['status']
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
        homework_name = homework['homework_name']
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        logger.error(f'Недокументированный статус домашней работы({error})')
        raise HomeworkStatusNotCorrect


def check_tokens() -> bool:
    """Функция для проверки доступности переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    check_tokens()
    if not check_tokens():
        logger.critical('Недоступны переменные окружения')
        raise TokensAreNotGiven
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)
                current_timestamp = response.get('current_date')
            else:
                bot.send_message(TELEGRAM_CHAT_ID, 'Нет домашних работ')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
