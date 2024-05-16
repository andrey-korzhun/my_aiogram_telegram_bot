import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StatesGroup, State
from aiogram.utils import executor

from transformers import AutoModelForChat, AutoTokenizer

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHATGPT_MODEL = os.getenv('CHATGPT_MODEL')
CHATGPT_TOKENIZER = os.getenv('CHATGPT_TOKENIZER')
RESTRICTED_USERS = os.getenv('RESTRICTED_USERS', '').split(',')

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage)

class ChatGPTBot(StatesGroup):
    waiting_for_start = State()
    waiting_for_answers = State()
    waiting_for_choice = State()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.from_user.username in RESTRICTED_USERS:
        await message.answer('Access denied')
        return
    await ChatGPTBot.waiting_for_answers.set()
    await message.answer('Let\'s start our conversation! What do you think about AI?')

@dp.message_handler(state=ChatGPTBot.waiting_for_answers)
async def process_answers(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if not data.get('history'):
            data['history'] = []
        data['history'].append(message.text)
        if len(data['history']) < 8:
            model = AutoModelForChat.from_pretrained(CHATGPT_MODEL)
            tokenizer = AutoTokenizer.from_pretrained(CHATGPT_TOKENIZER)
            prompt = ' '.join(data['history'] + [message.text])
            input_ids = tokenizer.encode(prompt, return_tensors='pt')
            output = model(input_ids)
            response = tokenizer.decode(output[0].argmax(-1))
            await message.answer(response)
        else:
            await state.set_state(ChatGPTBot.waiting_for_choice)
            await message.answer('You have finished the conversation. Choose an option:', reply_markup=types.ReplyKeyboardMarkup([
                ['External link 1', 'External link 2', 'More questions']
            ]))

@dp.message_handler(state=ChatGPTBot.waiting_for_choice)
async def process_choice(message: types.Message, state: FSMContext):
    if message.text == 'External link 1':
        await message.answer('https://example.com/link1')
    elif message.text == 'External link 2':
        await message.answer('https://example.com/link2')
    elif message.text == 'More questions':
        async with state.proxy() as data:
            data['history'] = []
            data['prompt'] = 'Let\'s continue our conversation! What do you think about AI in healthcare?'
            await state.set_state(ChatGPTBot.waiting_for_answers)
            await message.answer(data['prompt'])
    else:
        await message.answer('Invalid option. Please choose again.')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
