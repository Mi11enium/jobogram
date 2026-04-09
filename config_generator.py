import requests
import json
import re
import time
import os
from typing import Dict, List, Set, Any
from dotenv import load_dotenv

load_dotenv()

# ===== ДЕФОЛТНЫЙ КОНФИГ (fallback) =====
DEFAULT_TECH_CATEGORIES = {
    'Языки программирования': [
        'python', 'питон', 'java', 'javascript', 'js', 'typescript', 'ts', 'c++', 'cpp', 
        'c#', 'csharp', 'php', 'ruby', 'go', 'golang', 'rust', 'swift', 'kotlin', '1с', '1c', 'sql'
    ],
    'Базы данных': [
        'postgresql', 'postgres', 'mysql', 'mongodb', 'mongo', 'redis', 'elasticsearch', 
        'clickhouse', 'sqlite', 'oracle', 'mariadb', 'база данных', 'бд'
    ],
    'Фреймворки и библиотеки': [
        'django', 'flask', 'spring', 'react', 'vue', 'angular', 'pandas', 'numpy', 
        'tensorflow', 'pytorch', 'bootstrap', 'jquery', 'fastapi', 'laravel'
    ],
    'DevOps и инфраструктура': [
        'docker', 'kubernetes', 'k8s', 'jenkins', 'gitlab', 'ansible', 'terraform', 
        'nginx', 'apache', 'kafka', 'rabbitmq', 'devops', 'ci/cd'
    ],
    'Тестирование и качество': [
        'pytest', 'unittest', 'selenium', 'cypress', 'jest', 'junit', 'тестирование', 
        'qa', 'quality assurance', 'баг-репорт', 'регрессионное тестирование'
    ],
    'Облачные технологии': [
        'aws', 'yandex cloud', 'google cloud', 'gcp', 'azure', 'cloud', 'облако'
    ],
    'Инструменты разработки': [
        'git', 'github', 'gitlab', 'jira', 'confluence', 'vscode', 'intellij', 
        'pycharm', 'postman', 'swagger'
    ]
}

DEFAULT_ACTION_VERBS = {
    'разработка', 'разрабатывать', 'проектирование', 'тестирование', 'тестировать',
    'рефакторинг', 'отладка', 'развертывание', 'деплой', 'администрирование',
    'мониторинг', 'документирование', 'оптимизация', 'автоматизация',
    'интеграция', 'сопровождение', 'поддержка', 'code review'
}

DEFAULT_CATEGORY_ICONS = {
    'Языки программирования': '💻',
    'Базы данных': '🗄️',
    'Фреймворки и библиотеки': '📚',
    'DevOps и инфраструктура': '⚙️',
    'Тестирование и качество': '✅',
    'Облачные технологии': '☁️',
    'Инструменты разработки': '🛠️'
}

DEFAULT_CATEGORY_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
]

class DynamicConfig:
    def __init__(self):
        self.tech_categories = DEFAULT_TECH_CATEGORIES.copy()
        self.action_verbs = DEFAULT_ACTION_VERBS.copy()
        self.category_icons = DEFAULT_CATEGORY_ICONS.copy()
        self.category_colors = DEFAULT_CATEGORY_COLORS.copy()
        self.all_tech_terms = set()
        self.update_all_tech_terms()
        self.is_generated = False
        self.job_title = None
    
    def update_all_tech_terms(self):
        self.all_tech_terms = set()
        for terms in self.tech_categories.values():
            self.all_tech_terms.update(terms)
    
    def apply_api_response(self, data: dict, job_title: str):
        self.tech_categories = data.get('TECH_CATEGORIES', DEFAULT_TECH_CATEGORIES)
        action_list = data.get('ACTION_VERBS', list(DEFAULT_ACTION_VERBS))
        self.action_verbs = set(action_list) if isinstance(action_list, list) else DEFAULT_ACTION_VERBS.copy()
        self.category_icons = data.get('CATEGORY_ICONS', DEFAULT_CATEGORY_ICONS)
        self.category_colors = data.get('CATEGORY_COLORS', DEFAULT_CATEGORY_COLORS)
        self.update_all_tech_terms()
        self.is_generated = True
        self.job_title = job_title

def clean_and_extract_json(content: str) -> str:
    content = re.sub(r'```json\s*', '', content)
    content = re.sub(r'```\s*', '', content)
    content = content.strip()
    
    start = content.find('{')
    end = content.rfind('}')
    
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No valid JSON object found")
    
    return content[start:end+1]

def fix_truncated_json(json_str: str) -> str:
    stack = []
    in_string = False
    escape_next = False
    result = list(json_str)
    
    for i, char in enumerate(json_str):
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\' and in_string:
            escape_next = True
            continue
            
        if char == '"' and not in_string:
            in_string = True
        elif char == '"' and in_string:
            in_string = False
        elif not in_string:
            if char in ['{', '[']:
                stack.append(char)
            elif char == '}' and stack and stack[-1] == '{':
                stack.pop()
            elif char == ']' and stack and stack[-1] == '[':
                stack.pop()
    
    if in_string:
        result.append('"')
    
    while stack:
        last = stack.pop()
        if last == '{':
            result.append('}')
        elif last == '[':
            result.append(']')
    
    return ''.join(result)

