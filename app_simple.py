from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def filter_vegan_items(menu_text: str) -> list:
    """Simple function to filter vegan items using OpenAI"""
    
    print(f"\n🔵 filter_vegan_items called with menu_text length: {len(menu_text)}")
    print(f"Menu text content:\n{repr(menu_text)}")
    
    if not menu_text or len(menu_text.strip()) == 0:
        print("❌ ERROR: menu_text is empty!")
        return []
    
    prompt = f"""Look at this menu and list ONLY the vegan dishes (no animal products).

Menu:
{menu_text}

Your response (just list the vegan items, one per line):"""

    print(f"\n🔗 Calling OpenAI API...")
    print(f"API Key: {OPENAI_API_KEY[:15]}...")
    print(f"Full prompt length: {len(prompt)}")
    print(f"Prompt preview:\n{prompt[:500]}...")
    
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

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.text}")
            return []
        
        result = response.json()
        result_text = result["choices"][0]["message"]["content"].strip()
        
        print("\n" + "="*60)
        print("RAW LLM OUTPUT:")
        print("="*60)
        print(result_text)
        print("="*60 + "\n")
        
        # Parse lines
        items = []
        for line in result_text.split('\n'):
            line = line.strip().lstrip('*-•123456789. ')
            if line and len(line) > 3:
                items.append(line)
        
        print(f"✅ Found {len(items)} vegan items")
        return items
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        return []

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head><title>Simple Vegan Filter Test</title></head>
        <body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>🌱 Simple Vegan Filter Test</h1>
            <form method="post" action="/test" enctype="application/x-www-form-urlencoded">
                <textarea name="menu" style="width: 100%; height: 200px; padding: 10px; font-size: 16px;">Grilled chicken $15.99
Vegan burger $5.99
Caesar salad $12.99</textarea>
                <br><br>
                <button type="submit" style="padding: 15px 30px; font-size: 18px; background: #4CAF50; color: white; border: none; cursor: pointer;">
                    Filter Vegan Items
                </button>
            </form>
        </body>
    </html>
    """

@app.post("/test")
async def test(menu: str = Form("")):
    print("\n" + "="*60)
    print("TEST REQUEST RECEIVED")
    print("="*60)
    print(f"Menu text received (length: {len(menu)}):\n{repr(menu)}")
    print(f"Menu text content:\n{menu}")
    
    if not menu or len(menu.strip()) == 0:
        return HTMLResponse(content="""
        <html>
            <body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
                <h1>❌ Error: No menu text received</h1>
                <p>Please enter menu text in the form.</p>
                <a href="/">Go Back</a>
            </body>
        </html>
        """)
    
    vegan_items = filter_vegan_items(menu)
    
    results_html = "<br>".join([f"✅ {item}" for item in vegan_items])
    if not vegan_items:
        results_html = "❌ No vegan items found"
    
    return HTMLResponse(content=f"""
    <html>
        <head><title>Results</title></head>
        <body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>🌱 Vegan Items Found:</h1>
            <div style="background: #f0f0f0; padding: 20px; border-radius: 10px; font-size: 18px;">
                {results_html}
            </div>
            <br>
            <a href="/" style="padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
                Try Again
            </a>
        </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting SIMPLE test app...")
    print("📱 Visit: http://127.0.0.1:8001")
    print("🧪 Test with the pre-filled simple menu")
    uvicorn.run("app_simple:app", host="127.0.0.1", port=8001, reload=True)

