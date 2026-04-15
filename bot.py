from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

TOKEN = os.getenv("8697150456:AAG3XFoicVatIkqpNc1WiPxgaYyB3n_RSns")
ADMIN_ID = 584607403

# Цена указана за 1 бутылку / 1 штуку
products = {
    "Tassay Energy Оригинал 0.45": {"price": 458, "pack_size": 12},
    "Tassay Energy Гранат 0.45": {"price": 458, "pack_size": 12},
    "Tassay Energy Персик 0.45": {"price": 458, "pack_size": 12},
    "Tassay Cola 1.0": {"price": 375, "pack_size": 6},
    "Tassay Cola 2.0": {"price": 458, "pack_size": 6},
    "Tassay Вода 1.0 газ": {"price": 375, "pack_size": 6},
    "Tassay Вода 1.0 негаз": {"price": 375, "pack_size": 6},
    "Tassay Вода 1.5 газ": {"price": 458, "pack_size": 6},
    "Tassay Вода 1.5 негаз": {"price": 458, "pack_size": 6},
    "Tassay Вода 5.0": {"price": 625, "pack_size": 2},
    "Holiday Limonade 1.0": {"price": 500, "pack_size": 6},
    "Holiday Limonade 1.5": {"price": 625, "pack_size": 6},
    "Holiday Limonade 2.0": {"price": 708, "pack_size": 6},
    "Holiday Limonade 2.5": {"price": 750, "pack_size": 6},
}

ADDRESS, PHONE, PRODUCT, QUANTITY, NEXT_ACTION, CONFIRM, DELETE_ITEM = range(7)


def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["Оформить заказ", "Прайс"],
            ["Контакты"],
        ],
        resize_keyboard=True
    )


def product_menu():
    buttons = [[name] for name in products.keys()]
    buttons.append(["Отмена"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def next_menu():
    return ReplyKeyboardMarkup(
        [
            ["Добавить еще товар"],
            ["Показать корзину", "Удалить позицию"],
            ["Очистить корзину", "Подтвердить заказ"],
            ["Отмена"],
        ],
        resize_keyboard=True
    )


def contact_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📞 Отправить номер телефона", request_contact=True)],
            ["Отмена"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def format_price():
    if not products:
        return "Прайс пока пуст."

    lines = []
    for name, data in products.items():
        price = data["price"]
        pack_size = data["pack_size"]
        lines.append(f"{name} — {price} тг/шт (в упаковке {pack_size} бутылок)")

    return "Прайс:\n(цена указана за 1 бутылку / 1 штуку)\n\n" + "\n".join(lines)


def format_cart(cart):
    if not cart:
        return "Корзина пуста."

    lines = []
    total = 0

    for i, item in enumerate(cart, start=1):
        item_sum = item["packs"] * item["pack_size"] * item["price"]
        total += item_sum
        lines.append(
            f"{i}) {item['name']} — {item['packs']} упак. × {item['pack_size']} бутылок × {item['price']} тг = {item_sum} тг"
        )

    lines.append(f"\nИтого: {total} тг")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте!\n\n"
        "Вас приветствует ТОО «ТД Фэст Реал».\n"
        "Мы занимаемся доставкой напитков по городу Уральск.\n\n"
        "В этом боте вы можете посмотреть прайс и оформить заказ.",
        reply_markup=main_menu()
    )


async def show_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_price(), reply_markup=main_menu())


async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ТОО «ТД Фэст Реал»\n"
        "Контактный номер: +7 775 412 31 12",
        reply_markup=main_menu()
    )


