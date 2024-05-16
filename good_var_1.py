import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
import openai
import asyncio
import httpx
from openai import AsyncOpenAI

# Загрузка переменных окружения
load_dotenv()

API_TOKEN = os.getenv('TG_TOKEN')
OPENAI_API_KEY = os.getenv('AI_TOKEN')
# ALLOWED_USERS = os.getenv('ALLOWED_USERS').split(',')
STOP_LIST = []

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Установка API ключа OpenAI
openai.api_key = OPENAI_API_KEY

user_states = {}

class UserState:
    def __init__(self, start_prompt):
        self.start_prompt = start_prompt
        self.answers = []
        self.questions = []
        self.stage = 0

client = AsyncOpenAI(api_key=os.getenv('AI_TOKEN'),
                     http_client=httpx.AsyncClient(
                         proxies=os.getenv('PROXY'),
                         transport=httpx.HTTPTransport(local_address="0.0.0.0")
                     ))


# Настройка HTTP-клиента с использованием прокси
async def get_chatgpt_response(user_state: UserState):
    conversation = user_state.start_prompt + "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(user_state.questions, user_state.answers)])
    response = await client.chat.completions.create(
        messages=[{"role": "user",
               "content": str(conversation)}],
        model="gpt-4o"
    )
    return response.choices[0].message.content


async def start_dialogue(message: types.Message, user_state: UserState):
    if user_state.stage == 0:
        first_question = "Какой ваш любимый фильм?"
        await message.answer(first_question)
        user_state.questions.append(first_question)
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

@router.message(Command('start'))
async def cmd_start(message: types.Message):
    if message.from_user.username not in STOP_LIST:
        user_state = UserState("Это начальный промпт.\n")
        user_states[message.from_user.id] = user_state
        await start_dialogue(message, user_state)
    else:
        await message.answer("Вы не имеете доступа к этому боту.")

@router.message()
async def process_message(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_states:
        user_state = user_states[user_id]
        await start_dialogue(message, user_state)
    else:
        await message.answer("Используйте команду /start для начала диалога.")

@router.callback_query(lambda c: c.data == 'new_dialog')
async def process_callback_new_dialog(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_states:
        user_state = user_states[user_id]
        user_state.answers = []
        user_state.questions = []
        user_state.stage = 0
        await start_dialogue(callback_query.message, user_state)
    await bot.answer_callback_query(callback_query.id)

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
