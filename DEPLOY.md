# Деплой бота на Render

## Подготовка

1. ✅ `render.yaml` - готов
2. ✅ `server.py` - Flask сервер для Render
3. ✅ `requirements.txt` - все зависимости
4. ✅ `.env` - настройки (не коммитить!)

## Шаги деплоя

### 1. Создай Git репозиторий (если еще нет)

```bash
cd C:\Users\nutip\OneDrive\Desktop\проекты\DiiaBot
git init
git add .
git commit -m "Initial commit: Diia Telegram Bot"
```

### 2. Запуш на GitHub

```bash
# Создай репозиторий на GitHub
# Потом:
git remote add origin https://github.com/your-username/diia-bot.git
git branch -M main
git push -u origin main
```

### 3. Деплой на Render

1. Открой https://dashboard.render.com/
2. Нажми **"New +"** → **"Web Service"**
3. Подключи GitHub репозиторий
4. Render автоматически обнаружит `render.yaml`
5. Настрой переменные окружения (скопируй из `.env`):

   **Обязательные переменные:**
   - `BOT_TOKEN` - токен твоего бота от @BotFather
   - `DATABASE_URL` - PostgreSQL URL (можешь создать на Render)
   - `ADMIN_IDS` - твой Telegram ID
   - `CRYPTOPAY_TOKEN` - токен от CryptoPay
   - `CLOUDINARY_URL` - URL от Cloudinary

6. Нажми **"Create Web Service"**

### 4. Настройка переменных окружения на Render

В Dashboard твоего сервиса → **Environment**:

```
BOT_TOKEN=твой_токен_от_BotFather
DATABASE_URL=postgresql://user:pass@host/db
ADMIN_IDS=твой_telegram_id
CRYPTOPAY_TOKEN=твой_cryptopay_токен
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### 5. Создай PostgreSQL базу данных (если нужно)

1. В Render Dashboard → **"New +"** → **"PostgreSQL"**
2. Создай базу данных
3. Скопируй **External Database URL**
4. Добавь в переменную `DATABASE_URL`

## Проверка деплоя

1. Дождись завершения деплоя (статус "Live")
2. Открой URL своего сервиса (например: https://diia-bot.onrender.com)
3. Должен показать:
   ```json
   {
     "status": "ok",
     "service": "Diia Telegram Bot",
     "bot_running": true
   }
   ```

4. Проверь бота в Telegram - отправь `/start`

## Логи

Смотри логи в Render Dashboard → **Logs**

Если бот не работает, проверь:
- ✅ Все переменные окружения заданы
- ✅ БД доступна
- ✅ Токен бота правильный
- ✅ Cloudinary настроен

## Обновление

После изменений в коде:

```bash
git add .
git commit -m "Update bot"
git push origin main
```

Render автоматически задеплоит обновление!

## Важно!

- **НЕ коммить `.env` файл** - он в `.gitignore`
- Render использует free tier - может засыпать после 15 минут неактивности
- Для постоянной работы нужен платный план или keep-alive сервис

## Troubleshooting

### Бот не отвечает
- Проверь логи на Render
- Убедись что `BOT_TOKEN` правильный
- Проверь что сервис в статусе "Live"

### База данных не доступна
- Проверь `DATABASE_URL`
- Убедись что PostgreSQL сервис запущен
- Проверь права доступа

### Event loop errors
- Перезапусти сервис на Render
- Проверь логи на ошибки Python

## Контакты

Если возникли проблемы - проверь логи и документацию Render.

