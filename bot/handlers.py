"""
Telegram bot handlers - Clean version without merge conflicts
"""
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from datetime import datetime, timedelta
import os
import re
import aiohttp
import asyncio

router = Router()

# Admin IDs - replace with actual admin IDs
ADMIN_IDS = [448592121]  # Replace with actual admin IDs

# CryptoPay API configuration
CRYPTOPAY_TOKEN = "479115:AARxfBgUT3h1n9oBCwY1Y3UbgwN1n6S9mHn"
CRYPTOPAY_API_URL = "https://pay.crypt.bot/api"

# Subscription prices and durations
SUBSCRIPTION_PLANS = {
    "1_day": {"price": 1.0, "days": 1, "text": "1 день - $1"},
    "7_days": {"price": 3.0, "days": 7, "text": "7 днів - $3"},
    "14_days": {"price": 5.0, "days": 14, "text": "14 днів - $5"},
    "30_days": {"price": 7.0, "days": 30, "text": "30 днів - $7"},
    "lifetime": {"price": 15.0, "days": 99999, "text": "Назавжди - $15"}
}


class RegistrationStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_birth_date = State()
    waiting_for_photo = State()
    waiting_for_login = State()
    waiting_for_password = State()
    preview = State()  # Предпросмотр данных перед сохранением


class TicketStates(StatesGroup):
    waiting_for_ticket_message = State()


async def create_cryptopay_invoice(user_id: int, amount: float, currency: str = "USDT", description: str = "") -> dict:
    """Create invoice in CryptoPay"""
    url = f"{CRYPTOPAY_API_URL}/createInvoice"
    
    payload = {
        "asset": currency,
        "amount": str(amount),
        "description": description,
        "hidden_message": f"Payment for user {user_id}",
        "paid_btn_name": "openBot",
        "paid_btn_url": "https://t.me/maijediiabot",
        "payload": str(user_id)
    }
    
    headers = {
        "Crypto-Pay-API-Token": CRYPTOPAY_TOKEN
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                if data.get("ok"):
                    return data.get("result", {})
                else:
                    print(f"CryptoPay error: {data}")
                    return None
    except Exception as e:
        print(f"CryptoPay exception: {e}")
        return None


async def check_invoice_status(invoice_id: int) -> dict:
    """Check invoice payment status in CryptoPay"""
    url = f"{CRYPTOPAY_API_URL}/getInvoices"
    
    payload = {
        "invoice_ids": str(invoice_id)
    }
    
    headers = {
        "Crypto-Pay-API-Token": CRYPTOPAY_TOKEN
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                if data.get("ok") and data.get("result", {}).get("items"):
                    return data["result"]["items"][0]
                return None
    except Exception as e:
        print(f"CryptoPay check error: {e}")
        return None


@router.message(Command("start"))
async def cmd_start(message: Message, db):
    """Handle /start command"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if user:
        await message.answer(
            "✅ Ви вже зареєстровані!\n\n"
            "Використовуйте команду /menu для переміщення в меню бота."
        )
    else:
        await message.answer(
            "✅ Ви успішно прийняли умови використання нашого застосунку.\n"
            "Дякуємо та вітаємо Вас!\n\n"
            "Використовуйте команду /menu для переміщення в меню бота."
        )


@router.message(Command("menu"))
async def cmd_menu(message: Message, db):
    """Handle /menu command"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Почати реєстрацію", callback_data="start_registration")]
        ])
        
        await message.answer(
            "✨ Вітаємо в головному меню, оберіть потрібний пункт.\n\n"
            "🛑 Ваш профіль пустий",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Профіль", callback_data="profile")],
            [InlineKeyboardButton(text="📲 Завантажити застосунок", callback_data="download_app")],
            [InlineKeyboardButton(text="💎 Придбати підписку", callback_data="buy_subscription")],
            [InlineKeyboardButton(text="❓ Допомога", callback_data="help")],
            [InlineKeyboardButton(text="⚙️ Налаштування", callback_data="settings")]
        ])
        
        await message.answer(
            "✨ Вітаємо в головному меню, оберіть потрібний пункт.",
            reply_markup=keyboard
        )


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, db):
    """Show user profile"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Помилка: профіль не знайдено", show_alert=True)
        return
    
    last_login = user['last_login'] if user['last_login'] else "Ніколи"
    if last_login != "Ніколи":
        try:
            dt = datetime.fromisoformat(last_login)
            last_login = dt.strftime("%d.%m.%Y о %H:%M")
        except:
            pass
    
    subscription_status = "✅ Активна" if user['subscription_active'] else "❌ Неактивна"
    subscription_until = user['subscription_until'] if user['subscription_until'] else "—"
    
    profile_text = (
        "👤 Профіль\n\n"
        f"👼 ПІБ: {user['full_name']}\n"
        f"🗓️ Дата народження: {user['birth_date']}\n"
        f"📲 Останній вхід в застосунок о: {last_login}\n"
        f"🌝 Стан підписки: {subscription_status}\n"
        f"🌀 Тип підписки: {user['subscription_type']}\n"
        f"🎫 Підписка дійсна до: {subscription_until}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Змінити інформацію", callback_data="edit_profile")],
        [InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(profile_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "edit_profile")
async def edit_profile(callback: CallbackQuery, state: FSMContext, db):
    """Start profile editing (re-registration)"""
    await db.clear_registration_state(callback.from_user.id)
    await callback.message.edit_text(
        "💻 Почнемо заповнювати інформацію про Вас.\n\n"
        "1) Напишіть ваше ПІБ в такому форматі:\n"
        "Маск Ілон Максимович"
    )
    await state.set_state(RegistrationStates.waiting_for_full_name)
    await db.save_registration_state(callback.from_user.id, "waiting_for_full_name", {"is_editing": True})
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Return to main menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профіль", callback_data="profile")],
        [InlineKeyboardButton(text="📲 Завантажити застосунок", callback_data="download_app")],
        [InlineKeyboardButton(text="💎 Придбати підписку", callback_data="buy_subscription")],
        [InlineKeyboardButton(text="❓ Допомога", callback_data="help")],
        [InlineKeyboardButton(text="⚙️ Налаштування", callback_data="settings")]
    ])
    
    await callback.message.edit_text(
        "✨ Вітаємо в головному меню, оберіть потрібний пункт.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "download_app")
async def download_app(callback: CallbackQuery, db):
    """Download app"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Спочатку зареєструйтесь!", show_alert=True)
        return
    
    # Check if user has active subscription
    if not user.get('subscription_active', False):
        await callback.answer(
            "❌ У вас немає активної підписки. Придбайте підписку для завантаження застосунку.",
            show_alert=True
        )
        return
    
    # Get IPA URL from Cloudinary (set in environment variable)
    ipa_url = os.getenv("IPA_CLOUDINARY_URL")
    
    if not ipa_url:
        await callback.answer(
            "❌ Застосунок тимчасово недоступний. Зверніться до адміністратора.",
            show_alert=True
        )
        return
    
    try:
        # Send download link with instructions
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Завантажити IPA", url=ipa_url)],
            [InlineKeyboardButton(text="📖 Інструкція по встановленню", callback_data="install_guide")],
            [InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="back_to_menu")]
        ])
        
        await callback.message.edit_text(
            "📲 <b>Завантаження застосунку Майже Дія</b>\n\n"
            "✅ Ваша підписка активна!\n\n"
            "📋 <b>Кроки для встановлення:</b>\n"
            "1️⃣ Натисніть кнопку нижче для завантаження .ipa файлу\n"
            "2️⃣ Встановіть через Sideloadly, AltStore або інший додаток\n"
            "3️⃣ Після встановлення запустіть застосунок\n"
            "4️⃣ Увійдіть використовуючи свій логін і пароль\n"
            "5️⃣ Перезапустіть застосунок для коректної роботи\n\n"
            "⚠️ <b>Важливо:</b> Для входу використовуйте логін і пароль, які ви створили при реєстрації в боті",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(
            f"❌ Помилка: {str(e)}",
            show_alert=True
        )


@router.callback_query(F.data == "install_guide")
async def install_guide(callback: CallbackQuery):
    """Show installation guide"""
    guide_text = (
        "📖 <b>Інструкція по встановленню Майже Дія</b>\n\n"
        "<b>📱 Спосіб 1: Sideloadly (Рекомендовано)</b>\n"
        "1. Завантажте Sideloadly з офіційного сайту\n"
        "2. Підключіть iPhone до комп'ютера\n"
        "3. Відкрийте Sideloadly і перетягніть .ipa файл\n"
        "4. Введіть свій Apple ID (дані НЕ зберігаються)\n"
        "5. Натисніть Start і дочекайтеся встановлення\n"
        "6. На iPhone: Налаштування → Основні → VPN та керування пристроєм\n"
        "7. Довіріть сертифікату розробника\n\n"
        "<b>📱 Спосіб 2: AltStore</b>\n"
        "1. Встановіть AltServer на комп'ютер\n"
        "2. Встановіть AltStore на iPhone\n"
        "3. Відкрийте AltStore на iPhone\n"
        "4. Натисніть + та оберіть .ipa файл\n"
        "5. Дочекайтеся встановлення\n\n"
        "⚠️ <b>Важливо:</b>\n"
        "• Застосунок потрібно оновлювати кожні 7 днів\n"
        "• Використовуйте логін та пароль з бота для входу\n"
        "• Перезапустіть застосунок після першого входу"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="download_app")]
    ])
    
    await callback.message.edit_text(
        guide_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "buy_subscription")
