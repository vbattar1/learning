#!/usr/bin/env python3
"""
Test with the simple menu case
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

menu_text = """Grilled chicken $15.99
Vegan burger $5.99
Caesar salad $12.99"""

prompt = f"""Look at this menu and list ONLY the vegan dishes.

Menu:
{menu_text}

Your response (just list the vegan items, one per line):"""

print("="*60)
print("Testing with simple menu case")
print("="*60)
print(f"Menu:\n{menu_text}\n")
print(f"Prompt:\n{prompt}\n")

url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}
data = {
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.1,
    "max_tokens": 2000
}

print("🔗 Calling OpenAI API...")
response = requests.post(url, headers=headers, json=data, timeout=30)

print(f"Status: {response.status_code}")

if response.status_code != 200:
    print(f"❌ Error: {response.text}")
else:
    result = response.json()
    result_text = result["choices"][0]["message"]["content"].strip()
    
    print("\n" + "="*60)
    print("RAW LLM OUTPUT:")
    print("="*60)
    print(result_text)
    print("="*60)
    
    # Parse it
    lines = result_text.split('\n')
    items = [line.strip().lstrip('*-•123456789. ') for line in lines if line.strip() and len(line.strip()) > 3]
    
    print(f"\nParsed items: {items}")
    print(f"Found {len(items)} vegan items")

