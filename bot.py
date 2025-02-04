import logging
import gspread
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import openai
from datetime import datetime, timedelta

# 🔹 Khai báo API Key và thông tin cần thiết
TELEGRAM_BOT_TOKEN = "7560269155:AAHK_Wdu8mkJhguAkBiU_uqVHI2eYTtUC5U"
OPENAI_API_KEY = "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"
SPREADSHEET_ID = "1b3yCr1_GE47TQTdKc-U5bJFL36aEgTpnpLMGB_0oVgI"
CREDENTIALS_FILE = "credentials.json"  # Tên file xác thực Google Sheets

# 🔹 Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔹 Kết nối Google Sheets
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# 🔹 Cấu hình OpenAI API
openai.api_key = OPENAI_API_KEY

# 🔹 Lãi suất mặc định (có thể thay đổi bằng lệnh /ls <lãi suất>)
CURRENT_INTEREST_RATE = 4000  # 4.000 VND / 1 triệu / ngày

async def start(update: Update, context: CallbackContext) -> None:
    """Lệnh /start để hướng dẫn người dùng nhập khoản vay."""
    await update.message.reply_text(
        "🤖 Xin chào! Tôi là bot quản lý khoản vay.\n"
        "💰 Nhập số tiền, số ngày vay theo định dạng: `50,30`\n"
        "💡 Ví dụ: `50,30` (tức là vay 50 triệu trong 30 ngày)."
    )

async def add_loan(update: Update, context: CallbackContext) -> None:
    """Xử lý khi người dùng nhập khoản vay theo định dạng <số tiền>,<số ngày>."""
    try:
        message_text = update.message.text.strip()
        amount, days = map(float, message_text.split(','))

        amount *= 1_000_000  # Chuyển từ triệu sang đồng
        start_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=int(days))).strftime('%Y-%m-%d')
        interest = (CURRENT_INTEREST_RATE * amount / 1_000_000) * days
        total_payment = amount + interest

        # Ghi dữ liệu vào Google Sheets
        sheet.append_row([
            f"{amount:,.0f}", days, start_date, due_date,
            f"{CURRENT_INTEREST_RATE:,.0f}", f"{interest:,.0f}",
            f"{total_payment:,.0f}", "Chưa trả"
        ])

        # Trả lời người dùng
        await update.message.reply_text(
            f"✅ Khoản vay {amount:,.0f} VND trong {int(days)} ngày đã được ghi nhận!\n"
            f"📅 Ngày đến hạn: {due_date}\n"
            f"💵 Lãi dự kiến: {interest:,.0f} VND\n"
            f"💰 Tổng phải trả: {total_payment:,.0f} VND"
        )
    except:
        await update.message.reply_text("⚠️ Lỗi: Hãy nhập đúng định dạng 💰 <số tiền>,<số ngày> (VD: `50,30`)")

async def set_interest_rate(update: Update, context: CallbackContext) -> None:
    """Lệnh /ls <lãi suất> để cập nhật lãi suất mới."""
    global CURRENT_INTEREST_RATE
    try:
        new_rate = float(context.args[0])
        CURRENT_INTEREST_RATE = new_rate
        await update.message.reply_text(f"✅ Lãi suất mới: {new_rate:,.0f} VND/1 triệu/ngày")
    except:
        await update.message.reply_text("⚠️ Lỗi: Hãy nhập lãi suất hợp lệ. Ví dụ: `/ls 5000`")

async def main() -> None:
    """Khởi động bot Telegram."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ls", set_interest_rate))
    application.add_handler(MessageHandler(filters.Regex(r'^\d+,\d+$'), add_loan))

    print("🚀 Bot Telegram đang chạy...")
    await application.run_polling()

# Chạy bot
if __name__ == "__main__":
    import sys
    import asyncio

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            pass  # Bỏ qua lỗi vòng lặp đang chạy