async def buy_subscription(callback: CallbackQuery, db):
    """Buy subscription - show plans"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Спочатку зареєструйтесь!", show_alert=True)
        return
    
    # Create keyboard with subscription plans
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=SUBSCRIPTION_PLANS["1_day"]["text"], callback_data="sub_1_day")],
        [InlineKeyboardButton(text=SUBSCRIPTION_PLANS["7_days"]["text"], callback_data="sub_7_days")],
        [InlineKeyboardButton(text=SUBSCRIPTION_PLANS["14_days"]["text"], callback_data="sub_14_days")],
        [InlineKeyboardButton(text=SUBSCRIPTION_PLANS["30_days"]["text"], callback_data="sub_30_days")],
        [InlineKeyboardButton(text=SUBSCRIPTION_PLANS["lifetime"]["text"], callback_data="sub_lifetime")],
        [InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        "💎 Придбання підписки\n\n"
        "Оберіть план підписки:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub_"))
async def process_subscription_payment(callback: CallbackQuery, db):
    """Process subscription payment"""
    plan_key = callback.data.replace("sub_", "")
    
    if plan_key not in SUBSCRIPTION_PLANS:
        await callback.answer("Невірний план підписки!", show_alert=True)
        return
    
    plan = SUBSCRIPTION_PLANS[plan_key]
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Помилка: користувач не знайдено", show_alert=True)
        return
    
    # Show loading message
    await callback.message.edit_text(
        f"💎 Обробка платежу...\n\n"
        f"План: {plan['text']}\n"
        f"Сума: ${plan['price']}\n\n"
        f"⏳ Створення рахунку..."
    )
    
    # Create invoice in CryptoPay
    invoice = await create_cryptopay_invoice(
        user_id=callback.from_user.id,
        amount=plan['price'],
        currency="USDT",
        description=f"Підписка на {plan['text']}"
    )
    
    if not invoice:
        await callback.message.edit_text(
            "❌ Помилка створення рахунку\n\n"
            "Спробуйте ще раз або зверніться до адміністратора."
        )
        await callback.answer("Помилка створення рахунку", show_alert=True)
        return
    
    # Get payment link and invoice ID
    invoice_url = invoice.get("pay_url", "#")
    invoice_id = invoice.get("invoice_id")
    
    # Create payment confirmation button with invoice_id in callback
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатити", url=invoice_url)],
        [InlineKeyboardButton(text="✅ Я оплатив", callback_data=f"check_payment_{plan_key}_{invoice_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_subscription")]
    ])
    
    await callback.message.edit_text(
        f"💎 Рахунок створено\n\n"
        f"План: {plan['text']}\n"
        f"Сума: ${plan['price']}\n\n"
        f"Для оплати натисніть кнопку 'Оплатити' або перейдіть за посиланням:\n"
        f"{invoice_url}\n\n"
        f"⚠️ Після оплати натисніть 'Я оплатив' для активації підписки.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_status(callback: CallbackQuery, db):
    """Check payment status and activate subscription"""
    # Parse callback data: check_payment_{plan_key}_{invoice_id}
    parts = callback.data.replace("check_payment_", "").split("_")
    
    if len(parts) < 2:
        await callback.answer("Помилка формату даних!", show_alert=True)
        return
    
    plan_key = "_".join(parts[:-1])  # In case plan_key has underscores like "1_day"
    invoice_id = parts[-1]
    
    if plan_key not in SUBSCRIPTION_PLANS:
        await callback.answer("Невірний план підписки!", show_alert=True)
        return
    
    plan = SUBSCRIPTION_PLANS[plan_key]
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Помилка: користувач не знайдено", show_alert=True)
        return
    
    # Show checking message
    await callback.message.edit_text(
        "⏳ Перевірка оплати...\n\n"
        "Зачекайте, будь ласка."
    )
    
    # Check actual payment status via CryptoPay API
    try:
        invoice_id_int = int(invoice_id)
        invoice_status = await check_invoice_status(invoice_id_int)
        
        if not invoice_status:
            # Show error with retry button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Перевірити ще раз", callback_data=callback.data)],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_subscription")]
            ])
            
            await callback.message.edit_text(
                "❌ Не вдалося перевірити статус платежу\n\n"
                "Спробуйте ще раз або зверніться до адміністратора.",
                reply_markup=keyboard
            )
            await callback.answer("Помилка перевірки", show_alert=True)
            return
        
        # Check if invoice is paid
        invoice_paid = invoice_status.get("status") == "paid"
        
        if not invoice_paid:
            # Show error with retry button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Перевірити ще раз", callback_data=callback.data)],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_subscription")]
            ])
            
            await callback.message.edit_text(
                "❌ Платіж не знайдено\n\n"
                "Переконайтесь, що ви завершили оплату.\n\n"
                "Якщо ви вже оплатили, натисніть 'Перевірити ще раз' через кілька секунд.",
                reply_markup=keyboard
            )
            await callback.answer("Оплата не знайдена", show_alert=True)
            return
            
    except (ValueError, TypeError) as e:
        print(f"Error parsing invoice_id: {e}")
        # Show error with retry button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Перевірити ще раз", callback_data=callback.data)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="buy_subscription")]
        ])
        
        await callback.message.edit_text(
            "❌ Помилка перевірки платежу\n\n"
            "Зверніться до адміністратора.",
            reply_markup=keyboard
        )
        await callback.answer("Помилка", show_alert=True)
        return
    
    # Payment confirmed! Now activate the subscription
    
    # Calculate new subscription end date
    if plan_key == "lifetime":
        subscription_until = None
        subscription_until_display = "Назавжди"
        subscription_type = "Назавжди"
    else:
        current_date = datetime.now()
        if user['subscription_until']:
            try:
                # Parse existing subscription_until (can be datetime or string)
                if isinstance(user['subscription_until'], str):
                    current_date = datetime.fromisoformat(user['subscription_until'])
                elif isinstance(user['subscription_until'], datetime):
                    current_date = user['subscription_until']
            except:
                current_date = datetime.now()
        
        subscription_until = current_date + timedelta(days=plan['days'])
        subscription_until_display = subscription_until.isoformat()
        subscription_type = f"{plan['days']} днів"
    
    # Update user subscription
    user_obj = await db.get_user_by_id(user['id'])
    if user_obj:
        await db.update_subscription(
            user_id=user['id'],
            active=True,
            sub_type=subscription_type,
            until=subscription_until
        )
        success = True
    else:
        success = False
    
    if success:
        display_until = subscription_until_display if plan_key != "lifetime" else "Назавжди"
        await callback.message.edit_text(
            f"✅ Підписку активовано!\n\n"
            f"План: {plan['text']}\n"
            f"Дійсна до: {display_until}\n\n"
            f"Тепер ви можете завантажити застосунок через меню!"
        )
        
        # Show back to menu button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ До меню", callback_data="back_to_menu")]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer("Підписку активовано!", show_alert=True)
    else:
        await callback.message.edit_text(
            "❌ Помилка активації підписки\n\n"
            "Зверніться до адміністратора."
        )
        await callback.answer("Помилка активації", show_alert=True)


@router.callback_query(F.data == "settings")
async def settings(callback: CallbackQuery):
    """Settings"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        "⚙️ Налаштування\n\n"
        "Поки що тут нічого немає.",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    """Help information"""
    help_text = (
        "❓ Допомога\n\n"
        "📱 Про застосунок:\n"
        "Майже Дія - це застосунок для перегляду та керування вашими цифровими документами. "
        "У застосунку ви можете зберігати свої документи, переглядати їх у будь-який час та мати "
        "доступ до них з вашого пристрою.\n\n"
        "💎 Як отримати підписку:\n"
        "1. Натисніть кнопку '💎 Придбати підписку' в головному меню\n"
        "2. Оберіть план підписки (1 день, 7 днів, 14 днів, 30 днів або назавжди)\n"
        "3. Оплатіть через криптовалюту (USDT) за допомогою CryptoPay\n"
        "4. Після оплати натисніть кнопку '✅ Я оплатив' для активації підписки\n"
        "5. Підписка буде активована автоматично після підтвердження платежу\n\n"
        "📥 Як встановити застосунок:\n"
        "1. Придбайте активну підписку\n"
        "2. Перейдіть у розділ '📲 Завантажити застосунок' в головному меню\n"
        "3. Завантажте .ipa файл на ваш пристрій\n"
        "4. Встановіть застосунок через Sideloadly або інший додаток для встановлення\n"
        "5. Перезапустіть застосунок після першого входу для коректної роботи\n\n"
        "🆘 Зворотній зв'язок:\n"
        "Якщо у вас виникли питання або проблеми, зверніться до адміністратора через бота."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Створити тікет", callback_data="create_ticket")],
        [InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(help_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "create_ticket")
async def create_ticket_handler(callback: CallbackQuery, state: FSMContext):
    """Start creating a support ticket"""
    await callback.message.edit_text(
        "📝 Створення тікета\n\n"
        "Напишіть ваше питання або опишіть проблему, з якою ви зіткнулися.\n\n"
        "Адміністратор відповість вам якнайшвидше."
    )
    await state.set_state(TicketStates.waiting_for_ticket_message)
    await callback.answer()


@router.message(TicketStates.waiting_for_ticket_message)
async def process_ticket_message(message: Message, state: FSMContext, bot, db):
    """Process ticket message and send to admins"""
    ticket_message = message.text
    
    # Get user info
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Спочатку зареєструйтесь!")
        await state.clear()
        return
    
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    
    # Create ticket in database
    ticket_id = await db.create_ticket(
        user_id=user['id'],  # Use user database ID, not telegram ID
        user_telegram_id=message.from_user.id,  # Telegram ID for sending messages
        message=ticket_message,
        status="open"
    )
    
    # Send notification to admins
    ticket_text = (
        f"📝 Новий тікет #{ticket_id}\n\n"
        f"👤 Користувач: {user_info}\n"
        f"📧 Повідомлення:\n{ticket_message}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Відповісти", callback_data=f"reply_ticket_{ticket_id}")],
        [InlineKeyboardButton(text="✅ Закрити", callback_data=f"close_ticket_{ticket_id}")]
    ])
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, ticket_text, reply_markup=keyboard)
        except:
            pass
    
    await message.answer(
        f"✅ Ваш тікет #{ticket_id} створено!\n\n"
        "Адміністратор розгляне його та надішле відповідь найближчим часом.\n\n"
        "Очікуйте на відповідь."
    )
    
    await state.clear()


