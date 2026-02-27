import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_URL = "https://models.inference.ai.azure.com/chat/completions"
LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")

def ask_gpt(messages):
    if not GITHUB_TOKEN:
        return None
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    if not messages or messages[0].get("role") != "system":
        messages_with_system = [
            {"role": "system", "content": "Ты полезный ассистент. Отвечай на вопросы, учитывая контекст предыдущих сообщений."}
        ] + messages
    else:
        messages_with_system = messages
    
    data = {
        "messages": messages_with_system,
        "model": "gpt-4o",
        "temperature": 0.7
    }
    
    try:
        response = requests.post(GITHUB_API_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return None
    except Exception:
        return None

def translate_to_english(text):
    if not text:
        return text
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {"role": "system", "content": "Ты переводчик. Переведи текст на английский язык. Отвечай только переводом, без пояснений."},
            {"role": "user", "content": text}
        ],
        "model": "gpt-4o",
        "temperature": 0.3
    }
    
    try:
        response = requests.post(GITHUB_API_URL, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            return text
    except Exception:
        return text

def generate_image(prompt):
    try:
        english_prompt = translate_to_english(prompt)
        
        url = "https://cloud.leonardo.ai/api/rest/v1/generations"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {LEONARDO_API_KEY}"
        }
        
        payload = {
            "height": 512,
            "width": 512,
            "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
            "prompt": english_prompt
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            return None
            
        generation_id = response.json()['sdGenerationJob']['generationId']
        
        time.sleep(20)
        
        result_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
        response = requests.get(result_url, headers=headers)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        image_url = data["generations_by_pk"]["generated_images"][0]["url"]
        
        image_data = requests.get(image_url).content
        return image_data
        
    except Exception:
        return None