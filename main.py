import os
import logging
from fastapi import FastAPI, Request
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

@app.post("/")
async def main(request: Request):
    try:
        body = await request.json()
        user_text = body["request"]["original_utterance"]

        if not DEEPSEEK_API_KEY:
            logger.error("DEEPSEEK_API_KEY не задан")
            return {"response": {"text": "Сервис временно недоступен."}}

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Ты — полезный ассистент. Отвечай пользователю кратко и только на русском языке."},
                {"role": "user", "content": user_text}
            ],
            "max_tokens": 300,
            "temperature": 0.3
        }

        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=4)
        data = response.json()

        if response.status_code != 200:
            logger.error(f"Ошибка DeepSeek: {data}")
            return {"response": {"text": "Не удалось получить ответ. Попробуйте позже."}}

        answer = data["choices"][0]["message"]["content"]

        return {
            "version": body.get("version", "1.0"),
            "session": body.get("session", {}),
            "response": {"end_session": False, "text": answer}
        }

    except Exception as e:
        logger.exception("Ошибка в обработчике")
        return {"response": {"text": "Внутренняя ошибка. Попробуйте ещё раз."}}