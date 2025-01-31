from flask import Flask, request, jsonify
from openai import OpenAI
import requests
import logging
import os
import httpx

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Используем переменные окружения для хранения ключей
OPENAI_API_KEY = "На сервере сдесь версия с ключем "
GOOGLE_API_KEY = "На сервере сдесь версия с ключем"
GOOGLE_CSE_ID = "На сервере сдесь версия с ключем"

# Создаем клиент OpenAI с явным указанием параметров httpx
http_client = httpx.Client()  # Создаем клиент httpx без параметра proxies
client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)

app = Flask(__name__)

@app.route('/')
def home():
    return "Добро пожаловать в ITMO Bot! Используйте /api/request для запросов."

def ask_gpt(query):
    """
    Функция для отправки запроса к OpenAI API.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Можно заменить на "gpt-4"
            messages=[{"role": "user", "content": query}],
            max_tokens=0.5
        )
        time.sleep(5)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI API: {e}")
        return f"Ошибка: {e}"

def search_google(query, num_results=3):
    """
    Функция для поиска ссылок с использованием Google Custom Search API.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        logger.error("API-ключ Google или CSE ID не настроены.")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_results = response.json().get("items", [])
        return [result["link"] for result in search_results]
    except Exception as e:
        logger.error(f"Ошибка при поиске в Google: {e}")
        return []

@app.route('/api/request', methods=['POST'])
def handle_request():
    """
    Обработчик POST-запросов на /api/request.
    """
    data = request.json
    query = data.get('query')
    id = data.get('id')

    if not query or not id:
        return jsonify({"error": "Неверный запрос: отсутствует query или id"}), 400

    # Используем GPT для генерации ответа
    gpt_response = ask_gpt(query)

    # Ищем ссылки с использованием Google Custom Search API
    search_query = f"Университет ИТМО {query}"  # Добавляем контекст для поиска
    sources = search_google(search_query)

    # Формируем JSON-ответ
    response = {
        "id": id,
        "answer": None,  # Если вопрос не предполагает выбор из вариантов
        "reasoning": gpt_response,
        "sources": sources  # Добавляем найденные ссылки
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)