# Admin ticket management handlers
class TicketReplyStates(StatesGroup):
    waiting_for_reply = State()


@router.callback_query(F.data.startswith("reply_ticket_"))
async def start_reply_to_ticket(callback: CallbackQuery, state: FSMContext, db):
    """Start replying to a ticket"""
    ticket_id = int(callback.data.replace("reply_ticket_", ""))
    
    # Get ticket info
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await callback.answer("Тікет не знайдено!", show_alert=True)
        return
    
    await db.update_ticket_status(ticket_id, "answering")
    
    await callback.message.edit_text(
        f"💬 Відповідь на тікет #{ticket_id}\n\n"
        f"📝 Повідомлення користувача:\n{ticket['message']}\n\n"
        "Напишіть відповідь користувачу:"
    )
    
    await state.set_state(TicketReplyStates.waiting_for_reply)
    await state.update_data(ticket_id=ticket_id)
    await callback.answer()


@router.message(TicketReplyStates.waiting_for_reply)
async def process_ticket_reply(message: Message, state: FSMContext, bot, db):
    """Process admin reply to ticket"""
    data = await state.get_data()
    ticket_id = data['ticket_id']
    
    # Get ticket info
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await message.answer("❌ Тікет не знайдено!")
        await state.clear()
        return
    
    admin_reply = message.text
    
    # Save reply to database
    await db.add_ticket_reply(ticket_id, admin_reply)
    
    # Update ticket status
    await db.update_ticket_status(ticket_id, "answered")
    
    # Send reply to user
    try:
        await bot.send_message(
            ticket['user_telegram_id'],
            f"💬 Відповідь від підтримки\n\n"
            f"📝 Ваш тікет #{ticket_id}:\n{ticket['message']}\n\n"
            f"✅ Відповідь:\n{admin_reply}"
        )
    except:
        pass
    
    await message.answer(
        f"✅ Відповідь надіслано користувачу!\n\n"
        f"Тікет #{ticket_id} закрито."
    )
    
    await state.clear()


