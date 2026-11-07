import os
import logging
from fastapi import FastAPI, Request
import requests

# Настройка логирования для отладки в SnapDeploy
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Официальный endpoint DeepSeek (без /v1)
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

@app.post("/")
async def main(request: Request):
    try:
        body = await request.json()
        logger.info(f"Получен запрос от Алисы: {body}")

        user_text = body["request"]["original_utterance"]

        if not DEEPSEEK_API_KEY:
            logger.error("Переменная DEEPSEEK_API_KEY не задана!")
            return {
                "version": body.get("version", "1.0"),
                "session": body.get("session", {}),
                "response": {"end_session": False, "text": "Сервис временно недоступен."}
            }

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": user_text}],
            "max_tokens": 500
        }

        logger.info("Отправка запроса в DeepSeek...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=10)

        logger.info(f"Статус ответа DeepSeek: {response.status_code}")
        logger.info(f"Тело ответа DeepSeek: {response.text}")

        if response.status_code != 200:
            logger.error(f"Ошибка API DeepSeek: {response.status_code} - {response.text}")
            return {
                "version": body.get("version", "1.0"),
                "session": body.get("session", {}),
                "response": {"end_session": False, "text": "Извините, не удалось получить ответ от нейросети. Попробуйте позже."}
            }

        data = response.json()

        if "choices" not in data or not data["choices"]:
            logger.error(f"Неожиданный формат ответа: {data}")
            return {
                "version": body.get("version", "1.0"),
                "session": body.get("session", {}),
                "response": {"end_session": False, "text": "Нейросеть вернула пустой ответ."}
            }

        answer = data["choices"][0]["message"]["content"]
        logger.info("Ответ успешно сформирован.")

        return {
            "version": body.get("version", "1.0"),
            "session": body.get("session", {}),
            "response": {"end_session": False, "text": answer}
        }

    except Exception as e:
        logger.exception("Непредвиденная ошибка в обработчике")
        return {
            "version": body.get("version", "1.0") if 'body' in locals() else "1.0",
            "session": body.get("session", {}) if 'body' in locals() else {},
            "response": {"end_session": False, "text": "Произошла внутренняя ошибка. Попробуйте ещё раз."}
        }