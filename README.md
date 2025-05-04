#  Бот для проверки статуса домашней работы
* **Описание**: Telegram-бот, который каждые 10 минут обращается к API сервиса Практикум Домашка и при обновлении статуса присылает оповещение в telegram.
* **Стек технологий**  
  Telegram Bot API, requests
* **Установка**  
Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:KatyaSoloveva/homework_bot.git
```  

```
cd homework_bot
```
Создать и активировать виртуальное окружение:
```
python -m venv venv
```

Для Windows
```
source venv/Scripts/activate
```

Для Linux
```
source venv/bin/activate
```
Загрузить зависимости
```
pip install -r requirements.txt
```
```
python -m pip install --upgrade pip
```
Создать файл .env:
```
touch .evn
```
И в нем разместить токен для доступа к API сервиса Practicum, токен для доступа к Telegram Bot API и идентификатор чата в Telegram.
Запустить проект:
```
python homework.py
```

* **Created by Ekaterina Soloveva**  
https://github.com/KatyaSoloveva
