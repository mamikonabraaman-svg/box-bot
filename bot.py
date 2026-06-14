import logging
import os
from telegram import Update, ReplyKeyboardRemove
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

INPUT_DIMS, INPUT_QTY = range(2)

FORMATS = {
    "FEFCO 0201": "Обычная коробка",
    "FEFCO 0211-1": "Двухклапанная коробка",
    "FEFCO 0426": "Самосборная коробка",
    "FEFCO 0427": "Самосборная коробка с замками",
    "FEFCO 0471": "Самосборная коробка (усиленная)",
}

MIN_L = 30
MIN_W = 30
MIN_D = 20
MIN_QTY = 100

MAX_SIDE_1 = 1200  # максимальная длина развёртки
MAX_SIDE_2 = 800   # максимальная ширина развёртки

MIN_PRICE = 5.0

CONTACT_INFO = (
    "\n🌐 Для оформления заказа:\n"
    "Сайт: dilmakrd.ru\n"
    "📞 Телефон: +7 918 631 20 56"
)


def get_price_per_mm2(qty):
    if qty >= 1000:
        return 0.00013
    elif qty >= 300:
        return 0.00015
    else:
        return 0.00016


def get_blank_size(fmt, L, W, D):
    """Возвращает (сторона1, сторона2) развёртки для формата"""
    if fmt == "FEFCO 0201":
        s1 = 2 * L + 2 * W + 21
        s2 = D + W
        return s1, s2
    elif fmt == "FEFCO 0211-1":
        s1 = 2 * L + 2 * W + 15
        s2 = 2 * (20 + W) + D
        return s1, s2
    elif fmt == "FEFCO 0426":
        s1 = 2 * D + L
        s2 = 4 * D + 2 * W + 2
        return s1, s2
    elif fmt == "FEFCO 0427":
        s1 = 4 + 4 * D + L
        s2 = 3 * D + 2 * W
        return s1, s2
    elif fmt == "FEFCO 0471":
        s1 = 2 * L
        s2 = 20 + 3 * D + 2 * W
        return s1, s2
    return 0, 0


def is_blank_ok(s1, s2):
    """Проверяет вписывается ли развёртка в 1200x800 (в любой ориентации)"""
    if (s1 <= MAX_SIDE_1 and s2 <= MAX_SIDE_2):
        return True
    if (s1 <= MAX_SIDE_2 and s2 <= MAX_SIDE_1):
        return True
    return False


def calc_area(s1, s2):
    return s1 * s2


def calc_price(area, qty):
    price_per_box = area * get_price_per_mm2(qty)
    if price_per_box < MIN_PRICE:
        price_per_box = MIN_PRICE
    return price_per_box


async def start(update, context):
    await update.message.reply_text(
        "Привет! Я рассчитаю стоимость коробки по всем форматам.\n\n"
        "Введите размеры через пробел:\n"
        "Длина Ширина Высота (в мм)\n\n"
        "Пример: 300 200 150"
    )
    return INPUT_DIMS


async def input_dims(update, context):
    try:
        parts = update.message.text.replace(",", ".").split()
        if len(parts) != 3:
            await update.message.reply_text(
                "Нужно ввести три числа через пробел.\n"
                "Пример: 300 200 150"
            )
            return INPUT_DIMS

        L, W, D = float(parts[0]), float(parts[1]), float(parts[2])

        if L < MIN_L:
            await update.message.reply_text("Длина должна быть минимум 30 мм. Введите снова:")
            return INPUT_DIMS
        if W < MIN_W:
            await update.message.reply_text("Ширина должна быть минимум 30 мм. Введите снова:")
            return INPUT_DIMS
        if D < MIN_D:
            await update.message.reply_text("Высота должна быть минимум 20 мм. Введите снова:")
            return INPUT_DIMS

        context.user_data["L"] = L
        context.user_data["W"] = W
        context.user_data["D"] = D

        await update.message.reply_text(
            "Размеры: " + str(int(L)) + " x " + str(int(W)) + " x " + str(int(D)) + " мм\n\n"
            "Введите количество штук (минимум 100):"
        )
        return INPUT_QTY

    except ValueError:
        await update.message.reply_text(
            "Введите три числа через пробел.\n"
            "Пример: 300 200 150"
        )
        return INPUT_DIMS


async def input_qty(update, context):
    try:
        qty = int(float(update.message.text.replace(",", ".")))

        if qty < MIN_QTY:
            await update.message.reply_text("Минимальное количество 100 шт. Введите снова:")
            return INPUT_QTY

        L = context.user_data["L"]
        W = context.user_data["W"]
        D = context.user_data["D"]

        result = (
            "📦 Размеры: " +
            str(int(L)) + " x " + str(int(W)) + " x " + str(int(D)) + " мм\n"
            "Количество: " + str(qty) + " шт\n"
            "─────────────────────\n"
        )

        for fmt, description in FORMATS.items():
            s1, s2 = get_blank_size(fmt, L, W, D)

            if not is_blank_ok(s1, s2):
                result += (
                    "📌 " + fmt + "\n"
                    "▫️ " + description + "\n"
                    "⛔ Не можем изготовить — развёртка превышает 1200 x 800 мм\n"
                    "─────────────────────\n"
                )
                continue

            area = calc_area(s1, s2)
            price_per_box = calc_price(area, qty)
            total = price_per_box * qty

            result += (
                "📌 " + fmt + "\n"
                "▫️ " + description + "\n"
                "Цена за шт: " + str(round(price_per_box, 2)) + " руб\n"
                "Итого: " + str(round(total, 2)) + " руб\n"
                "─────────────────────\n"
            )

        result += CONTACT_INFO
        result += "\n\nДля нового расчёта нажмите /start"

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
            INPUT_DIMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_dims)],
            INPUT_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_qty)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
