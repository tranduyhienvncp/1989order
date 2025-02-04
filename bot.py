import logging
import os
import gspread
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import openai
from datetime import datetime, timedelta
import json

# Cấu hình logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Đọc token từ biến môi trường
TELEGRAM_BOT_TOKEN = os.getenv("7560269155:AAHK_Wdu8mkJhguAkBiU_uqVHI2eYTtUC5U")
OPENAI_API_KEY = os.getenv("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")
SPREADSHEET_ID = os.getenv("1b3yCr1_GE47TQTdKc-U5bJFL36aEgTpnpLMGB_0oVgI")
GOOGLE_CREDENTIALS_JSON = os.getenv("credentials.json")

# Đọc Google API Credentials từ biến môi trường
creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, 
    ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
)
client = gspread.authorize(creds)

# Mở Google Sheet
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Cấu hình OpenAI API
openai.api_key = OPENAI_API_KEY

# Lãi suất mặc định (VND/1 triệu/ngày)
CURRENT_INTEREST_RATE = 4000

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Xin chào! Tôi là bot quản lý khoản vay của bạn.")

async def add_loan(update: Update, context: CallbackContext) -> None:
    try:
        message_text = update.message.text.strip()
        if not message_text or ',' not in message_text:
            await update.message.reply_text("⚠️ Sai định dạng! Hãy nhập: <số tiền>,<số ngày>")
            return

        amount, days = map(float, message_text.split(','))
        amount *= 1_000_000  # Chuyển từ triệu sang đồng
        start_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=int(days))).strftime('%Y-%m-%d')
        interest = (CURRENT_INTEREST_RATE * amount / 1_000_000) * days
        total_payment = amount + interest

        sheet.append_row([f"{amount:,.0f}", days, start_date, due_date, f"{interest:,.0f}", f"{total_payment:,.0f}", "Chưa trả"])
        
        await update.message.reply_text(f"✅ Đã ghi nhận khoản vay {amount:,.0f} VND.")
    except Exception as e:
        await update.message.reply_text("❌ Có lỗi xảy ra.")
        logger.error(f"Lỗi khi ghi khoản vay: {e}")

async def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex(r'^\d+,\d+$'), add_loan))

    print("🚀 Bot đang chạy trên Render...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
