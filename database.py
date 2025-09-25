import aiosqlite

from config import DB_NAME


async def create_table():
    """Создание базы данных."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_state(
                user_id INTEGER PRIMARY KEY,
                question_index INTEGER,
                correct_answer INTEGER DEFAULT 0
            )
            """
        )
        await db.commit()


async def update_quiz_index(user_id: int, question_index: int):
    """Обновление данных о конкретном вопросе."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO quiz_state (user_id, question_index)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE
            SET question_index = excluded.question_index
            """,
            (user_id, question_index)
        )
        await db.commit()


async def update_right_answer(user_id: int):
    """Обновляет количество правильных ответов."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE quiz_state
            SET correct_answer = correct_answer + 1
            WHERE user_id = ?
            """,
            (user_id,)
        )
        if db.total_changes == 0:
            await db.execute(
                """
                INSERT INTO quiz_state (user_id, correct_answer)
                VALUES (?, ?)
                """,
                (user_id, 1)
            )
        await db.commit()


async def get_quiz_index(user_id: int):
    """Получение конретного вопроса из базы данных."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """
            SELECT question_index FROM quiz_state WHERE user_id = ?
            """,
            (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def get_right_answers(user_id: int):
    """"Получение количества правильных ответов из базы данных."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """
            SELECT correct_answer FROM quiz_state WHERE user_id = ?
            """,
            (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0