@router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(callback: CallbackQuery, db, bot):
    """Close a ticket without reply"""
    ticket_id = int(callback.data.replace("close_ticket_", ""))
    
    # Get ticket info
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await callback.answer("Тікет не знайдено!", show_alert=True)
        return
    
    # Update ticket status
    await db.update_ticket_status(ticket_id, "closed")
    
    # Notify user
    try:
        await bot.send_message(
            ticket['user_telegram_id'],
            f"📝 Тікет #{ticket_id} закрито адміністратором."
        )
    except:
        pass
    
    await callback.message.edit_text(
        f"✅ Тікет #{ticket_id} закрито."
    )
    await callback.answer()


# Admin commands
@router.message(Command("admin"))
async def admin_panel(message: Message, db):
    """Admin panel for managing tickets"""
    # Check if user is admin
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас немає доступу до цієї команди.")
        return
    
    # Get open tickets
    tickets = await db.get_open_tickets()
    
    if not tickets:
        await message.answer(
            "📋 Адміністративна панель\n\n"
            "📝 Відкриті тікети: немає\n\n"
            "Усі тікети оброблені ✅"
        )
        return
    
    # Display tickets
    tickets_text = f"📋 Адміністративна панель\n\n📝 Відкриті тікети: {len(tickets)}\n\n"
    
    keyboard_buttons = []
    for ticket in tickets:
        # Get user info
        user = await db.get_user_by_id(ticket['user_id'])
        user_name = user['full_name'] if user else f"ID: {ticket['user_telegram_id']}"
        
        # Format creation date
        try:
            created_dt = datetime.fromisoformat(ticket['created_at'])
            created_str = created_dt.strftime("%d.%m.%Y %H:%M")
        except:
            created_str = ticket['created_at']
        
        # Display ticket preview
        tickets_text += f"🔹 Тікет #{ticket['id']}\n"
        tickets_text += f"👤 {user_name}\n"
        tickets_text += f"📅 {created_str}\n"
        tickets_text += f"📝 {ticket['message'][:50]}...\n\n"
        
        # Add button for each ticket
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"Тікет #{ticket['id']} - {user_name[:20]}",
                callback_data=f"admin_ticket_{ticket['id']}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(tickets_text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("admin_ticket_"))
