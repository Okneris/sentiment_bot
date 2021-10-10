# Импорт библиотек
import fasttext
import re
import logging
import json
from dostoevsky.tokenization import RegexTokenizer
from dostoevsky.models import FastTextSocialNetworkModel
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    CallbackContext
from datetime import timedelta
fasttext.FastText.eprint = lambda x: None


# Загрузка модели Dostoevsky для анализа настроений текста
tokenizer = RegexTokenizer()
model = FastTextSocialNetworkModel(tokenizer=tokenizer)


# Функции
def check_symbol(text):
    """ Функция для опрелеления языка текста. Бот работает с русскими фразами

    Переменные:
    ----------

    text: str, фраза переданная пользователем
    count: int, количество символов отличных от кирилицы

    Результат:
    ---------
    'en': str, если в фразе больше 80% сиволом английского алфавита
    'rus': str, если в фразе на русском
    """

    count = 0
    for i in text:
        if re.match(r'[a-zA-Z]+$', i):
            count += 1
    if count > 0.8 * len(text):
        return 'en'
    else:
        return 'rus'


def bot_answer(message):
    """ Функция для опрелеления анализа настроений текста

    Переменные:
    ----------

    message: str, фраза передаваемая пользователем
    result: dict, результат модели с вероятностью отнесения к каждому классу
    key: str, наиболее вероятный класс: negative, positive ...

    Результат:
    ---------
    positive, negative, neutral: str, текст сообщения пользователю
                                1. На позитивную тональность отвечает:
                                    "Спасибо за хорошую обратную связь!"
                                2. На нейтральную:
                                    "Ваше обращение принято. Всего доброго!"
                                3. На негативную:
                                    ""Ваше обращение приянто.
                                    Просим извинения за неудобства!
                                    Мы работаем над улучшением нашего сервиса."

    Пример:
    ------
    >> bot_answer('Настроение поднялось:)).Крутой фильм')
    >> Спасибо за хорошую обратную связь!
    """

    positive = "Спасибо за хорошую обратную связь!"
    negative = "Ваше обращение приянто. Просим извинения за неудобства! \
Мы работаем над улучшением нашего сервиса."
    neutral = "Ваше обращение принято. Всего доброго!"

    lis = list()
    lis.append(message)
    result = model.predict(lis, k=1)[0]
    key = list(result.keys())[0] # получение результата модели: negative...

    if key == 'negative':
        return negative
    elif key == 'neutral' or key == 'speech' or key == 'skip':
        return neutral
    else:
        return positive


def write_json(date, user_id, username, message, answer):
    """ Функция для записи полученных сообщений от пользователя, ответов бота в
    файл json формата

    Переменные:
    ----------

    date: datetime, дата отправки сообщения
    user_id: int, уникальный номер пользователя
    username: str, имя пользователя
    message: str, сообщение пользователя
    answer: str, ответ бота
    dict_m: dict, объект словарь для записи информации по пользователю
    data_m: list, список содержащий в себе словарь dict_m с данными

    Результат:
    ---------
    data.json: json, файл с даными

    Пример:
    ------
    >> write_json('2021-10-10 00:00:00+00:00', '268083166', 'sirenkovv',
        'Настроение поднялось:)).Крутой фильм',
        'bot_answer(Настроение поднялось:)).Крутой фильм)')
    >> [
         {
        "date": "2021-10-10 00:00:00+00:00",
        "user_id": 268083166,
        "username": "sirenkovv",
        "message": "Настроение поднялось:)).Крутой фильм",
        "answer": "Спасибо за хорошую обратную связь!"
    }
]
    """

    dict_m = {
        'date': str(date),
        'user_id': user_id,
        'username': username,
        'message': message,
        'answer': answer
    }

    with open('data.json', 'r', encoding='utf-8') as file:
        data_m = json.load(file)
    data_m.append(dict_m)
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(data_m, file, indent=4, ensure_ascii=False)


# Создание файла bot.log для записи логов и ошибок
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)


def start(update: Update, context: CallbackContext) -> None:
    """ Функция для отправки сообщения, когда будет выдана команда /start.

    """

    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def answer_user(update: Update, context: CallbackContext) -> None:
    """ Функция для отправки сообщения пользователю в телеграм

    """

    if check_symbol(update.message.text) == 'rus':
        answer = bot_answer(update.message.text)
        update.message.reply_text(answer)

        write_json(update.message.date + timedelta(hours=3),
                   update.message.from_user['id'],
                   update.message.from_user['username'], update.message.text,
                   answer)

    else:
        update.message.reply_text('При создании сообщения используйте\
 русские символы')
        write_json(update.message.date, update.message.from_user['id'],
                   update.message.from_user['username'], update.message.text,
                   'При создании сообщения используйте русские символы')


def main() -> None:
    """ Функция старта телеграм бота

    """

    # Передача токена телеграм бота
    updater = Updater(token="")

    # Соедининяемся с ботом в телеграм
    dispatcher = updater.dispatcher

    # Ответ бота на команду start, вызов функции start
    dispatcher.add_handler(CommandHandler("start", start))

    # Ответ бота пользователю
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                          answer_user))

    # Старт бот
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
