import telebot
import openai
import logging
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Инициализация логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Токены
TG_TOKEN = os.getenv("TG_TOKEN")
AI_TOKEN = os.getenv("AI_TOKEN")

# Инициализация ChatGPT
openai.api_key = AI_TOKEN

# Инициализация бота
bot = telebot.TeleBot(TG_TOKEN)

# Словарь для хранения истории диалогов пользователей
user_dialogs = {}

# Ограничение по username (замените на список username)
restricted_users = ["username1", "username2"]

# Функция для генерации ответа ChatGPT
def generate_chatgpt_response(prompt, conversation_history):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            *conversation_history
        ]
    )
    return response.choices[0].message['content'].strip()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Проверка на ограничение
    if username in restricted_users:
        bot.send_message(user_id, "Извините, ваш доступ к этому боту ограничен.")
        return

    # Инициализация диалога
    user_dialogs[user_id] = []
    
    # Задаем начальный промпт
    initial_prompt = "Привет! Давай поболтаем. Расскажи мне о своем любимом хобби."
    
    # Отправляем первый вопрос
    bot.send_message(user_id, initial_prompt)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id

    # Проверка на наличие диалога
    if user_id not in user_dialogs:
        bot.send_message(user_id, "Для начала диалога введите /start")
        return

    # Добавляем сообщение пользователя в историю
    user_dialogs[user_id].append({"role": "user", "content": message.text})

    # Проверяем количество ответов пользователя
    if len(user_dialogs[user_id]) <= 8:
        # Генерируем ответ ChatGPT
        prompt = "Ответь на вопрос пользователя и задай свой вопрос."
        chatgpt_response = generate_chatgpt_response(prompt, user_dialogs[user_id])

        # Добавляем ответ ChatGPT в историю
        user_dialogs[user_id].append({"role": "assistant", "content": chatgpt_response})

        # Отправляем ответ ChatGPT пользователю
        bot.send_message(user_id, chatgpt_response)
    else:
        # Создаем кнопки
        markup = telebot.types.InlineKeyboardMarkup()
        btn1 = telebot.types.InlineKeyboardButton("Ссылка 1", url="https://www.google.com")
        btn2 = telebot.types.InlineKeyboardButton("Ссылка 2", url="https://www.yandex.ru")
        btn3 = telebot.types.InlineKeyboardButton("Продолжить диалог", callback_data="continue")
        markup.add(btn1, btn2, btn3)

        # Отправляем кнопки пользователю
        bot.send_message(user_id, "Выберите действие:", reply_markup=markup)

# Обработчик нажатия кнопки "Продолжить диалог"
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id

    if call.data == "continue":
        # Устанавливаем новый промпт
        prompt = "Продолжим наш диалог! Расскажи мне о своих планах на будущее."

        # Генерируем 7 вопросов от ChatGPT
        for _ in range(7):
            chatgpt_response = generate_chatgpt_response(prompt, user_dialogs[user_id])
            user_dialogs[user_id].append({"role": "assistant", "content": chatgpt_response})
            bot.send_message(user_id, chatgpt_response)

# Запуск бота
bot.polling()
