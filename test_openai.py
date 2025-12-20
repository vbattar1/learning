#!/usr/bin/env python3
"""
Simple test script to verify OpenAI API connection
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("="*60)
print("OpenAI API Connection Test")
print("="*60)

# Check API key
if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not found in environment")
    print("Please create a .env file with: OPENAI_API_KEY=sk-your-key-here")
    exit(1)

print(f"✅ API Key found: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}")

# Test simple API call
print("\n🔗 Making test API call to OpenAI...")

url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}
data = {
    "model": "gpt-4o",  # Using latest model
    "messages": [
        {"role": "user", "content": "Say 'Hello! API connection working!' and nothing else."}
    ],
    "temperature": 0.1,
    "max_tokens": 50
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=15)
    
    print(f"📊 Response Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
    
    result = response.json()
    
    # Print full response
    print("\n" + "="*60)
    print("Full API Response:")
    print("="*60)
    import json
    print(json.dumps(result, indent=2))
    
    # Extract and print the message
    message = result["choices"][0]["message"]["content"]
    
    print("\n" + "="*60)
    print("LLM Response:")
    print("="*60)
    print(message)
    print("="*60)
    
    print("\n✅ SUCCESS! OpenAI API is working correctly!")
    print(f"✅ Model used: {result['model']}")
    print(f"✅ Tokens used: {result['usage']['total_tokens']}")

except requests.exceptions.RequestException as e:
    print(f"\n❌ Network Error: {e}")
    print("Check your internet connection")
    exit(1)
    
except KeyError as e:
    print(f"\n❌ Unexpected response format: {e}")
    print(f"Response: {response.text[:500]}")
    exit(1)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    print(traceback.format_exc())
    exit(1)

print("\n✅ Test completed successfully!")
print("Your OpenAI API connection is working properly.")

