import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# --- SOZLAMALAR ---
BOT_TOKEN = "8156712952:AAFS8l6-06YpUa361zKylRj1-xJ_3Mv6eN4"
ADMIN_IDS = [5621415174, 8761111637]  # Adminlar ro'yxati

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- MA'LUMOTLAR BAZASI ---
textbooks_db = {}  # Format: {"1-sinf": {"Matematika": "file_id"}}
literature_db = {} # Format: {"O'zbek adabiyoti": {"O'tkan kunlar": "file_id"}}
users_set = set()

# --- FSM (Holatlar) ---
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

# --- KLAVIATURALAR ---
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
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("O'zbek adabiyoti", "Jahon adabiyoti")
    kb.add("Bolalar ertaklari", "Ilmiy-fantastik")
    kb.add("⬅️ Orqaga")
    return kb

# --- START BUYRUG'I ---
@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    users_set.add(message.from_user.id)
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
        f"📚 Maktab darsliklari va 📖 Adabiy kitoblar botiga xush kelibsiz!",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

# --- ASOSIY BO'LIMLAR ---
@dp.message_handler(text="📚 Maktab darsliklari", state="*")
async def show_classes(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Qaysi sinf darsligi kerak? Quyidagi sinflardan birini tanlang:",
        reply_markup=get_classes_keyboard()
    )

@dp.message_handler(text="📖 Adabiy kitoblar", state="*")
async def show_lit_categories(message: types.Message, state: FSMContext):
    await state.finish()
    if not literature_db:
        await message.answer("📖 Hozircha adabiy kitoblar qo'shilmagan.")
        return
    
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for cat in literature_db.keys():
        kb.add(cat)
    kb.add("⬅️ Bosh menyu")
    await message.answer("📖 Adabiyot turini tanlang:", reply_markup=kb)

@dp.message_handler(text="⬅️ Bosh menyu", state="*")
@dp.message_handler(text="⬅️ Orqaga", state="*")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Bosh menyu:", reply_markup=get_main_keyboard(message.from_user.id))

