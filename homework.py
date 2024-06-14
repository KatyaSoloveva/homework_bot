import logging
import os
import time
from http import HTTPStatus

import requests
from telebot import TeleBot
from dotenv import load_dotenv

from exceptions import ResponseCodeError

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
file_handler = logging.FileHandler(__file__ + '.log', mode='a',
                                   encoding='utf-8')
logger.addHandler(file_handler)
formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s,'
                              '%(funcName)s, %(lineno)d')
handler.setFormatter(formatter)
file_handler.setFormatter(formatter)


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens = (
        ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
        ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
        ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID),
    )
    boolean_variable = True
    for name, token in tokens:
        if not token:
            logger.critical('Отсутствует обязательная переменная '
                            f'окружения {name}.')
            boolean_variable = False
    if not boolean_variable:
        raise ValueError('Программа принудительно остановлена.')


def send_message(bot, message):
    """Отправка сообщений в Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения: {error}')
        return False
    logger.debug(f'Отправлено сообщение: {message}')
    return True


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    params = {'from_date': timestamp}
    requests_dict = {'url': ENDPOINT,
                     'headers': HEADERS,
                     'params': params}
    message = ('к эндпоинту {url} c заголовками {headers} и '
               'парметрами {params}'.format(**requests_dict))
    logger.debug('Отправлен запрос ' + message)
    try:
        response = requests.get(**requests_dict)
    except requests.exceptions.RequestException:
        raise ConnectionError('Сбой при доступе ' + message)
    if response.status_code != HTTPStatus.OK:
        raise ResponseCodeError(f'Эндпоинт недоступен: {response.status_code},'
                                f'{response.reason}, {response.text}')
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Response не словарь.')
    if 'homeworks' not in response:
        raise KeyError('Ключ homeworks отсутствует в словаре.')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Homeworks не список.')
    return homeworks


def parse_status(homework):
    """Извлечение статуса из информации о дом.работе."""
    try:
        homework_status = homework['status']
        homework_name = homework['homework_name']
    except KeyError as error:
        raise KeyError(f'Ключ {error} не найден в словаре.')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError('Неожиданный статус домашней работы.')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_var = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logger.debug('Домашних заданий нет.')
                continue
            status_message = parse_status(homeworks[0])
            if (status_message != previous_var
                    and send_message(bot, status_message)):
                previous_var = status_message
                timestamp = response.get('current_date', timestamp)
            else:
                logger.debug('В ответе отсутствуют новые статусы.')
        except Exception as error:
            current_error = f'Сбой в работе программы: {error}'
            logger.error(current_error)
            if (current_error != previous_var
                    and send_message(bot, current_error)):
                previous_var = current_error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
