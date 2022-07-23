import os
import time
import telegram
import telegram.ext
import requests
import logging

from http import HTTPStatus
from exceptions import TokensAreNotGiven, HomeworkStatusNotCorrect
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=('%(asctime)s, %(lineno)d, %(funcName)s,'
                '%(levelname)s, %(message)s')
    )

PRACTICUM_TOKEN = os.getenv('YA_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELE_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция для отправки сообщения ботом."""
    logging.debug(f'Попытка отправить сообщение: {message}')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        raise Exception(f'Сообщение "{message}" не отправлено из-за {error}')
    else:
        logging.info(f'Сообщение "{message}" отправлено')


def get_api_answer(current_timestamp):
    """Функция для запроса ресурса с API Практикума."""
    logging.debug('Поптыка запроса ресурса с API Практикума')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }
    try:
        response = requests.get(**request_params)
        if response.status_code != HTTPStatus.OK:
            raise Exception(
                f'Ответ от API отличный от "200" с параметрами'
                f'{request_params.values()}'
            )
    except Exception as error:
        raise Exception(f'Ошибка доступа к API: {error}')
    return response.json()


def check_response(response):
    """Функция для проверки формата ответа от API Практикума."""
    logging.debug('Проверка формата ответа от API')
    if not isinstance(response, dict):
        raise TypeError('Ошибка типа')
    if 'homeworks' not in response or 'current_date' not in response:
        logging.error('Ошибка доступа по ключу')
        raise KeyError('Отсутствует Один из ключей')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Ошибка типа')
    return homeworks


def parse_status(homework):
    """Определение статуса домашней работы."""
    if homework is {}:
        raise Exception('Домашних работ не найдено')
    logging.debug('Поптыка определения статуса домашней работы')
    keys = ['homework_name', 'status']
    for key in keys:
        if key not in homework.keys():
            logging.error(f'В ответе API не обнаружен ключ "{key}"')
            raise KeyError('Не обнаружены необходимые ключи в ответе API')
    homework_status = homework['status']
    try:
        verdict = HOMEWORK_VERDICTS[homework_status]
        homework_name = homework['homework_name']
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        raise HomeworkStatusNotCorrect(
            f'Недокументированный статус домашней работы({error})'
        )


def check_tokens() -> bool:
    """Функция для проверки доступности переменных окружения."""
    logging.debug('Проверка доступности переменных окружения')
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    logging.debug('Бот запущен')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_report = {}
    prev_err_message = ''
    if not check_tokens():
        logging.critical('Недоступны переменные окружения')
        raise TokensAreNotGiven
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks != prev_report:
                if len(homeworks) > 0:
                    for homework in homeworks:
                        message = parse_status(homework)
                        send_message(bot, message)
                    prev_report = homeworks.copy()
                current_timestamp = response.get('current_date')
            else:
                logging.debug('Нет новых статусов домашних работ')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != prev_err_message:
                logging.error(message)
                send_message(bot, message)
                prev_err_message = message
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
