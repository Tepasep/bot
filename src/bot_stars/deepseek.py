import aiohttp
from telegram import (
    KeyboardButton,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import random
import os
from telegram.ext import ConversationHandler, ContextTypes, CallbackQueryHandler

class DeepSeekHandler:
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_response(self, user_input: str, system_prompt: str = None) -> str:
        """Получение ответа от DeepSeek API"""
        payload = self._build_payload(user_input, system_prompt)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL,
                    headers=self.headers,
                    json=payload
                ) as response:
                    return await self._process_response(response)
        except Exception as e:
            print(f"API Connection Error: {e}")
            return "Извините, возникла проблема с соединением."

    def _build_payload(self, user_input: str, system_prompt: str = None) -> dict:
        """Формирование тела запроса"""
        base_system_prompt = """Вы - полезный помощник. Отвечайте на вопросы 
        на основе предоставленной базы знаний. Если ответа нет в базе знаний, 
        вежливо извинитесь."""
        
        messages = [{
            "role": "system",
            "content": system_prompt or base_system_prompt
        }, {
            "role": "user",
            "content": user_input
        }]
        
        return {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.7
        }

    async def _process_response(self, response: aiohttp.ClientResponse) -> str:
        """Обработка ответа от API"""
        if response.status == 200:
            data = await response.json()
            return data['choices'][0]['message']['content']
        else:
            error = await response.text()
            print(f"DeepSeek API Error: {error}")
            return "Извините, не удалось обработать запрос."