# --- MAKTAB DARSLIKLARINI KO'RSATISH ---
@dp.message_handler(lambda m: m.text and m.text.endswith("-sinf"), state="*")
async def show_subjects(message: types.Message):
    selected_class = message.text
    if selected_class not in textbooks_db or not textbooks_db[selected_class]:
        await message.answer(f"📁 {selected_class} uchun hali darsliklar yuklanmagan.")
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    for subject in textbooks_db[selected_class].keys():
        kb.add(types.InlineKeyboardButton(text=subject, callback_data=f"tbook_{selected_class}_{subject}"))
    
    await message.answer(f"📚 {selected_class} uchun mavjud darsliklar:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("tbook_"))
async def send_textbook_pdf(call: types.CallbackQuery):
    _, sel_class, subject = call.data.split("_")
    file_id = textbooks_db.get(sel_class, {}).get(subject)
    if file_id:
        await call.message.answer_document(file_id, caption=f"📖 {sel_class} — {subject}")
    else:
        await call.answer("Fayl topilmadi!", show_alert=True)

# --- ADABIY KITOBLARNI KO'RSATISH ---
@dp.message_handler(lambda m: m.text in literature_db.keys(), state="*")
async def show_lit_books(message: types.Message):
    category = message.text
    kb = types.InlineKeyboardMarkup(row_width=1)
    for title in literature_db[category].keys():
        kb.add(types.InlineKeyboardButton(text=title, callback_data=f"lit_{category}_{title}"))
    
    await message.answer(f"📖 '{category}' bo'limidagi kitoblar:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("lit_"))
async def send_lit_pdf(call: types.CallbackQuery):
    parts = call.data.split("_", 2)
    category = parts[1]
    title = parts[2]
    file_id = literature_db.get(category, {}).get(title)
    if file_id:
        await call.message.answer_document(file_id, caption=f"📖 {title}\n📂 Bo'lim: {category}")
    else:
        await call.answer("Kitob topilmadi!", show_alert=True)

# --- ADMIN PANEL ---
@dp.message_handler(text="🛠 Admin Panel", state="*")
async def admin_panel(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🛠 Admin panelga xush kelibsiz!", reply_markup=get_admin_keyboard())

@dp.message_handler(text="📊 Statistika", state="*")
async def show_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(f"📊 Jami foydalanuvchilar soni: {len(users_set)} ta")

# --- ADMIN: DARSLIK QO'SHISH ---
@dp.message_handler(text="➕ Darslik qo'shish (PDF)", state="*")
async def start_add_textbook(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await AddTextbookState.waiting_for_file.set()
    await message.answer("📥 Maktab darsligining **PDF faylini** yuboring:")

@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=AddTextbookState.waiting_for_file)
async def process_tb_file(message: types.Message, state: FSMContext):
    if not message.document.mime_type.endswith('pdf'):
        await message.answer("⚠️ Iltimos, faqat **PDF** formatidagi fayl yuboring!")
        return

    await state.update_data(file_id=message.document.file_id)
    await AddTextbookState.waiting_for_class.set()
    await message.answer("✅ Fayl qabul qilindi! Endi darslik **qaysi sinfga** tegishli ekanligini tanlang:", reply_markup=get_classes_keyboard())

@dp.message_handler(lambda m: m.text and m.text.endswith("-sinf"), state=AddTextbookState.waiting_for_class)
async def process_tb_class(message: types.Message, state: FSMContext):
    await state.update_data(selected_class=message.text)
    await AddTextbookState.waiting_for_subject.set()
    await message.answer(f"✅ {message.text} tanlandi. Endi **fan nomini** yozing (Masalan: *Matematika*):", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(state=AddTextbookState.waiting_for_subject)
async def process_tb_subject(message: types.Message, state: FSMContext):
    subject_name = message.text.strip()
    data = await state.get_data()
    sel_class = data['selected_class']
    file_id = data['file_id']

    if sel_class not in textbooks_db:
        textbooks_db[sel_class] = {}
    
    textbooks_db[sel_class][subject_name] = file_id
    await state.finish()

    await message.answer(f"🎉 Darslik qo'shildi!\n📌 Sinf: {sel_class}\n📖 Fan: {subject_name}", reply_markup=get_admin_keyboard())

# --- ADMIN: ADABIY KITOB QO'SHISH ---
@dp.message_handler(text="➕ Adabiy kitob qo'shish (PDF)", state="*")
async def start_add_lit(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await AddLitState.waiting_for_file.set()
    await message.answer("📥 Adabiy kitobning **PDF faylini** yuboring:")

@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=AddLitState.waiting_for_file)
async def process_lit_file(message: types.Message, state: FSMContext):
    if not message.document.mime_type.endswith('pdf'):
        await message.answer("⚠️ Iltimos, faqat **PDF** formatidagi fayl yuboring!")
        return

    await state.update_data(file_id=message.document.file_id)
    await AddLitState.waiting_for_category.set()
    await message.answer("✅ Fayl qabul qilindi! Kitob uchun kategoriya tanlang yoki nomini yozing (Masalan: *O'zbek adabiyoti*):", reply_markup=get_lit_categories_keyboard())

@dp.message_handler(state=AddLitState.waiting_for_category)
async def process_lit_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await AddLitState.waiting_for_title.set()
    await message.answer("✅ Kategoriya saqlandi. Endi **kitobning nomini** yozing (Masalan: *O'tkan kunlar*):", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(state=AddLitState.waiting_for_title)
async def process_lit_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    data = await state.get_data()
    category = data['category']
    file_id = data['file_id']

    if category not in literature_db:
        literature_db[category] = {}
    
    literature_db[category][title] = file_id
    await state.finish()

    await message.answer(f"🎉 Adabiy kitob qo'shildi!\n📂 Kategoriya: {category}\n📖 Kitob nomi: {title}", reply_markup=get_admin_keyboard())

# --- RASSILKA (XABAR YUBORISH) ---
@dp.message_handler(text="📢 Xabar yuborish", state="*")
async def start_broadcast(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await BroadcastState.waiting_for_message.set()
    await message.answer("Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:")

@dp.message_handler(state=BroadcastState.waiting_for_message)
async def process_broadcast(message: types.Message, state: FSMContext):
    await state.finish()
    count = 0
    for user_id in users_set:
        try:
            await bot.send_message(user_id, message.text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"✅ Xabar {count} ta foydalanuvchiga yuborildi!", reply_markup=get_admin_keyboard())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
