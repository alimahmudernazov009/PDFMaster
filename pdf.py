import os
import img2pdf
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- SOZLAMALAR ---
TOKEN = "8579089955:AAFIDdY6qOE7BG8o4jqYRPoNRwQmYrA88Ys"
bot = Bot(token=TOKEN)
dp = Dispatcher()
user_data = {}

# --- KLAVIATURALAR ---
def get_start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🖼 Rasm tanlash")]],
        resize_keyboard=True
    )

def get_pdf_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ PDF-ni yakunlash", callback_data="make_pdf")]
    ])

# --- BOT HANDLERLARI ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {'images': [], 'last_msg_id': None, 'processing': False}
    await message.answer("Salom! PDF yaratish uchun rasmlarni yuboring.", reply_markup=get_start_keyboard())

@dp.message(F.text == "🖼 Rasm tanlash")
async def rasm_tanlash(message: types.Message):
    await message.answer("👇 Pastdagi skrepka (📎) belgisini bosing va rasmlarni tanlang!")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'images': [], 'last_msg_id': None, 'processing': False}

    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = f"{file_id}.jpg"
    await bot.download_file(file.file_path, file_path)
    user_data[user_id]['images'].append(file_path)
    
    if not user_data[user_id]['processing']:
        user_data[user_id]['processing'] = True
        await asyncio.sleep(1.5)
        
        if user_data[user_id]['last_msg_id']:
            try: await bot.delete_message(message.chat.id, user_data[user_id]['last_msg_id'])
            except: pass

        sent_msg = await message.answer(
            f"✅ {len(user_data[user_id]['images'])} ta rasm tayyor.",
            reply_markup=get_pdf_inline_keyboard()
        )
        user_data[user_id]['last_msg_id'] = sent_msg.message_id
        user_data[user_id]['processing'] = False

@dp.callback_query(F.data == "make_pdf")
async def finalize_pdf(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_data or not user_data[user_id]['images']:
        await callback.answer("Rasm yo'q!", show_alert=True)
        return

    await callback.message.edit_text("⏳ PDF tayyorlanmoqda...")
    pdf_name = f"result_{user_id}.pdf"
    
    try:
        with open(pdf_name, "wb") as f:
            f.write(img2pdf.convert(user_data[user_id]['images']))
        
        await callback.message.answer_document(FSInputFile(pdf_name), caption="📚 Marhamat!")
        
        for img in user_data[user_id]['images']: 
            if os.path.exists(img): os.remove(img)
        if os.path.exists(pdf_name): os.remove(pdf_name)
        
        await callback.message.delete()
        del user_data[user_id]
    except Exception as e:
        await callback.message.answer(f"Xato yuz berdi: {e}")

# --- RENDER UCHUN PORT OCHISH ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    # Serverni ishga tushirish (Koyeb uchun)
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # Botni ishga tushirish (aiogram 3.x uchun to'g'ri yo'l)
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