async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cart"] = []
    context.user_data.pop("phone", None)
    await update.message.reply_text(
        "Укажите адрес доставки:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()

    if address == "Отмена":
        await update.message.reply_text("Заказ отменен.", reply_markup=main_menu())
        return ConversationHandler.END

    context.user_data["address"] = address

    await update.message.reply_text(
        "Пожалуйста, отправьте ваш номер телефона кнопкой ниже.\n"
        "Без номера оформить заказ нельзя.",
        reply_markup=contact_menu()
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.strip() == "Отмена":
        await update.message.reply_text("Заказ отменен.", reply_markup=main_menu())
        return ConversationHandler.END

    contact = update.message.contact

    if not contact:
        await update.message.reply_text(
            "Пожалуйста, отправьте номер телефона именно кнопкой ниже.",
            reply_markup=contact_menu()
        )
        return PHONE

    if contact.user_id and contact.user_id != update.effective_user.id:
        await update.message.reply_text(
            "Пожалуйста, отправьте свой собственный номер телефона.",
            reply_markup=contact_menu()
        )
        return PHONE

    context.user_data["phone"] = contact.phone_number

    await update.message.reply_text(
        "Спасибо. Теперь выберите товар:",
        reply_markup=product_menu()
    )
    return PRODUCT


async def phone_text_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Отмена":
        await update.message.reply_text("Заказ отменен.", reply_markup=main_menu())
        return ConversationHandler.END

    await update.message.reply_text(
        "Для оформления заказа нужно отправить номер телефона кнопкой ниже.",
        reply_markup=contact_menu()
    )
    return PHONE


async def get_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Отмена":
        await update.message.reply_text("Заказ отменен.", reply_markup=main_menu())
        return ConversationHandler.END

    if text not in products:
        await update.message.reply_text("Пожалуйста, выберите товар кнопкой.")
        return PRODUCT

    context.user_data["selected_product"] = text
    pack_size = products[text]["pack_size"]

    await update.message.reply_text(
        f"Введите количество упаковок для товара:\n{text}\n"
        f"В 1 упаковке: {pack_size} бутылок",
        reply_markup=ReplyKeyboardRemove()
    )
    return QUANTITY


async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("Введите количество упаковок цифрами. Например: 2")
        return QUANTITY

    packs = int(text)
    if packs <= 0:
        await update.message.reply_text("Количество упаковок должно быть больше нуля.")
        return QUANTITY

    product_name = context.user_data["selected_product"]
    product_data = products[product_name]

    context.user_data["cart"].append({
        "name": product_name,
        "packs": packs,
        "price": product_data["price"],
        "pack_size": product_data["pack_size"],
    })

    await update.message.reply_text(
        "Товар добавлен в корзину.\n\n"
        f"{format_cart(context.user_data['cart'])}\n\n"
        "Что дальше?",
        reply_markup=next_menu()
    )
    return NEXT_ACTION


async def next_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    cart = context.user_data.get("cart", [])

    if text == "Добавить еще товар":
        await update.message.reply_text(
            "Выберите следующий товар:",
            reply_markup=product_menu()
        )
        return PRODUCT

    if text == "Показать корзину":
        await update.message.reply_text(
            f"Ваш заказ:\n\n{format_cart(cart)}",
            reply_markup=next_menu()
        )
        return NEXT_ACTION

    if text == "Удалить позицию":
        if not cart:
            await update.message.reply_text(
                "Корзина пуста.",
                reply_markup=next_menu()
            )
            return NEXT_ACTION

        await update.message.reply_text(
            "Введите номер позиции для удаления.\n\n"
            f"{format_cart(cart)}",
            reply_markup=ReplyKeyboardRemove()
        )
        return DELETE_ITEM

    if text == "Очистить корзину":
        context.user_data["cart"] = []
        await update.message.reply_text(
            "Корзина очищена.",
            reply_markup=next_menu()
        )
        return NEXT_ACTION

    if text == "Подтвердить заказ":
        if not cart:
            await update.message.reply_text(
                "Корзина пуста. Сначала добавьте товар.",
                reply_markup=next_menu()
            )
            return NEXT_ACTION

        summary = (
            "Проверьте заказ:\n\n"
            f"Телефон: {context.user_data.get('phone', 'не указан')}\n"
            f"Адрес: {context.user_data['address']}\n\n"
            f"{format_cart(cart)}\n\n"
            "Подтвердить?"
        )
        confirm_keyboard = ReplyKeyboardMarkup(
            [["Подтвердить", "Отмена"]],
            resize_keyboard=True
        )
        await update.message.reply_text(summary, reply_markup=confirm_keyboard)
        return CONFIRM

    if text == "Отмена":
        await update.message.reply_text("Заказ отменен.", reply_markup=main_menu())
        return ConversationHandler.END

    await update.message.reply_text("Выберите один из вариантов кнопкой.")
    return NEXT_ACTION


async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    cart = context.user_data.get("cart", [])

    if not cart:
        await update.message.reply_text(
            "Корзина пуста.",
            reply_markup=next_menu()
        )
        return NEXT_ACTION

    if not text.isdigit():
        await update.message.reply_text(
            "Введите номер позиции цифрами. Например: 1",
            reply_markup=ReplyKeyboardRemove()
        )
        return DELETE_ITEM

    index = int(text) - 1

    if index < 0 or index >= len(cart):
        await update.message.reply_text(
            "Такой позиции нет. Введите номер из корзины.",
            reply_markup=ReplyKeyboardRemove()
        )
        return DELETE_ITEM

    deleted_item = cart.pop(index)
    context.user_data["cart"] = cart

    if not cart:
        await update.message.reply_text(
            f"Позиция «{deleted_item['name']}» удалена.\n\nКорзина теперь пуста.",
            reply_markup=next_menu()
        )
        return NEXT_ACTION

    await update.message.reply_text(
        f"Позиция «{deleted_item['name']}» удалена.\n\n"
        f"Обновленная корзина:\n\n{format_cart(cart)}",
        reply_markup=next_menu()
    )
    return NEXT_ACTION


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Отмена":
        await update.message.reply_text("Заказ отменен.", reply_markup=main_menu())
        return ConversationHandler.END

    if text != "Подтвердить":
        await update.message.reply_text("Нажмите «Подтвердить» или «Отмена».")
        return CONFIRM

    user = update.effective_user
    address = context.user_data["address"]
    phone = context.user_data.get("phone", "не указан")
    cart = context.user_data.get("cart", [])

    if not cart:
        await update.message.reply_text(
            "Корзина пуста. Заказ отменен.",
            reply_markup=main_menu()
        )
        return ConversationHandler.END

    total = sum(item["packs"] * item["pack_size"] * item["price"] for item in cart)
    username = f"@{user.username}" if user.username else "не указан"

    order_text = (
        "Новый заказ\n\n"
        f"Клиент: {user.full_name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user.id}\n"
        f"Телефон: {phone}\n\n"
        f"Адрес: {address}\n\n"
        f"{format_cart(cart)}\n\n"
        f"Общая сумма: {total} тг"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=order_text)

    await update.message.reply_text(
        "Спасибо! Ваш заказ принят.\n"
        "Мы свяжемся с вами при необходимости.",
        reply_markup=main_menu()
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=main_menu()
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()

    order_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Оформить заказ$"), order_start)
        ],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            PHONE: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone_text_fallback),
            ],
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            NEXT_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, next_action)],
            DELETE_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_item)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^Отмена$"), cancel),
        ],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^Прайс$"), show_price))
    app.add_handler(MessageHandler(filters.Regex("^Контакты$"), contacts))
    app.add_handler(order_handler)

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_server).start()