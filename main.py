import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiohttp import web

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

def get_main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📚 Maktab darsliklari", "📖 Adabiy kitoblar")
    if uid in ADMIN_IDS:
        kb.add("🛠 Admin Panel")
    return kb

def get_admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add("➕ Darslik qo'shish (PDF)", "➕ Adabiy kitob qo'shish (PDF)")
    kb.add("📊 Statistika", "📢 Xabar yuborish", "⬅️ Bosh menyu")
    return kb

def get_classes_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add(*(f"{i}-sinf" for i in range(1, 12)))
    kb.add("⬅️ Orqaga")
    return kb

@dp.message_handler(commands=['start'], state="*")
async def start_cmd(m: types.Message, state: FSMContext):
    await state.finish()
    users_set.add(m.from_user.id)
    await m.answer("Assalomu alaykum! Darsliklar va Adabiy kitoblar botiga xush kelibsiz!", reply_markup=get_main_kb(m.from_user.id))

@dp.message_handler(text="📚 Maktab darsliklari", state="*")
async def cb_classes(m: types.Message, state: FSMContext):
    await state.finish()
    await m.answer("Qaysi sinf darsligi kerak?", reply_markup=get_classes_kb())

@dp.message_handler(text="📖 Adabiy kitoblar", state="*")
async def cb_lit(m: types.Message, state: FSMContext):
    await state.finish()
    if not literature_db:
        await m.answer("📖 Hozircha adabiy kitoblar qo'shilmagan.")
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for cat in literature_db.keys():
        kb.add(cat)
    kb.add("⬅️ Bosh menyu")
    await m.answer("Adabiyot turini tanlang:", reply_markup=kb)

@dp.message_handler(text=["⬅️ Bosh menyu", "⬅️ Orqaga"], state="*")
async def go_back(m: types.Message, state: FSMContext):
    await state.finish()
    await m.answer("Bosh menyu:", reply_markup=get_main_kb(m.from_user.id))

@dp.message_handler(lambda m: m.text and m.text.endswith("-sinf"), state="*")
async def show_subs(m: types.Message):
    cls = m.text
    if cls not in textbooks_db or not textbooks_db[cls]:
        await m.answer(f"📁 {cls} uchun darsliklar topilmadi.")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    for sub in textbooks_db[cls].keys():
        kb.add(types.InlineKeyboardButton(text=sub, callback_data=f"tb_{cls}_{sub}"))
    await m.answer(f"📚 {cls} darsliklari:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("tb_"))
async def get_tb(call: types.CallbackQuery):
    _, cls, sub = call.data.split("_", 2)
    fid = textbooks_db.get(cls, {}).get(sub)
    if fid:
        await call.message.answer_document(fid, caption=f"📖 {cls} - {sub}")
    else:
        await call.answer("Topilmadi!", show_alert=True)

@dp.message_handler(lambda m: m.text in literature_db.keys(), state="*")
async def show_lit_list(m: types.Message):
    cat = m.text
    kb = types.InlineKeyboardMarkup(row_width=1)
    for title in literature_db[cat].keys():
        kb.add(types.InlineKeyboardButton(text=title, callback_data=f"lt_{cat}_{title}"))
    await m.answer(f"📖 {cat}:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("lt_"))
async def get_lit(call: types.CallbackQuery):
    parts = call.data.split("_", 2)
    cat, title = parts[1], parts[2]
    fid = literature_db.get(cat, {}).get(title)
    if fid:
        await call.message.answer_document(fid, caption=f"📖 {title}\n📂 {cat}")
    else:
        await call.answer("Topilmadi!", show_alert=True)

@dp.message_handler(text="🛠 Admin Panel", state="*")
async def admin_pnl(m: types.Message, state: FSMContext):
    await state.finish()
    if m.from_user.id not in ADMIN_IDS:
        return
    await m.answer("Admin panel:", reply_markup=get_admin_kb())

@dp.message_handler(text="📊 Statistika", state="*")
async def stats(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    await m.answer(f"📊 Foydalanuvchilar: {len(users_set)} ta")

@dp.message_handler(text="➕ Darslik qo'shish (PDF)", state="*")
async def add_tb_start(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    await AddTextbookState.waiting_for_file.set()
    await m.answer("📥 Darslik PDF faylini yuboring:")

@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=AddTextbookState.waiting_for_file)
async def add_tb_file(m: types.Message, state: FSMContext):
    if not m.document.mime_type.endswith('pdf'):
        await m.answer("⚠️ Faqat PDF yuboring!")
        return
    await state.update_data(file_id=m.document.file_id)
    await AddTextbookState.waiting_for_class.set()
    await m.answer("Sinfni tanlang:", reply_markup=get_classes_kb())

@dp.message_handler(lambda m: m.text and m.text.endswith("-sinf"), state=AddTextbookState.waiting_for_class)
async def add_tb_cls(m: types.Message, state: FSMContext):
    await state.update_data(cls=m.text)
    await AddTextbookState.waiting_for_subject.set()
    await m.answer("Fan nomini yozing (masalan: Matematika):", reply_markup=types.ReplyKeyboardRemove())

@dp.
