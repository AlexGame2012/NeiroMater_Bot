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
        
        # Улучшенные параметры для генерации
        payload = {
            "height": 1024,  # Увеличил размер для лучшего качества
            "width": 1024,
            "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Phoenix модель
            "prompt": english_prompt,
            "num_images": 1,
            "presetStyle": "DYNAMIC",  # Добавил стиль
            "contrast": 3.5,  # Добавил контраст
            "public": False,  # Приватная генерация
            "scheduler": "DPMSolverMultistepScheduler",  # Улучшенный scheduler
            "guidance_scale": 7,  # Контроль следования промпту
            "num_inference_steps": 30  # Больше шагов = лучше качество
        }
        
        # Отправка запроса на генерацию
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Ошибка при создании задачи: {response.status_code}")
            print(f"Ответ: {response.text}")
            return None
            
        generation_data = response.json()
        generation_id = generation_data['sdGenerationJob']['generationId']
        
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(5) 
            
            result_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
            response = requests.get(result_url, headers=headers)
            
            if response.status_code != 200:
                continue
                
            data = response.json()
            
            if data["generations_by_pk"]["status"] == "COMPLETE":
                if data["generations_by_pk"]["generated_images"]:
                    image_url = data["generations_by_pk"]["generated_images"][0]["url"]
                    image_data = requests.get(image_url).content
                    return image_data
            elif data["generations_by_pk"]["status"] == "FAILED":
                print("Генерация не удалась")
                return None
        
        print("Таймаут ожидания генерации")
        return None
        
    except Exception as e:
        print(f"Ошибка в generate_image: {e}")
        import traceback
        traceback.print_exc()
        return None