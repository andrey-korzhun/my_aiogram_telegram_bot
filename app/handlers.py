from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.generators import gpt4

router = Router()


class Generate(StatesGroup):
    text = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer('Добро пожаловать в бот! Напишите ваш вопрос!')
    await state.clear()


@router.message(Generate.text)
async def generate_error(message: Message):
    await message.answer('Подождите, ответ генерируется...')


@router.message(F.text)
async def generate(message: Message, state: FSMContext):
   await state.set_state(Generate.text)
   response = await gpt4(message.text)
   await message.answer(response.choices[0].message.content)
   await state.clear()
