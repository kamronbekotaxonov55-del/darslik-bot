import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

BOT_TOKEN = "8156712952:AAFS8l6-06YpUa361zKylRj1-xJ_3Mv6eN4"
ADMIN_IDS = [5621415174, 8761111637]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

textbooks_db = {}
literature_db = {}
users_set = set()

class AddTextbookState(StatesGroup):
    waiting_for_file = State()
    waiting_for_class = State()
    waiting_for_subject = State()

class AddLitState(StatesGroup):
    waiting_for_file = State()
    waiting_for_category = State()
    waiting_for_title = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

def get_main_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📚 Maktab darsliklari", "📖 Adabiy kitoblar")
    if user_id in ADMIN_IDS:
        kb.add("🛠 Admin Panel")
    return kb

def get_admin_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add("➕ Darslik qo'shish (PDF)")
    kb.add("➕ Adabiy kitob qo'shish (PDF)")
    kb.add("📊 Statistika", "📢 Xabar yuborish")
    kb.add("⬅️ Bosh menyu")
    return kb

def get_classes_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [f"{i}-sinf" for i in range(1, 12)]
    kb.add(*buttons)
    kb.add("⬅️ Orqaga")
    return kb

def get_lit_categories_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row
