import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
TOKEN = os.getenv("BOT_TOKEN", "8863654292:AAFvshUDHU8Tb7dGbfx3o5sgteEBKtkD70g")
SELECT_FORMAT, INPUT_L, INPUT_W, INPUT_D, INPUT_QTY = range(5)
FORMATS = {
    "FEFCO 0201": "Стандартная коробка",
    "FEFCO 0211-1": "Двухклапанная",
    "FEFCO 0426": "Самосборная",
    "FEFCO 0427": "Самосборная с замками (0427)",
    "FEFCO 0471": "Самосборная с замками (0471)",
}
MIN_L = 30
MIN_W = 30
MIN_D = 20
MIN_QTY = 100
MAX_AREA = 1_040_000
MIN_PRICE = 5.0
def get_price_per_mm2(qty: int) -> float:
    if qty >= 1000:
        return 0.00013
    elif qty >= 300:
        return 0.00015
    else:
        return 0.00016
def calc_area(fmt: str, L: float, W: float, D: float) -> float:
    if fmt == "FEFCO 0201":
        return (21 + 2*L + 2*W) * (D + W)
    elif fmt == "FEFCO 0211-1":
        return (15 + 2*L + 2*W) * (2*(20+W) + D)
    elif fmt == "FEFCO 0426":
        return (4*D + 2*W + 2) * (2*D + L)
    elif fmt == "FEFCO 0427":
        return (4 + 4*D + L) * (3*D + 2*W)
    elif fmt == "FEFCO 0471":
        return 2 * L * (20 + 3*D + 2*W)
    return 0
def calc_price(area: float, qty: int) -> float:
    price_per_box = area * get_price_per_mm2(qty)
    if price_per_box < MIN_PRICE:
        price_per_box = MIN_PRICE
    return price_per_box
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[fmt] for fmt in FORMATS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Привет! Я помогу рассчитать стоимость картонной коробки.\n\n"
        "📦 Выберите формат коробки:",
        reply_markup=reply_markup
    )
    return SELECT_FORMAT
async def select_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    fmt = update.message.text
    if fmt not in FORMATS:
        await update.message.reply_text("❌ Пожалуйста, выберите формат из списка.")
        return SELECT_FORMAT
    context.user_data["format"] = fmt
    await update.message.reply_text(
        f"✅ Выбран формат: {fmt} — {FORMATS[fmt]}\n\n"
        f"📏 Введите длину (L) в мм (минимум {MIN_L} мм):",
        reply_markup=ReplyKeyboardRemove()
    )
    return INPUT_L
async def input_l(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        L = float(update.message.text.replace(",", "."))
        if L < MIN_L:
            await update.message.reply_text(f"❌ Минимальная длина {MIN_L} мм. Введите снова:")
            return INPUT_L
        context.user_data["L"] = L
        await update.message.reply_text(f"📏 Введите ширину (W) в мм (минимум {MIN_W} мм):")
        return INPUT_W
    except ValueError:
        await update.message.reply_text("❌ Введите числовое значение:")
        return INPUT_L
async def input_w(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        W = float(update.message.text.replace(",", "."))
        if W < MIN_W:
            await update.message.reply_text(f"❌ Минимальная ширина {MIN_W} мм. Введите снова:")
            return INPUT_W
        context.user_data["W"] = W
        await update.message.reply_text(f"📏 Введите высоту (D) в мм (минимум {MIN_D} мм):")
        return INPUT_D
    except ValueError:
        await update.message.reply_text("❌ Введите числовое значение:")
        return INPUT_W
async def input_d(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        D = float(update.message.text.replace(",", "."))
        if D < MIN_D:
            await update.message.reply_text(f"❌ Минимальная высота {MIN_D} мм. Введите снова:")
            return INPUT_D
        fmt
