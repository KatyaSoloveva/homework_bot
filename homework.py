import logging
import os
import time
from http import HTTPStatus

import requests
from telebot import TeleBot
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s')
handler.setFormatter(formatter)


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправка сообщений в Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Отправлено сообщение: {message}')
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise requests.exceptions.HTTPError('Эндпоинт недоступен.')
    except requests.exceptions.RequestException as error:
        message = f'Сбой при доступе к эндпоинту: {error}'
        logger.error(message)
        raise ConnectionError(message)
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        message = 'Response не словарь.'
        logger.error(message)
        raise TypeError(message)
    if 'homeworks' not in response:
        message = 'Ключ homeworks отсутствует в словаре.'
        logger.error(message)
        raise KeyError(message)
    if 'current_date' not in response:
        message = 'Ключ current_date отсутствует в словаре.'
        logger.error(message)
        raise KeyError(message)
    if not isinstance(response.get('homeworks'), list):
        message = 'Homeworks не список.'
        logger.error(message)
        raise TypeError(message)
    return response.get('homeworks')[0]


def parse_status(homework):
    """Извлечение статуса из информации о дом.работе."""
    try:
        homework_status = homework['status']
        homework_name = homework['homework_name']
    except KeyError as error:
        message = f'Ключ {error} не найден в словаре.'
        logger.error(message)
        raise KeyError(message)
    try:
        verdict = HOMEWORK_VERDICTS[homework_status]
    except KeyError as error:
        message = f'Неожиданный статус домашней работы {error}'
        logger.error(message)
        raise KeyError(message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствуют обязательные переменные окружения.')
        raise Exception('Программа принудительно остановлена.')

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_homework = ''
    previous_error = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework != previous_homework:
                status_message = parse_status(homework)
                send_message(bot, status_message)
                previous_homework = homework
            else:
                logger.debug('В ответе отсутствуют новые статусы.')
        except Exception as error:
            if str(error) != previous_error:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
                previous_error = str(error)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
