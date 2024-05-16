import os
from dotenv import load_dotenv

import telebot
import openai
from telebot import types


load_dotenv()

# Константы
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')
OPENAI_API_KEY = os.getenv('AI_TOKEN')
MAX_HISTORY_LENGTH = 16  # 8 вопросов и 8 ответов
WELCOME_PROMPT = """
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

SCENARIOS = {
    "Сценарий 1": "Ты выбрал Сценарий 1. Начнем!",
    "Сценарий 2": "Ты выбрал Сценарий 2. Начнем!",
    "Сценарий 3": "Ты выбрал Сценарий 3. Начнем!"
}

# Инициализация OpenAI
openai.api_key = OPENAI_API_KEY

# Инициализация Telebot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Переменная для сохранения истории диалога (использование словаря для хранения данных пользователей)
user_data = {}

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {"conversation": [{"role": "user", "content": WELCOME_PROMPT}], "scenario": None}

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=user_data[chat_id]["conversation"]
        )
        ai_response = response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Ошибка при вызове OpenAI API: {e}")
        ai_response = "Произошла ошибка при обработке вашего запроса."

    user_data[chat_id]["conversation"].append({"role": "assistant", "content": ai_response})
    bot.send_message(chat_id, ai_response)

# Показ кнопок с различными сценариями
def show_scenarios(message):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for scenario in SCENARIOS.keys():
        keyboard.add(types.KeyboardButton(scenario))
    bot.send_message(message.chat.id, "Выберите следующий сценарий:", reply_markup=keyboard)

# Обработка выбора сценария
@bot.message_handler(func=lambda message: message.text in SCENARIOS)
def choose_scenario(message):
    chat_id = message.chat.id
    scenario_prompt = SCENARIOS[message.text]
    user_data[chat_id] = {"conversation": [{"role": "user", "content": scenario_prompt}], "scenario": message.text}

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=user_data[chat_id]["conversation"]
        )
        ai_response = response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Ошибка при вызове OpenAI API: {e}")
        ai_response = "Произошла ошибка при обработке вашего запроса."

    user_data[chat_id]["conversation"].append({"role": "assistant", "content": ai_response})
    bot.send_message(chat_id, ai_response)

# Обработка сообщений от пользователя
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_message = message.text
    conversation = user_data.get(chat_id, {}).get("conversation", [])

    conversation.append({"role": "user", "content": user_message})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=conversation
        )
        ai_response = response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Ошибка при вызове OpenAI API: {e}")
        ai_response = "Произошла ошибка при обработке вашего запроса."

    conversation.append({"role": "assistant", "content": ai_response})
    bot.send_message(chat_id, ai_response)

    if len(conversation) >= MAX_HISTORY_LENGTH:
        
        show_scenarios(message)
    else:
        user_data[chat_id]["conversation"] = conversation  # Обновляем историю диалога

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