async def admin_view_ticket(callback: CallbackQuery, db):
    """View specific ticket details"""
    # Check if user is admin
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас немає доступу!", show_alert=True)
        return
    
    ticket_id = int(callback.data.replace("admin_ticket_", ""))
    
    # Get ticket
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await callback.answer("Тікет не знайдено!", show_alert=True)
        return
    
    # Get user info
    user = await db.get_user_by_id(ticket['user_id'])
    user_name = user['full_name'] if user else f"ID: {ticket['user_telegram_id']}"
    
    # Format dates
    try:
        created_dt = datetime.fromisoformat(ticket['created_at'])
        created_str = created_dt.strftime("%d.%m.%Y %H:%M")
    except:
        created_str = ticket['created_at']
    
    ticket_text = (
        f"📋 Тікет #{ticket_id}\n\n"
        f"👤 Користувач: {user_name}\n"
        f"📅 Створено: {created_str}\n"
        f"📊 Статус: {ticket['status']}\n\n"
        f"📝 Повідомлення:\n{ticket['message']}"
    )
    
    if ticket['reply']:
        ticket_text += f"\n\n💬 Відповідь:\n{ticket['reply']}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Відповісти", callback_data=f"reply_ticket_{ticket_id}")],
        [InlineKeyboardButton(text="✅ Закрити", callback_data=f"close_ticket_{ticket_id}")],
        [InlineKeyboardButton(text="⬅️ До списку", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(ticket_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, db):
    """Return to admin ticket list"""
    # Check if user is admin
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас немає доступу!", show_alert=True)
        return
    
    # Get open tickets
    tickets = await db.get_open_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            "📋 Адміністративна панель\n\n"
            "📝 Відкриті тікети: немає\n\n"
            "Усі тікети оброблені ✅"
        )
        return
    
    # Display tickets
    tickets_text = f"📋 Адміністративна панель\n\n📝 Відкриті тікети: {len(tickets)}\n\n"
    
    keyboard_buttons = []
    for ticket in tickets:
        # Get user info
        user = await db.get_user_by_id(ticket['user_id'])
        user_name = user['full_name'] if user else f"ID: {ticket['user_telegram_id']}"
        
        # Format creation date
        try:
            created_dt = datetime.fromisoformat(ticket['created_at'])
            created_str = created_dt.strftime("%d.%m.%Y %H:%M")
        except:
            created_str = ticket['created_at']
        
        # Display ticket preview
        tickets_text += f"🔹 Тікет #{ticket['id']}\n"
        tickets_text += f"👤 {user_name}\n"
        tickets_text += f"📅 {created_str}\n"
        tickets_text += f"📝 {ticket['message'][:50]}...\n\n"
        
        # Add button for each ticket
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"Тікет #{ticket['id']} - {user_name[:20]}",
                callback_data=f"admin_ticket_{ticket['id']}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(tickets_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "start_registration")
async def start_registration(callback: CallbackQuery, state: FSMContext, db):
    """Start registration process"""
    await callback.message.edit_text(
        "💻 Почнемо заповнювати інформацію про Вас.\n\n"
        "1) Напишіть ваше ПІБ в такому форматі:\n"
        "Маск Ілон Максимович"
    )
    await state.set_state(RegistrationStates.waiting_for_full_name)
    await db.save_registration_state(callback.from_user.id, "waiting_for_full_name", {})
    await callback.answer()


@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext, db):
    """Process full name"""
    full_name = message.text.strip()
    
    # Validate name format (3 words)
    if len(full_name.split()) != 3:
        await message.answer(
            "❌ Неправильний формат ПІБ.\n"
            "Напишіть ваше ПІБ в такому форматі:\n"
            "Маск Ілон Максимович"
        )
        return
    
    await message.answer("✍️ ПІБ записане")
    
    _, data = await db.get_registration_state(message.from_user.id)
    data['full_name'] = full_name
    
    # Если все данные уже заполнены (редактирование из предпросмотра), показываем предпросмотр
    if data.get('login') and data.get('password') and data.get('birth_date') and data.get('photo_path'):
        await show_registration_preview(message, state, db, data, data.get('is_editing', False))
        return
    
    await message.answer(
        "🛑 Зауваження: дата народження не може бути менша ніж 2000 рік та не більша ніж 2014.\n\n"
        "2) Напишіть вашу дату народження в такому форматі:\n"
        "24.08.2000"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад (змінити ПІБ)", callback_data="reg_back_full_name")],
        [InlineKeyboardButton(text="❌ Скасувати реєстрацію", callback_data="cancel_registration")]
    ])
    
    await message.answer("💡 Ви можете повернутися назад або скасувати реєстрацію", reply_markup=keyboard)
    
    await state.set_state(RegistrationStates.waiting_for_birth_date)
    await db.save_registration_state(message.from_user.id, "waiting_for_birth_date", data)


