import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.bot import DefaultBotProperties
from aiogram.filters import Command
import asyncio

from openai import AsyncOpenAI


load_dotenv()
TG_TOKEN = os.getenv('TG_TOKEN')
AI_TOKEN = os.getenv('AI_TOKEN')

client = AsyncOpenAI(api_key=AI_TOKEN)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_dialogs = {}

restricted_users = ["username1", "username2"]

n_questions = 7

prompt = f'''
Привет Софи! 
'''

finalize = '''
Проанализируй ответы и напиши рекомендации как психолог для проработки проблем клиента.
'''

pay_text = """
Предлагаю оформить пробный период на 7 дней за 200 рублей ↓

"""

async def generate_chatgpt_response(prompt, conversation_history):
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            *conversation_history
        ]
    )
    return response.choices[0].message['content'].strip()

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

    if user_id not in user_dialogs:
        await message.answer("Для начала диалога введите /start")
        return

    user_dialogs[user_id].append({"role": "user", "content": message.text})

    if len(user_dialogs[user_id]) >= ((n_questions * 2) - 1):
        chatgpt_response = await generate_chatgpt_response(finalize, user_dialogs[user_id])

        await message.answer(chatgpt_response)

        markup = InlineKeyboardMarkup()
        btn1 = InlineKeyboardButton("ОПЛАТИТЬ", url='https://tinyurl.com/paysofi')
        btn2 = InlineKeyboardButton("Написать отзыв", url="https://t.me/Dr_Haifisch")
        btn3 = InlineKeyboardButton("Создать сказку!", callback_data="continue")
        markup.add(btn1, btn2, btn3)

        await message.answer(pay_text, reply_markup=markup)

        user_dialogs[user_id] = []

    else:
        chatgpt_response = await generate_chatgpt_response(prompt, user_dialogs[user_id])

        user_dialogs[user_id].append({"role": "assistant", "content": chatgpt_response})

        await message.answer(chatgpt_response)

@router.callback_query(lambda c: c.data == "continue")
async def callback_query(call: types.CallbackQuery):
    global prompt, finalize, pay_text, user_dialogs
    user_id = call.from_user.id

    prompt = """
    Софи, ты семейный психолог
    """

    finalize = '''
    Софи, ты семейный психолог
    '''

    pay_text = "Перешли сказку, чтобы поднять настроение! )"

    first_question = "Как зовут тебя и твоего партнера?"

    await bot.send_message(user_id, first_question)

    user_dialogs[user_id] = []

    user_dialogs[user_id].append({"role": "assistant", "content": first_question})

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')