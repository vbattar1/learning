#!/usr/bin/env python3
"""Test if environment variables are being read correctly"""
import os
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("Environment Variables Test")
print("="*60)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

print(f"OPENAI_API_KEY: {OPENAI_API_KEY[:15]}... (length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0})")
print(f"USE_LLM: {USE_LLM} (type: {type(USE_LLM)})")
print(f"LLM_MODEL: {LLM_MODEL}")
print(f"LLM_TEMPERATURE: {LLM_TEMPERATURE}")

print("\n" + "="*60)
print("Raw .env values:")
print("="*60)
print(f"USE_LLM raw: '{os.getenv('USE_LLM')}'")
print(f"USE_LLM lower: '{os.getenv('USE_LLM', 'false').lower()}'")
print(f"Comparison: '{os.getenv('USE_LLM', 'false').lower()}' == 'true' ? {os.getenv('USE_LLM', 'false').lower() == 'true'}")

if USE_LLM:
    print("\n✅ LLM is ENABLED")
else:
    print("\n❌ LLM is DISABLED")
    print("To enable, set USE_LLM=true in .env file")