@router.message(RegistrationStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext, db):
    """Process birth date"""
    birth_date = message.text.strip()
    
    # Validate date format
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', birth_date):
        await message.answer(
            "❌ Неправильний формат дати.\n"
            "Напишіть вашу дату народження в такому форматі:\n"
            "24.08.2000"
        )
        return
    
    # Validate year range
    try:
        day, month, year = birth_date.split('.')
        year = int(year)
        if year < 2000 or year > 2014:
            await message.answer(
                "🛑 Дата народження не може бути менша ніж 2000 рік та не більша ніж 2014.\n\n"
                "Напишіть вашу дату народження в такому форматі:\n"
                "24.08.2000"
            )
            return
    except:
        await message.answer("❌ Неправильний формат дати.")
        return
    
    await message.answer("✍️ Дата народження записана!")
    
    _, data = await db.get_registration_state(message.from_user.id)
    data['birth_date'] = birth_date
    
    # Если все данные уже заполнены (редактирование из предпросмотра), показываем предпросмотр
    if data.get('login') and data.get('password') and data.get('full_name') and data.get('photo_path'):
        await show_registration_preview(message, state, db, data, data.get('is_editing', False))
        return
    
    await message.answer(
        "🤳 Відправте своє фото формату 3х4, як показано на прикладі.\n\n"
        "🛑 САМЕ 3х4!!!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад (змінити дату)", callback_data="reg_back_birth_date")],
        [InlineKeyboardButton(text="❌ Скасувати реєстрацію", callback_data="cancel_registration")]
    ])
    
    await message.answer("💡 Ви можете повернутися назад або скасувати реєстрацію", reply_markup=keyboard)
    
    await state.set_state(RegistrationStates.waiting_for_photo)
    await db.save_registration_state(message.from_user.id, "waiting_for_photo", data)


@router.message(RegistrationStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext, db, bot):
    """Process photo"""
    from utils.cloudinary_helper import upload_photo_to_cloudinary
    
    photo = message.photo[-1]
    
    # Download photo to temporary location
    os.makedirs("uploads/photos", exist_ok=True)
    temp_file_path = f"uploads/photos/{message.from_user.id}_{datetime.now().timestamp()}.jpg"
    
    await bot.download(photo, destination=temp_file_path)
    
    try:
        # Upload to Cloudinary
        cloudinary_url = await upload_photo_to_cloudinary(temp_file_path, message.from_user.id)
        
        # Delete local temp file
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        await message.answer("✅ Фото збережено!")
        
        _, data = await db.get_registration_state(message.from_user.id)
        data['photo_path'] = cloudinary_url
        
        # Если все данные уже заполнены (редактирование из предпросмотра), показываем предпросмотр
        if data.get('login') and data.get('password') and data.get('full_name') and data.get('birth_date'):
            await show_registration_preview(message, state, db, data, data.get('is_editing', False))
            return
    except Exception as e:
        await message.answer(f"❌ Помилка завантаження фото: {str(e)}\nСпробуйте ще раз.")
        return
    
    await message.answer(
        "💾 Реєстрація в застосунку\n\n"
        "При заході в Diia ви повинні будете авторизовуватись в системі, "
        "тому зараз необхідно придумати логін та пароль до входу\n\n"
        "🔑 Розпочнемо, придумайте логін та напишіть його який би ви хотіли використовувати при авторизації.\n"
        "🛑 Уточнення: довжина логіна та паролю повинна бути від 4 до 16 символів.\n\n"
        "🪶 Введіть логін:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад (змінити фото)", callback_data="reg_back_photo")],
        [InlineKeyboardButton(text="❌ Скасувати реєстрацію", callback_data="cancel_registration")]
    ])
    
    await message.answer("💡 Ви можете повернутися назад або скасувати реєстрацію", reply_markup=keyboard)
    
    await state.set_state(RegistrationStates.waiting_for_login)
    await db.save_registration_state(message.from_user.id, "waiting_for_login", data)


@router.message(RegistrationStates.waiting_for_login)
async def process_login(message: Message, state: FSMContext, db):
    """Process login"""
    login = message.text.strip()
    
    # Validate login length
    if len(login) < 4 or len(login) > 16:
        await message.answer(
            "❌ Довжина логіна повинна бути від 4 до 16 символів.\n\n"
            "🪶 Введіть логін:"
        )
        return
    
    # Get registration data
    _, data = await db.get_registration_state(message.from_user.id)
    is_editing = data.get('is_editing', False)
    
    # Check if login exists (только при новой регистрации или если логин изменился)
    if not is_editing:
        if await db.login_exists(login):
            await message.answer(
                "🛑 Даний логін зайнятий, придумайте інший. "
                "Для відміни процедури напишіть /cancel."
            )
            return
    else:
        # При редактировании проверяем только если логин изменился
        user = await db.get_user_by_telegram_id(message.from_user.id)
        if user and user['login'] != login and await db.login_exists(login):
            await message.answer(
                "🛑 Даний логін зайнятий, придумайте інший. "
                "Для відміни процедури напишіть /cancel."
            )
            return
    
    await message.answer("✍️ Логін записано!")
    
    data['login'] = login
    
    # Если все данные уже заполнены (редактирование из предпросмотра), показываем предпросмотр
    if data.get('password') and data.get('full_name') and data.get('birth_date') and data.get('photo_path'):
        await show_registration_preview(message, state, db, data, data.get('is_editing', False))
        return
    
    await message.answer(
        "🛑 Уточнення: ми не знаємо ваших паролів, одразу після його написання, "
        "ми видалимо повідомлення в Телеграммі.\n\n"
        "Придумайте пароль та напишіть його."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад (змінити логін)", callback_data="reg_back_login")],
        [InlineKeyboardButton(text="❌ Скасувати реєстрацію", callback_data="cancel_registration")]
    ])
    
    await message.answer("💡 Ви можете повернутися назад або скасувати реєстрацію", reply_markup=keyboard)
    
    await state.set_state(RegistrationStates.waiting_for_password)
    await db.save_registration_state(message.from_user.id, "waiting_for_password", data)


@router.message(RegistrationStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext, db):
    """Process password and show preview"""
    password = message.text.strip()
    
    # Delete password message
    try:
        await message.delete()
    except:
        pass
    
    # Validate password length
    if len(password) < 4 or len(password) > 16:
        await message.answer(
            "❌ Довжина паролю повинна бути від 4 до 16 символів.\n\n"
            "Придумайте пароль та напишіть його."
        )
        return
    
    # Get registration data
    _, data = await db.get_registration_state(message.from_user.id)
    data['password'] = password  # Временно сохраняем для предпросмотра
    is_editing = data.get('is_editing', False)
    
    # Показываем предпросмотр данных
    await show_registration_preview(message, state, db, data, is_editing)


