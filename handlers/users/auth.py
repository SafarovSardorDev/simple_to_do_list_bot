import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, db
from states.register import RegisterState
from keyboards.default.mainbuttons import main_menu, phone_request_keyboard

async def send_greeting(message: types.Message, user: dict):
    """Foydalanuvchi uchun salomlash xabarini yuborish"""
    if user.firstName and user.lastName:
        greeting = f"Salom {user.firstName} {user.lastName}, siz ro‘yxatdan o‘tgansiz!"
    else:
        username = user.username or f"user_{user.telegramId}"
        greeting = f"Salom {username}, siz ro‘yxatdan o‘tgansiz!"
    await message.answer(greeting, reply_markup=main_menu())

@dp.message_handler(commands=['start'], state='*')
async def start_register(message: types.Message, state: FSMContext):
    await state.finish()  # Joriy holatni tozalash

    # Foydalanuvchi ro'yxatdan o'tganligini tekshirish
    user = await db.user.find_first(where={"telegramId": message.from_user.id})
    if user:
        await send_greeting(message, user)
        return

    await message.answer("Ismingizni kiriting:")
    await RegisterState.first_name.set()

@dp.message_handler(state=RegisterState.first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    first_name = message.text.strip()
    if not first_name:
        await message.answer("❌ Ism bo‘sh bo‘lmasligi kerak. Iltimos, ismingizni kiriting:")
        return
    await state.update_data(first_name=first_name)
    await message.answer("Familyangizni kiriting:")
    await RegisterState.last_name.set()

@dp.message_handler(state=RegisterState.last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    last_name = message.text.strip()
    if not last_name:
        await message.answer("❌ Familiya bo‘sh bo‘lmasligi kerak. Iltimos, familyangizni kiriting:")
        return
    await state.update_data(last_name=last_name)
    await message.answer(
        "Telefon raqamingizni kiriting\nNamuna: +998901234567",
        reply_markup=phone_request_keyboard(),
        parse_mode=None
    )
    await RegisterState.phone.set()

@dp.message_handler(content_types=['contact', 'text'], state=RegisterState.phone)
async def process_phone(message: types.Message, state: FSMContext):
    # Telefon raqamni olish
    phone = message.contact.phone_number if message.content_type == 'contact' else message.text.strip()

    # Telefon raqamni tozalash
    cleaned_phone = re.sub(r"[^\+\d]", "", phone).strip()

    # Validatsiya: +998 va 9 ta raqam
    if not re.match(r"^\+998\d{9}$", cleaned_phone):
        await message.answer(
            "❌ Telefon raqam formati noto‘g‘ri",
            reply_markup=phone_request_keyboard(),
            parse_mode=None
        )
        return

    # Ma'lumotlarni olish
    data = await state.get_data()
    telegram_id = message.from_user.id
    username = message.from_user.username or f"user_{telegram_id}"

    # Validatsiya
    if not telegram_id:
        await message.answer("❌ Foydalanuvchi ID topilmadi.")
        await state.finish()
        return
    if not data.get('first_name') or not data.get('last_name'):
        await message.answer("❌ Ism yoki familiya topilmadi. Iltimos, /start bilan qaytadan boshlang.")
        await state.finish()
        return

    # Ro'yxatdan o'tganligini tekshirish
    existing_user = await db.user.find_first(where={"telegramId": telegram_id})
    if existing_user:
        await send_greeting(message, existing_user)
        await state.finish()
        return

    # Foydalanuvchi yaratish
    try:
        await db.user.create({
            "telegramId": telegram_id,
            "username": username,
            "firstName": data['first_name'],
            "lastName": data['last_name'],
            "phone": cleaned_phone,
        })
        await message.answer("✅ Ro‘yxatdan muvaffaqiyatli o‘tdingiz!", reply_markup=main_menu())
        await state.finish()
    except Exception as e:
        await message.answer("❌ Xato yuz berdi. Iltimos, qaytadan urinib ko‘ring.")
        print(f"Xato: {e}")
        await state.finish()