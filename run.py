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
    initial_prompt = "Как долго вы вместе и какие вы видите проблемы в ваших отношениях?"
    
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
    if len(user_dialogs[user_id]) <= 16:
        # Генерируем ответ ChatGPT
        prompt = """
        Привет Софи! Ты семейный психолог с 15-ти летним стажем работы.
        К тебе на прием пришел клиент, который хочет понять какие проблемы есть у него в отношениях.
        Твоя задача - провести первый сеанс и продиагностировать ситуацию.
        Проведи тест из 7 вопросов на выявление проблем в отношениях.
        Получай ответ от человека, не придумывай сама.
        Следующий вопрос задай основываясь на предыдущем вопросе.
        После 7-го вопроса проанализируй ответы и напиши рекомендацию что делать
        """
        chatgpt_response = generate_chatgpt_response(prompt, user_dialogs[user_id])

        # Добавляем ответ ChatGPT в историю
        user_dialogs[user_id].append({"role": "assistant", "content": chatgpt_response})

        # Отправляем ответ ChatGPT пользователю
        bot.send_message(user_id, chatgpt_response)
    else:
        user_dialogs[user_id] = []
        # Создаем кнопки
        markup = telebot.types.InlineKeyboardMarkup()
        btn1 = telebot.types.InlineKeyboardButton("ОПЛАТИТЬ", url='https://tinyurl.com/paysofi')
        btn2 = telebot.types.InlineKeyboardButton("Написать отзыв", url="https://t.me/Dr_Haifisch")
        btn3 = telebot.types.InlineKeyboardButton("Создать сказку!", callback_data="continue")
        markup.add(btn1, btn2, btn3)

        # Отправляем кнопки пользователю
        bot.send_message(user_id, "Выберите действие:", reply_markup=markup)

# Обработчик нажатия кнопки "Продолжить диалог"
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id

    if call.data == "continue":
        # Устанавливаем новый промпт
        prompt = """
        Софи, ты семейный психолог с 15-ти летним стажем работы. К тебе на прием пришел клиент, который хочет сохранить отношения. Для того, чтобы вернуть приятные воспоминания о встрече клиенту и партнеру клиента, напиши сказку том как клиент и его партнер встретились. Если клиент мужчина, то его партнер девушка. Если клиент девушка, то ее партнер мужчина. 
        Сказка должна содержать три блока. Первый блок - время до встречи друг с другом. В этом блоке можно немного пофантазировать чем могли бы заниматься герои истории в рамках выбранной темы и вселенной. Важно отметить, что в первом блоке они еще не познали истинного счастья, так как не встретились. Второй блок - встреча. В этом блоке расскажи как они встретились, несмотря на все невзгоды и сразу поняли, что что-то испытывают друг к другу. Второй блок самый объемный по тексту, добавь сюда все детали, которые укажет клиент. Если детали не соответствуют вселенной или тематике, постарайся их адаптировать, чтобы они гармонично вписались. Третий блок - их будущее. В блоке важно указать, что пару ждало еще много испытаний, но, пока они вместе, они постараются преодолеть все невзгоды. 
        Стиль сказки должен быть волшебным. Стиль текста - художественный. Добавь в сказку милую и смешную ситуацию. Задача сказки - вернуть приятные воспоминания о встрече, получить позитивное настроение и получить надежду, что в реальной жизни клиент и его партнер тоже преодолеют все трудности, которые их ждут. 
        Для составления сказки задай 7 вопросов клиенту. Общайся на ты. Список вопросов:
        1. “Как зовут тебя и твоего партнера?”
        2. “Где вы познакомились с партнером?” (Если клиент назвал имя партнера, используй в вопросе названное имя партнера, вместо обезличенного обращения “Партнер”)
        3. “Это была случайная встреча или вас познакомили друг с другом?”
        4. “Чем тебе больше всего запомнилась встреча?”
        5. “Кем ты работаешь и чем любишь заниматься?”
        6. “Кем работает твой партнер и чем любит заниматься?” (Если клиент назвал имя партнера, используй в вопросе названное имя партнера, вместо обезличенного обращения “Партнер”)
        7. “Какой антураж для сказки ты выберешь? Древний Египет, Эпоху просвещения в европе, Настоящее время или далекое будущее? Если что-то другое или более конкретное - назови свой вариант.”
        Задай первый вопрос: “Как зовут тебя и твоего партнера?” и получи на него ответ. Получай ответ от человека, не придумывай сама. Не задавай следующий вопрос, пока не получишь на ответ от клиента на текущий вопрос. После получения ответа на 7 указанных вопросов - сгенерируй сказку.

        После генерации сказки отправь следующим, отдельным сообщением информацию о том, что эту сказку клиент может послать партнеру, чтобы поднять настроение. 
        """

        # Генерируем 7 вопросов от ChatGPT
        # for _ in range(7):
        chatgpt_response = generate_chatgpt_response(prompt, user_dialogs[user_id])
        user_dialogs[user_id].append({"role": "assistant", "content": chatgpt_response})
        bot.send_message(user_id, chatgpt_response)

# Запуск бота
bot.polling()
