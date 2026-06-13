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

TOKEN = os.getenv("BOT_TOKEN", "")

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


def get_price_per_mm2(qty):
    if qty >= 1000:
        return 0.00013
    elif qty >= 300:
        return 0.00015
    else:
        return 0.00016


def calc_area(fmt, L, W, D):
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


def calc_price(area, qty):
    price_per_box = area * get_price_per_mm2(qty)
    if price_per_box < MIN_PRICE:
        price_per_box = MIN_PRICE
    return price_per_box


async def start(update, context):
    keyboard = [[fmt] for fmt in FORMATS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я помогу рассчитать стоимость картонной коробки.\n\nВыберите формат коробки:",
        reply_markup=reply_markup
    )
    return SELECT_FORMAT


async def select_format(update, context):
    fmt = update.message.text
    if fmt not in FORMATS:
        await update.message.reply_text("Пожалуйста, выберите формат из списка.")
        return SELECT_FORMAT
    context.user_data["format"] = fmt
    await update.message.reply_text(
        "Выбран формат: " + fmt + "\n\nВведите длину L в мм (минимум 30):",
        reply_markup=ReplyKeyboardRemove()
    )
    return INPUT_L


async def input_l(update, context):
    try:
        L = float(update.message.text.replace(",", "."))
        if L < MIN_L:
            await update.message.reply_text("Минимальная длина 30 мм. Введите снова:")
            return INPUT_L
        context.user_data["L"] = L
        await update.message.reply_text("Введите ширину W в мм (минимум 30):")
        return INPUT_W
    except ValueError:
        await update.message.reply_text("Введите числовое значение:")
        return INPUT_L


async def input_w(update, context):
    try:
        W = float(update.message.text.replace(",", "."))
        if W < MIN_W:
            await update.message.reply_text("Минимальная ширина 30 мм. Введите снова:")
            return INPUT_W
        context.user_data["W"] = W
        await update.message.reply_text("Введите высоту D в мм (минимум 20):")
        return INPUT_D
    except ValueError:
        await update.message.reply_text("Введите числовое значение:")
        return INPUT_W


async def input_d(update, context):
    try:
        D = float(update.message.text.replace(",", "."))
        if D < MIN_D:
            await update.message.reply_text("Минимальная высота 20 мм. Введите снова:")
            return INPUT_D
        context.user_data["D"] = D
        await update.message.reply_text("Введите количество штук (минимум 100):")
        return INPUT_QTY
    except ValueError:
        await update.message.reply_text("Введите числовое значение:")
        return INPUT_D


async def input_qty(update, context):
    try:
        qty = int(float(update.message.text.replace(",", ".")))
        if qty < MIN
        fmt = context.user_data["format"]
        L = context.user_data["L"]
        W = context.user_data["W"]
        D = context.user_data["D"]
        area = calc_area(fmt, L, W, D)
        if area > MAX_AREA:
            await update.message.reply_text("Размеры слишком большие. Начните заново /start")
            return ConversationHandler.END
        price_per_box = calc_price(area, qty)
        total = price_per_box * qty
        result = (
            "Расчёт готов!\n\n"
            "Формат: " + fmt + "\n"
            "Размеры: " + str(int(L)) + " x " + str(int(W)) + " x " + str(int(D)) + " мм\n"
            "Количество: " + str(qty) + " шт\n"
            "Площадь заготовки: " + str(int(area)) + " мм2\n\n"
            "Цена за штуку: " + str(round(price_per_box, 2)) + " руб\n"
            "Итого: " + str(round(total, 2)) + " руб\n\n"
            "Для нового расчёта нажмите /start"
        )
        await update.message.reply_text(result)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Введите целое число:")
        return INPUT_QTY


async def cancel(update, context):
    await update.message.reply_text(
        "Расчёт отменён. Нажмите /start для начала.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_FORMAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_format)],
            INPUT_L: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_l)],
            INPUT_W: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_w)],
            INPUT_D: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_d)],
            INPUT_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_qty)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
