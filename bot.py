import asyncio
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder, InlineKeyboardButton, ReplyKeyboardBuilder
)
from dotenv import load_dotenv

from database import (
    create_table, update_quiz_index,
    update_right_answer, get_quiz_index, get_right_answers
)
from questions import quiz_data


load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

bot = Bot(API_TOKEN)
dp = Dispatcher()


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    """Обработчик команды /start."""
    builder = ReplyKeyboardBuilder()
    builder.button(text='Начать игру')
    await message.answer(
        'Добро пожаловать в квиз!',
        reply_markup=builder.as_markup(resize_keyboard=True)
    )


@dp.message(F.text == 'Начать игру')
@dp.message(Command('quiz'))
async def cmd_quiz(message: types.Message):
    """Обработчик команды /quiz."""
    await message.answer('Давай начнем квиз!')
    await new_quiz(message)


async def new_quiz(message: types.Message):
    """Начало нового квиза."""
    user_id: int = message.from_user.id
    current_question_index: int = 0
    await update_quiz_index(user_id, current_question_index)
    await get_question(message, user_id)


async def get_question(message: types.Message, user_id: int):
    """Получение вопроса из базы данных и отправка пользователю."""
    current_question_index: int = await get_quiz_index(user_id)
    correct_index: int = quiz_data[current_question_index]['correct_option']
    opts: list = quiz_data[current_question_index]['options']
    kb: list = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(
        f'{quiz_data[current_question_index]["question"]}',
        reply_markup=kb
    )


def generate_options_keyboard(answer_options, right_answer):
    """Генерация клавиатуры с вариантами ответов."""
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=(
                'right_answer'
                if option == right_answer
                else 'wrong_answer'
            )
        ))

    builder.adjust(1)
    return builder.as_markup()


@dp.callback_query(F.data.in_({'right_answer', 'wrong_answer'}))
async def answer(callback: types.CallbackQuery):
    """Обработчик ответов."""

    current_question_index: int = await get_quiz_index(callback.from_user.id)
    user_answer: str = callback.data
    correct_answer_index: int = quiz_data[
        current_question_index
    ]['correct_option']
    correct_answer: str = quiz_data[
        current_question_index
    ]['options'][correct_answer_index]

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=f'Ваш ответ: {user_answer}',
            callback_data='disabled'
        )
    )

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=builder.as_markup()
    )

    if user_answer == 'right_answer':
        await callback.message.answer('Правильно!')
        await update_right_answer(callback.from_user.id)
    else:
        await callback.message.answer(
            'Неверно! Правильный ответ: '
            f'{correct_answer}'
        )

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        statistics = await get_right_answers(callback.from_user.id)
        await callback.message.answer(
            'Это был последний вопрос. Квиз завершен!\n'
            f'Ваш результат: {statistics} из {len(quiz_data)}'
        )


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(create_table())
    asyncio.run(main())
