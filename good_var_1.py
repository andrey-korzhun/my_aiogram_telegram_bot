import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
import openai
import asyncio

# Загрузка переменных окружения
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ALLOWED_USERS = os.getenv('ALLOWED_USERS').split(',')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Установка API ключа OpenAI
openai.api_key = OPENAI_API_KEY

user_states = {}

class UserState:
    def __init__(self, start_prompt):
        self.start_prompt = start_prompt
        self.answers = []
        self.questions = []
        self.stage = 0

async def start_dialogue(message: types.Message, user_state: UserState):
    if user_state.stage == 0:
        await message.answer("Начнём диалог! Первый вопрос: Какой ваш любимый фильм?")
        user_state.questions.append("Какой ваш любимый фильм?")
        user_state.stage += 1
    else:
        user_state.answers.append(message.text)
        if user_state.stage < 8:
            response = await get_chatgpt_response(user_state)
            user_state.questions.append(response)
            await message.answer(response)
            user_state.stage += 1
        else:
            await send_options(message)

async def send_options(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Ссылка 1", url="https://example.com/1"))
    keyboard.add(InlineKeyboardButton("Ссылка 2", url="https://example.com/2"))
    keyboard.add(InlineKeyboardButton("Новый диалог", callback_data="new_dialog"))
    await message.answer("Выберите действие:", reply_markup=keyboard)

async def get_chatgpt_response(user_state: UserState):
    conversation = user_state.start_prompt + "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(user_state.questions, user_state.answers)])
    response = openai.Completion.create(
        model="text-davinci-004",
        prompt=conversation,
        max_tokens=100
    )
    return response.choices[0].text.strip()

@dp.message_handler(Command('start'))
async def cmd_start(message: types.Message):
    if message.from_user.username in ALLOWED_USERS:
        user_state = UserState("Это начальный промпт.\n")
        user_states[message.from_user.id] = user_state
        await start_dialogue(message, user_state)
    else:
        await message.answer("Вы не имеете доступа к этому боту.")

@dp.message_handler()
async def process_message(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_states:
        user_state = user_states[user_id]
        await start_dialogue(message, user_state)
    else:
        await message.answer("Используйте команду /start для начала диалога.")

@dp.callback_query_handler(lambda c: c.data == 'new_dialog')
async def process_callback_new_dialog(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_states:
        user_state = user_states[user_id]
        user_state.answers = []
        user_state.questions = []
        user_state.stage = 0
        await start_dialogue(callback_query.message, user_state)
    await bot.answer_callback_query(callback_query.id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