async def show_registration_preview(message_or_callback, state: FSMContext, db, data: dict, is_editing: bool = False):
    """Показать предпросмотр всех данных перед сохранением"""
    from aiogram.types import Message, CallbackQuery
    
    # Определяем user_id
    if isinstance(message_or_callback, Message):
        user_id = message_or_callback.from_user.id
        send_func = lambda text, **kwargs: message_or_callback.answer(text, **kwargs)
    else:
        user_id = message_or_callback.from_user.id
        send_func = lambda text, **kwargs: message_or_callback.message.edit_text(text, **kwargs)
        await message_or_callback.answer()
    
    # Формируем текст предпросмотра
    preview_text = (
        "📋 **ПЕРЕДПЕРЕГЛЯД ДАНИХ**\n\n"
        "Перевірте всі дані перед збереженням:\n\n"
        f"👤 **ПІБ:** {data.get('full_name', 'Не вказано')}\n"
        f"🗓️ **Дата народження:** {data.get('birth_date', 'Не вказано')}\n"
        f"📸 **Фото:** {'✅ Завантажено' if data.get('photo_path') else '❌ Не завантажено'}\n"
        f"🔑 **Логін:** {data.get('login', 'Не вказано')}\n"
        f"🔒 **Пароль:** {'✅ Встановлено' if data.get('password') else '❌ Не встановлено'}\n\n"
        "⚠️ Після підтвердження дані будуть збережені!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити та зберегти", callback_data="confirm_registration")],
        [
            InlineKeyboardButton(text="✏️ Змінити ПІБ", callback_data="reg_edit_full_name"),
            InlineKeyboardButton(text="✏️ Змінити дату", callback_data="reg_edit_birth_date")
        ],
        [
            InlineKeyboardButton(text="✏️ Змінити фото", callback_data="reg_edit_photo"),
            InlineKeyboardButton(text="✏️ Змінити логін", callback_data="reg_edit_login")
        ],
        [
            InlineKeyboardButton(text="✏️ Змінити пароль", callback_data="reg_edit_password"),
            InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_registration")
        ]
    ])
    
    await send_func(preview_text, reply_markup=keyboard, parse_mode="Markdown")
    
    await state.set_state(RegistrationStates.preview)
    await db.save_registration_state(user_id, "preview", data)


@router.callback_query(F.data == "confirm_registration")
async def confirm_registration(callback: CallbackQuery, state: FSMContext, db):
    """Подтвердить и сохранить регистрацию"""
    _, data = await db.get_registration_state(callback.from_user.id)
    is_editing = data.get('is_editing', False)
    password = data.get('password')
    
    if not password:
        await callback.answer("❌ Помилка: пароль не вказано", show_alert=True)
        return
    
    success = False
    
    if is_editing:
        # Update existing user
        success = await db.update_user(
            telegram_id=callback.from_user.id,
            full_name=data['full_name'],
            birth_date=data['birth_date'],
            photo_path=data['photo_path'],
            login=data['login'],
            password=password
        )
    else:
        # Create new user
        user_id = await db.create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=data['full_name'],
            birth_date=data['birth_date'],
            photo_path=data['photo_path'],
            login=data['login'],
            password=password
        )
        success = user_id is not None
    
    if success:
        action_text = "оновлено" if is_editing else "завершена"
        
        # If new registration, inform about subscription requirement
        if not is_editing:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💎 Придбати підписку", callback_data="buy_subscription")],
                [InlineKeyboardButton(text="📋 Меню", callback_data="back_to_menu")]
            ])
            
            await callback.message.edit_text(
                f"✅ Реєстрація {action_text}!\n\n"
                f"👤 ПІБ: {data['full_name']}\n"
                f"🗓️ Дата народження: {data['birth_date']}\n"
                f"🔑 Логін: {data['login']}\n\n"
                f"⚠️ Статус підписки: ❌ Неактивна\n\n"
                f"💡 Для завантаження застосунку потрібна активна підписка.\n"
                f"Придбайте підписку, щоб отримати доступ до всіх функцій!",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                f"✅ Реєстрація {action_text}!\n\n"
                f"👤 ПІБ: {data['full_name']}\n"
                f"🗓️ Дата народження: {data['birth_date']}\n"
                f"🔑 Логін: {data['login']}\n\n"
                "Тепер ви можете завантажити застосунок через меню /menu"
            )
        
        # Clear registration state
        await db.clear_registration_state(callback.from_user.id)
        await state.clear()
        await callback.answer("✅ Дані збережено!")
    else:
        await callback.answer("❌ Помилка збереження. Спробуйте ще раз.", show_alert=True)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, db):
    """Cancel registration"""
    await state.clear()
    await db.clear_registration_state(message.from_user.id)
    await message.answer(
        "❌ Реєстрація скасована.\n\n"
        "Використовуйте /menu для повернення в головне меню."
    )


# Обработчики для возврата назад и редактирования
@router.callback_query(F.data == "cancel_registration")
async def cancel_registration_callback(callback: CallbackQuery, state: FSMContext, db):
    """Отменить регистрацию"""
    await state.clear()
    await db.clear_registration_state(callback.from_user.id)
    await callback.message.edit_text(
        "❌ Реєстрація скасована.\n\n"
        "Використовуйте /menu для повернення в головне меню."
    )
    await callback.answer("Реєстрацію скасовано")


@router.callback_query(F.data == "reg_back_full_name")
async def reg_back_full_name(callback: CallbackQuery, state: FSMContext, db):
    """Вернуться к шагу ввода ПІБ"""
    await callback.message.edit_text(
        "💻 Почнемо заповнювати інформацію про Вас.\n\n"
        "1) Напишіть ваше ПІБ в такому форматі:\n"
        "Маск Ілон Максимович"
    )
    await state.set_state(RegistrationStates.waiting_for_full_name)
    _, data = await db.get_registration_state(callback.from_user.id)
    await db.save_registration_state(callback.from_user.id, "waiting_for_full_name", data)
    await callback.answer()


