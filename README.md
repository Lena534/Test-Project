# 🛠️ Система обработки жалоб клиентов

Простое API на FastAPI + SQLite с интеграцией внешних API:

- 🔍 Анализ тональности (APILayer)
- 🧠 Категоризация жалобы (OpenAI GPT-3.5)
- ⚙️ Готово к подключению n8n

---

## 🚀 Быстрый старт

### 1. Клонируй репозиторий

git clone git@github.com:Lena534/Test-Project.git

2. Установи зависимости

pip install -r requirements.txt

3. Настрой .env
Создай файл .env:

OPENAI_API_KEY=your_openai_key
APILAYER_KEY=your_apilayer_key

4. Запуск сервера

uvicorn main:app --reload
Открой в браузере:

Swagger UI: http://localhost:8000/docs

JSON-документация: http://localhost:8000/openapi.json

Примеры запросов (curl)

1. Добавить жалобу

curl -X POST http://127.0.0.1:8000/complaints \
     -H "Content-Type: application/json" \
     -d '{"text": "Не приходит SMS-код"}'
2. Получить все жалобы

curl http://127.0.0.1:8000/complaints
3. Фильтрация по статусу и дате

curl "http://127.0.0.1:8000/complaints?status=open&since=2024-04-25T00:00:00"
4. Получить жалобу по ID

curl http://127.0.0.1:8000/complaints/1
5. Обновить статус жалобы

curl -X PATCH http://127.0.0.1:8000/complaints/1/status \
     -H "Content-Type: application/json" \
     -d '{"status": "closed"}'