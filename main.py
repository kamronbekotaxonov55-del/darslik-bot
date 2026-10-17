import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

SPONSOR_CHANNEL = os.getenv("SPONSOR_CHANNEL", "@telegram") 

async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
        return member.status != "left"
    except Exception:
        return True

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    is_subscribed = await check_sub(message.from_user.id)
    if not is_subscribed:
        btn = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{SPONSOR_CHANNEL.replace('@', '')}")
        ).add(
            InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")
        )
        await message.answer("📚 Botdan foydalanish uchun avval homiy kanalga obuna bo'ling:", reply_markup=btn)
        return

    await message.answer(f"Assalomu alaykum, {message.from_user.first_name}!\n\n📚 Maktab darsliklari botiga xush kelibsiz! Qaysi sinf darsligi kerak?")

@dp.callback_query_handler(text="check_subscription")
async def check_cb(query: types.CallbackQuery):
    is_subscribed = await check_sub(query.from_user.id)
    if is_subscribed:
        await query.message.delete()
        await query.message.answer("✅ Rahmat! Endi botdan bemalol foydalanishingiz mumkin.\n/start tugmasini bosing.")
    else:
        await query.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
