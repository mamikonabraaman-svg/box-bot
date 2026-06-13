ssage.reply_text(f"📦 Введите количество штук (минимум {MIN_QTY}):")
        return INPUT_QTY
    except ValueError:
        await update.message.reply_text("❌ Введите числовое значение:")
        return INPUT_D
async def input_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = int(update.message.text.replace(",", ".").split(".")[0])
        if qty < MIN_QTY:
            await update.message.reply_text(f"❌ Минимальное количество {MIN_QTY} шт. Введите снова:")
            return INPUT_QTY
        fmt = context.user_data["format"]
        L = context.user_data["L"]
        W = context.user_data["W"]
        D = context.user_data["D"]
        area = calc_area(fmt, L, W, D)
        if area > MAX_AREA:
            await update.message.reply_text(
                "❌ Размеры слишком большие. Пожалуйста, начните заново /start"
            )
            return ConversationHandler.END
        price_per_box = calc_price(area, qty)
        total = price_per_box * qty
        result = (
            f"✅ Расчёт готов!\n\n"
            f"📦 Формат: {fmt}\n"
            f"📏 Размеры: {L:.0f} × {W:.0f} × {D:.0f} мм\n"
            f"🔢 Количество: {qty} шт\n"
            f"📐 Площадь заготовки: {area:.0f} мм²\n\n"
            f"💰 Цена за штуку: {price_per_box:.2f} руб\n"
            f"💵 Итого: {total:.2f} руб\n\n"
            f"Для нового расчёта нажмите /start"
        )
        await update.message.reply_text(result)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Введите целое число:")
        return INPUT_QTY
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "❌ Расчёт отменён. Нажмите /start для начала.",
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
    logger.info
("Бот запущен...")
    app.run_polling()
if __name__ == "__main__":
    main()