@router.callback_query(F.data == "reg_back_birth_date")
async def reg_back_birth_date(callback: CallbackQuery, state: FSMContext, db):
    """Вернуться к шагу ввода даты рождения"""
    await callback.message.edit_text(
        "🛑 Зауваження: дата народження не може бути менша ніж 2000 рік та не більша ніж 2014.\n\n"
        "2) Напишіть вашу дату народження в такому форматі:\n"
        "24.08.2000"
    )
    await state.set_state(RegistrationStates.waiting_for_birth_date)
    _, data = await db.get_registration_state(callback.from_user.id)
    await db.save_registration_state(callback.from_user.id, "waiting_for_birth_date", data)
    await callback.answer()


@router.callback_query(F.data == "reg_back_photo")
async def reg_back_photo(callback: CallbackQuery, state: FSMContext, db):
    """Вернуться к шагу загрузки фото"""
    await callback.message.edit_text(
        "🤳 Відправте своє фото формату 3х4, як показано на прикладі.\n\n"
        "🛑 САМЕ 3х4!!!"
    )
    await state.set_state(RegistrationStates.waiting_for_photo)
    _, data = await db.get_registration_state(callback.from_user.id)
    await db.save_registration_state(callback.from_user.id, "waiting_for_photo", data)
    await callback.answer()


@router.callback_query(F.data == "reg_back_login")
async def reg_back_login(callback: CallbackQuery, state: FSMContext, db):
    """Вернуться к шагу ввода логина"""
    await callback.message.edit_text(
        "💾 Реєстрація в застосунку\n\n"
        "При заході в Diia ви повинні будете авторизовуватись в системі, "
        "тому зараз необхідно придумати логін та пароль до входу\n\n"
        "🔑 Розпочнемо, придумайте логін та напишіть його який би ви хотіли використовувати при авторизації.\n"
        "🛑 Уточнення: довжина логіна та паролю повинна бути від 4 до 16 символів.\n\n"
        "🪶 Введіть логін:"
    )
    await state.set_state(RegistrationStates.waiting_for_login)
    _, data = await db.get_registration_state(callback.from_user.id)
    await db.save_registration_state(callback.from_user.id, "waiting_for_login", data)
    await callback.answer()


# Обработчики для редактирования из предпросмотра
@router.callback_query(F.data == "reg_edit_full_name")
async def reg_edit_full_name(callback: CallbackQuery, state: FSMContext, db):
    """Редактировать ПІБ из предпросмотра"""
    await callback.message.edit_text(
        "✏️ Редагування ПІБ\n\n"
        "Напишіть ваше ПІБ в такому форматі:\n"
        "Маск Ілон Максимович"
    )
    await state.set_state(RegistrationStates.waiting_for_full_name)
    _, data = await db.get_registration_state(callback.from_user.id)
    await db.save_registration_state(callback.from_user.id, "waiting_for_full_name", data)
    await callback.answer()


@router.callback_query(F.data == "reg_edit_birth_date")
async def reg_edit_birth_date(callback: CallbackQuery, state: FSMContext, db):
    """Редактировать дату рождения из предпросмотра"""
    await callback.message.edit_text(
        "✏️ Редагування дати народження\n\n"
        "🛑 Зауваження: дата народження не може бути менша ніж 2000 рік та не більша ніж 2014.\n\n"
        "Напишіть вашу дату народження в такому форматі:\n"
        "24.08.2000"
    )
    await state.set_state(RegistrationStates.waiting_for_birth_date)
    _, data = await db.get_registration_state(callback.from_user.id)
    await db.save_registration_state(callback.from_user.id, "waiting_for_birth_date", data)
    await callback.answer()


@router.callback_query(F.data == "reg_edit_photo")
async def reg_edit_photo(callback: CallbackQuery, state: FSMContext, db):
    """Редактировать фото из предпросмотра"""
    await callback.message.edit_text(
        "✏️ Редагування фото\n\n"
        "🤳 Відправте своє фото формату 3х4, як показано на прикладі.\n\n"
        "🛑 САМЕ 3х4!!!"
    )
    await state.set_state(RegistrationStates.waiting_for_photo)
    _, data = await db.get_registration_state(callback.from_user.id)
    await db.save_registration_state(callback.from_user.id, "waiting_for_photo", data)
    await callback.answer()


@router.callback_query(F.data == "reg_edit_login")
async def reg_edit_login(callback: CallbackQuery, state: FSMContext, db):
    """Редактировать логин из предпросмотра"""
    await callback.message.edit_text(
        "✏️ Редагування логіну\n\n"
        "🔑 Придумайте логін та напишіть його який би ви хотіли використовувати при авторизації.\n"
        "🛑 Уточнення: довжина логіна повинна бути від 4 до 16 символів.\n\n"
        "🪶 Введіть логін:"
    )
    await state.set_state(RegistrationStates.waiting_for_login)
    _, data = await db.get_registration_state(callback.from_user.id)
    await db.save_registration_state(callback.from_user.id, "waiting_for_login", data)
    await callback.answer()


@router.callback_query(F.data == "reg_edit_password")
async def reg_edit_password(callback: CallbackQuery, state: FSMContext, db):
    """Редактировать пароль из предпросмотра"""
    await callback.message.edit_text(
        "✏️ Редагування паролю\n\n"
        "🛑 Уточнення: ми не знаємо ваших паролів, одразу після його написання, "
        "ми видалимо повідомлення в Телеграммі.\n\n"
        "Придумайте пароль та напишіть його.\n"
        "🛑 Довжина паролю повинна бути від 4 до 16 символів."
    )
    await state.set_state(RegistrationStates.waiting_for_password)
    _, data = await db.get_registration_state(callback.from_user.id)
    # Удаляем старый пароль из данных
    if 'password' in data:
        del data['password']
    await db.save_registration_state(callback.from_user.id, "waiting_for_password", data)
    await callback.answer()



# Clean version - no merge conflicts