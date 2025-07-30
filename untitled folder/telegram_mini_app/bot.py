"""
Telegram‑бот, отправляющий кнопку для открытия мини‑приложения.

Бот использует библиотеку `aiogram` для обработки команд и сообщений. При
вызове команды `/start` бот отправляет сообщение с inline‑кнопкой, которая
открывает веб‑приложение (`/mini-app`) в Телеграме. Дополнительно
обрабатываются сообщения типа `web_app_data`, которые мини‑приложение
может отправлять обратно боту через `Telegram.WebApp.sendData()`.

Информация о публичном адресе приложения берётся из переменной
окружения `WEB_APP_URL`. Убедитесь, что этот адрес начинается с `https://`.
"""
from __future__ import annotations

import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import CommandStart
from aiogram import F
from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    # Настраиваем логирование
    logging.basicConfig(level=logging.INFO)
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    web_app_url = os.environ.get('WEB_APP_URL')
    if not token or not web_app_url:
        raise RuntimeError('Необходимо задать TELEGRAM_BOT_TOKEN и WEB_APP_URL в переменных окружения')

    bot = Bot(token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def handle_start(message: types.Message) -> None:
        """Отправляет приветствие и кнопку для запуска мини‑приложения."""
        # Создаём inline‑кнопку
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Открыть каталог',
                        web_app=WebAppInfo(url=f"{web_app_url.rstrip('/')}/mini-app"),
                    )
                ]
            ]
        )
        await message.answer(
            "Привет! Нажмите кнопку ниже, чтобы открыть каталог контента.",
            reply_markup=keyboard,
        )

    @dp.message(F.web_app_data)
    async def handle_web_app_data(message: types.Message) -> None:
        """Обрабатывает данные, отправленные мини‑приложением через sendData()."""
        data = message.web_app_data.data
        # В этом примере просто повторяем полученные данные
        await message.answer(f"Получены данные из мини‑приложения: {data}")

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Бот остановлен')