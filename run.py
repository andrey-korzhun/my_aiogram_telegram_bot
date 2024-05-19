import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import openai
import asyncio

load_dotenv()
TG_TOKEN = os.getenv('TG_TOKEN')
AI_TOKEN = os.getenv('AI_TOKEN')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TG_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

openai.api_key = AI_TOKEN

user_dialogs = {}

restricted_users = ["username1", "username2"]

n_questions = 7

prompt = f'''
Привет Софи! 
'''

temp = '''
Если ответ клиента на твой вопрос очень короткий и в нем недостаточно информации для анализа - задай уточняющий вопрос, используя доброжелательные формулировки.

'''

finalize = '''
Проанализируй ответы и напиши рекомендации как психолог для проработки проблем клиента.

'''

pay_text = """
Предлагаю оформить пробный период на 7 дней за 200 рублей ↓

"""

async def generate_chatgpt_response(prompt, conversation_history):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            *conversation_history
        ]
    )
    return response.choices[0].message['content'].strip()

# Создаем Router
router = Router()
dp.include_router(router)

@router.message(Command(commands=['start']))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username

    if username in restricted_users:
        await message.answer("Извините, ваш доступ ограничен.")
        return

    user_dialogs[user_id] = []

    initial_prompt = "Как долго вы вместе и какие вы видите проблемы в ваших отношениях?"

    await message.answer(initial_prompt)

    user_dialogs[user_id].append({"role": "assistant", "content": initial_prompt})

@router.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    # Проверка на наличие диалога
    if user_id not in user_dialogs:
        await message.answer("Для начала диалога введите /start")
        return

    # Добавляем сообщение пользователя в историю
    user_dialogs[user_id].append({"role": "user", "content": message.text})

    if len(user_dialogs[user_id]) >= ((n_questions * 2) - 1):
        # Генерируем финальный ответ ChatGPT
        chatgpt_response = await generate_chatgpt_response(finalize, user_dialogs[user_id])

        # Отправляем ответ ChatGPT пользователю
        await message.answer(chatgpt_response)

        # Создаем кнопки
        markup = InlineKeyboardMarkup()
        btn1 = InlineKeyboardButton("ОПЛАТИТЬ", url='https://tinyurl.com/paysofi')
        btn2 = InlineKeyboardButton("Написать отзыв", url="https://t.me/Dr_Haifisch")
        btn3 = InlineKeyboardButton("Создать сказку!", callback_data="continue")
        markup.add(btn1, btn2, btn3)

        # Отправляем кнопки пользователю
        await message.answer(pay_text, reply_markup=markup)

        # Очищаем историю диалога
        user_dialogs[user_id] = []

    else:
        # Генерируем ответ ChatGPT
        chatgpt_response = await generate_chatgpt_response(prompt, user_dialogs[user_id])

        # Добавляем ответ ChatGPT в историю
        user_dialogs[user_id].append({"role": "assistant", "content": chatgpt_response})

        # Отправляем ответ ChatGPT пользователю
        await message.answer(chatgpt_response)

# Обработчик нажатия кнопки "Создать сказку!"
@router.callback_query(lambda c: c.data == "continue")
async def callback_query(call: types.CallbackQuery):
    global prompt, finalize, pay_text, user_dialogs
    user_id = call.from_user.id

    # Устанавливаем новый промпт
    prompt = """
    Софи, ты семейный психолог с 15-ти летним стажем работы.
    """
    # После генерации сказки отправь следующим, отдельным сообщением информацию о том, что эту сказку клиент может послать партнеру, чтобы поднять настроение.

    finalize = '''
    Софи, ты семейный психолог с 15-
    '''

    pay_text = "Перешли сказку, чтобы поднять настроение! )"

    first_question = "Как зовут тебя и твоего партнера?"

    # Отправляем первый вопрос для составления сказки
    await bot.send_message(user_id, first_question)

    # Очищаем историю диалога
    user_dialogs[user_id] = []

    # Добавляем первый вопрос в историю
    user_dialogs[user_id].append({"role": "assistant", "content": first_question})

async def main():
    await dp.start_polling(bot, skip_updates=True)

# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())