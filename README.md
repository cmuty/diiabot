# Diia Telegram Bot

Telegram бот для системы "Майже Дія" - регистрация пользователей, управление подписками, и загрузка приложения.

## Функционал

- 📝 **Регистрация пользователей**: Полное ФИО, дата рождения, фото, логин и пароль
- 💎 **Система подписок**: Поддержка различных тарифов через CryptoPay
- 📲 **Загрузка приложения**: Отправка .ipa файла пользователям с активной подпиской
- 🎫 **Поддержка**: Система тикетов для связи с администратором
- 🔒 **Безопасность**: Хеширование паролей через bcrypt
- ☁️ **Cloudinary**: Хранение фотографий пользователей в облаке

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd DiiaBot
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` на основе `env_example.txt`:

```bash
cp env_example.txt .env
```

Заполните переменные в `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:pass@host/db
ADMIN_IDS=123456789
CRYPTOPAY_TOKEN=your_cryptopay_token
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### 4. Создание Telegram бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте токен и добавьте в `.env`

### 5. Настройка базы данных

Бот поддерживает **PostgreSQL** (рекомендуется) и **SQLite** (для тестирования).

#### PostgreSQL (рекомендуется)

```env
DATABASE_URL=postgresql://user:password@host:5432/database
```

#### SQLite (для локальной разработки)

```env
DATABASE_URL=database/diia.db
```

База данных автоматически инициализируется при первом запуске.

### 6. Настройка Cloudinary

1. Зарегистрируйтесь на [Cloudinary](https://cloudinary.com/)
2. Получите API ключи из Dashboard
3. Добавьте в `.env`:

```env
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### 7. Настройка CryptoPay

1. Создайте приложение в [CryptoPay](https://t.me/CryptoBot)
2. Получите API токен
3. Добавьте в `.env`:

```env
CRYPTOPAY_TOKEN=your_token
```

## Запуск бота

### Локально

```bash
python main.py
```

или

```bash
python -m bot.bot
```

### В фоновом режиме (Linux)

```bash
nohup python main.py &
```

## Структура проекта

```
DiiaBot/
├── bot/
│   ├── __init__.py
│   ├── bot.py              # Главный файл бота
│   └── handlers.py         # Обработчики команд и callback'ов
├── database/
│   ├── __init__.py
│   └── models.py           # Модели базы данных
├── utils/
│   ├── __init__.py
│   └── cloudinary_helper.py # Загрузка фото в Cloudinary
├── main.py                 # Точка входа
├── requirements.txt        # Зависимости
├── env_example.txt         # Пример .env файла
└── README.md
```

## Команды бота

### Пользовательские команды

- `/start` - Приветствие
- `/menu` - Главное меню бота
- `/cancel` - Отмена текущей операции

### Админ команды

- `/admin` - Админ панель (только для ADMIN_IDS)

## Меню бота

- 👤 **Профіль** - Просмотр и редактирование профиля
- 📲 **Завантажити застосунок** - Скачать .ipa файл (требуется подписка)
- 💎 **Придбати підписку** - Купить подписку
- ❓ **Допомога** - Помощь и создание тикета
- ⚙️ **Налаштування** - Настройки

## Тарифные планы

- 1 день - $1
- 7 дней - $3
- 14 дней - $5
- 30 дней - $7
- Навсегда - $15

## База данных

### Таблицы

1. **users** - Пользователи
   - id, telegram_id, username, full_name, birth_date
   - photo_path, login, password_hash
   - subscription_active, subscription_type, subscription_until
   - last_login, registered_at, updated_at

2. **sessions** - Сессии
   - id, user_id, device_info, created_at

3. **registration_temp** - Временные данные регистрации
   - telegram_id, state, data, created_at

4. **payments** - Платежи
   - id, user_id, amount, currency, payment_method
   - status, subscription_type, subscription_days
   - created_at, completed_at

## Разработка

### Добавление новых команд

Добавьте обработчик в `bot/handlers.py`:

```python
@router.message(Command("mycommand"))
async def my_command_handler(message: Message, db):
    await message.answer("My response")
```

### Добавление callback'ов

```python
@router.callback_query(F.data == "my_callback")
async def my_callback_handler(callback: CallbackQuery, db):
    await callback.message.edit_text("Response")
    await callback.answer()
```

## Troubleshooting

### Бот не отвечает

1. Проверьте `BOT_TOKEN` в `.env`
2. Убедитесь что бот запущен
3. Проверьте логи на ошибки

### Ошибки базы данных

1. Проверьте `DATABASE_URL`
2. Убедитесь что БД доступна
3. Проверьте права доступа

### Ошибки Cloudinary

1. Проверьте `CLOUDINARY_URL`
2. Убедитесь в правильности API ключей
3. Проверьте квоту на Cloudinary

## Безопасность

- ✅ Пароли хешируются через `bcrypt`
- ✅ Фото хранятся в Cloudinary (не на сервере)
- ✅ PostgreSQL для продакшена
- ✅ Валидация всех вводимых данных

## Поддержка

Если у вас возникли вопросы или проблемы, создайте issue в репозитории.

## Лицензия

MIT License