def validate_and_fix_config(data: dict) -> dict:
    if 'TECH_CATEGORIES' not in data or not isinstance(data['TECH_CATEGORIES'], dict):
        data['TECH_CATEGORIES'] = DEFAULT_TECH_CATEGORIES
    
    if 'ACTION_VERBS' not in data or not isinstance(data['ACTION_VERBS'], list):
        data['ACTION_VERBS'] = list(DEFAULT_ACTION_VERBS)
    
    if 'CATEGORY_ICONS' not in data or not isinstance(data['CATEGORY_ICONS'], dict):
        data['CATEGORY_ICONS'] = {}
    
    if 'CATEGORY_COLORS' not in data or not isinstance(data['CATEGORY_COLORS'], list):
        data['CATEGORY_COLORS'] = DEFAULT_CATEGORY_COLORS
    
    tech_categories = {}
    for cat, terms in data['TECH_CATEGORIES'].items():
        if isinstance(terms, list):
            clean_terms = []
            for term in terms:
                if isinstance(term, str):
                    clean_terms.append(term.lower().strip())
            tech_categories[cat] = list(set(clean_terms))
    data['TECH_CATEGORIES'] = tech_categories
    
    data['ACTION_VERBS'] = list(set(
        v.lower().strip() for v in data['ACTION_VERBS'] 
        if isinstance(v, str) and v.strip()
    ))
    
    tech_keys = set(data['TECH_CATEGORIES'].keys())
    icon_keys = set(data['CATEGORY_ICONS'].keys())
    
    for key in tech_keys - icon_keys:
        data['CATEGORY_ICONS'][key] = '🔹'
    
    for key in list(data['CATEGORY_ICONS'].keys()):
        if key not in tech_keys:
            del data['CATEGORY_ICONS'][key]
    
    colors_needed = max(len(tech_keys), 12)
    colors = data['CATEGORY_COLORS']
    if len(colors) < colors_needed:
        extended_colors = []
        while len(extended_colors) < colors_needed:
            extended_colors.extend(DEFAULT_CATEGORY_COLORS)
        data['CATEGORY_COLORS'] = extended_colors[:colors_needed]
    
    return data

def generate_config_from_api(job_titles: List[str], api_key: str = None, max_retries: int = 3) -> Dict[str, Any]:
    if not api_key:
        api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key or not job_titles:
        raise ValueError("API ключ и должности обязательны")
    
    job_titles_str = ", ".join(f'"{j}"' for j in job_titles)
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv('APP_URL', 'http://localhost:8501'),
        "X-Title": "Jobogram Config Generator"
    }
    
    system_prompt = "Ты — Senior IT-Рекрутер. Твоя задача: составить глубокий словарь ключевых слов для парсинга вакансий российского рынка."
    
    user_prompt = f"""Ты — Senior IT-Рекрутер. Твоя задача: составить глубокий словарь ключевых слов для парсинга вакансий российского рынка по должностям:
{job_titles_str}

ВАЖНО: Учитывай, что в русскоязычных вакансиях часто используются русские термины!

ПРАВИЛА ФОРМИРОВАНИЯ СЛОВАРЯ:
1. НАЗВАНИЯ КАТЕГОРИЙ — СТРОГО НА РУССКОМ ЯЗЫКЕ!
2. Технологии и инструменты — ДОБАВЛЯЙ И РУССКИЕ, И АНГЛИЙСКИЕ варианты
3. Добавляй русскоязычные синонимы
4. Все слова в нижнем регистре
5. Выдавай СТРОГО ВАЛИДНЫЙ JSON

Сгенерируй ответ СТРОГО в формате JSON:
{{
  "TECH_CATEGORIES": {{
    "Языки программирования": ["python", "питон", "java", "javascript"],
    "Базы данных": ["postgresql", "mysql", "база данных", "бд"]
  }},
  "ACTION_VERBS": ["разработка", "тестирование", "отладка"],
  "CATEGORY_ICONS": {{
    "Языки программирования": "💻",
    "Базы данных": "🗄️"
  }}
}}
ВЕРНИ ТОЛЬКО СЫРОЙ JSON. Никакого пояснительного текста"""

    last_error = None
    
    for attempt in range(max_retries):
        try:
            payload = {
                "model": "google/gemini-2.5-flash-lite",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2 + (attempt * 0.1),
                "max_tokens": 16000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            try:
                clean_json = clean_and_extract_json(content)
                config_data = json.loads(clean_json)
                return validate_and_fix_config(config_data)
            except json.JSONDecodeError:
                try:
                    fixed_json = fix_truncated_json(clean_json)
                    config_data = json.loads(fixed_json)
                    return validate_and_fix_config(config_data)
                except json.JSONDecodeError:
                    json_match = re.search(r'(\{[\s\S]*\})', content)
                    if json_match:
                        try:
                            config_data = json.loads(json_match.group(1))
                            return validate_and_fix_config(config_data)
                        except:
                            pass
                    
                    if attempt == max_retries - 1:
                        raise ValueError(f"Failed to parse JSON after {max_retries} attempts")
                    continue
                    
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"Config generation failed: {str(e)}")
    
    raise RuntimeError(f"Failed after {max_retries} attempts. Last error: {last_error}")

config = DynamicConfig()