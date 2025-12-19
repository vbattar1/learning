from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
from bs4 import BeautifulSoup
import re
from typing import Optional
import os
import requests
from dotenv import load_dotenv

app = FastAPI(title="Vegan Menu Filter", description="Filter restaurant menus for vegan and vegetarian options")

# Load environment variables
load_dotenv()

# Store OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configuration
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

# Debug: Print configuration on startup
print(f"🤖 LLM Configuration:")
print(f"   USE_LLM: {USE_LLM}")
print(f"   API_KEY_SET: {'YES' if OPENAI_API_KEY else 'NO'}")
print(f"   MODEL: {LLM_MODEL}")
print(f"   TEMPERATURE: {LLM_TEMPERATURE}")

# Mount templates and static files
templates = Jinja2Templates(directory="templates")

# Keywords that indicate vegan items
VEGAN_KEYWORDS = [
    'vegan', 'plant-based', 'plant based', 'no dairy', 'no eggs',
    'dairy-free', 'dairy free', 'egg-free', 'egg free'
]

# Keywords that indicate vegetarian items
VEGETARIAN_KEYWORDS = [
    'vegetarian', 'veggie', 'no meat', 'meat-free', 'meat free'
]

# Keywords that indicate non-vegan items (things to avoid for vegan filter)
NON_VEGAN_KEYWORDS = [
    'beef', 'pork', 'chicken', 'turkey', 'lamb', 'fish', 'seafood',
    'salmon', 'tuna', 'shrimp', 'crab', 'lobster', 'scallops', 'clams',
    'meat', 'bacon', 'sausage', 'ham', 'steak', 'burger', 'cheese',
    'milk', 'butter', 'cream', 'egg', 'eggs', 'yogurt', 'yoghurt'
]


def classify_menu_item_keywords(item_text: str) -> dict:
    """
    Classify menu item using keyword matching (fallback method)
    """
    item_lower = item_text.lower()

    # Check for explicit labels
    is_vegan = any(keyword in item_lower for keyword in VEGAN_KEYWORDS)
    is_vegetarian = any(keyword in item_lower for keyword in VEGAN_KEYWORDS + VEGETARIAN_KEYWORDS)

    # Check for non-vegan ingredients
    has_non_vegan = any(keyword in item_lower for keyword in NON_VEGAN_KEYWORDS)

    # If explicitly labeled, trust the label
    if is_vegan:
        return {"is_vegan": True, "is_vegetarian": True, "reason": "explicitly labeled vegan"}
    elif is_vegetarian:
        return {"is_vegan": False, "is_vegetarian": True, "reason": "explicitly labeled vegetarian"}

    # If no non-vegan keywords found, assume vegan (conservative)
    if not has_non_vegan:
        return {"is_vegan": True, "is_vegetarian": True, "reason": "no animal products detected"}

    # Check for meat specifically for vegetarian classification
    meat_keywords = ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'fish', 'seafood', 'meat', 'bacon', 'sausage', 'ham', 'steak']
    has_meat = any(keyword in item_lower for keyword in meat_keywords)

    if not has_meat:
        return {"is_vegan": False, "is_vegetarian": True, "reason": "no meat detected, may contain dairy/eggs"}
    else:
        return {"is_vegan": False, "is_vegetarian": False, "reason": "contains meat"}

def extract_menu_text(url: str) -> str:
    """Extract text content from a webpage"""
    try:
        # Add headers to appear more like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html5lib')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Try to find menu-specific content first
        menu_content = []

        # Look for common menu selectors
        menu_selectors = [
            'menu', '.menu', '#menu', '[class*="menu"]',
            'restaurant-menu', '.restaurant-menu',
            'food-menu', '.food-menu'
        ]

        for selector in menu_selectors:
            try:
                menu_elements = soup.select(selector)
                if menu_elements:
                    for element in menu_elements:
                        text = element.get_text(separator='\n', strip=True)
                        if text and len(text) > 50:  # Only include substantial content
                            menu_content.append(text)
            except:
                continue

        # If no specific menu content found, get all text
        if not menu_content:
            text = soup.get_text(separator='\n', strip=True)
            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            return text

        # Combine found menu content
        combined_text = '\n\n'.join(menu_content)
        return combined_text

    except requests.exceptions.RequestException as e:
        return f"Error fetching menu: Network error - {str(e)}"
    except Exception as e:
        return f"Error fetching menu: {str(e)}"

def filter_menu_items(menu_text: str, filter_type: str) -> list:
    """
    Filter menu items using LLM to analyze entire menu and return only matching items
    """
    print(f"🤖 Processing menu with {len(menu_text)} characters for filter: {filter_type}")

    if USE_LLM:
        return filter_menu_with_llm(menu_text, filter_type)
    else:
        return filter_menu_with_keywords(menu_text, filter_type)

def filter_menu_with_llm(menu_text: str, filter_type: str) -> list:
    """
    Use LLM to analyze entire menu and extract only items matching the filter criteria
    """
    print(f"🧠 Sending entire menu to LLM for {filter_type} filtering...")

    if not OPENAI_API_KEY:
        print("⚠️  No OpenAI API key, falling back to keyword filtering")
        return filter_menu_with_keywords(menu_text, filter_type)

    # Define filter criteria based on type
    if filter_type == 'vegan':
        criteria = "vegan (no animal products whatsoever - no meat, fish, dairy, eggs, honey, etc.)"
        filter_description = "only items that are 100% vegan"
    elif filter_type == 'vegetarian':
        criteria = "vegetarian (no meat or fish/seafood, but dairy and eggs are allowed)"
        filter_description = "only items that are vegetarian"
    else:  # all
        criteria = "all menu items (no filtering)"
        filter_description = "all menu items"

    prompt = f"""
    Analyze this restaurant menu text and extract {filter_description}.

    Menu text:
    {menu_text}

    Instructions:
    - Look for food items with prices (typically end with $X.XX)
    - For each item that matches the criteria "{criteria}", extract:
      * The full item name and description
      * The price
      * A brief reason why it matches the criteria

    Return ONLY a JSON array of matching items in this exact format:
    [
        {{
            "item": "Full item name and description with price",
            "reason": "Why this item matches {criteria}"
        }},
        {{
            "item": "Another item...",
            "reason": "Another reason..."
        }}
    ]

    Important:
    - Only include items that clearly match the {criteria} criteria
    - Exclude any items containing meat, fish, or seafood for vegetarian
    - Exclude ALL animal products for vegan (meat, fish, dairy, eggs, honey)
    - If no items match, return an empty array []
    - Be conservative - when in doubt, exclude the item
    """

    try:
        # Make direct API call to OpenAI
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": LLM_TEMPERATURE,
            "max_tokens": 1000
        }

        response = requests.post(url, headers=headers, json=data, timeout=20)
        response.raise_for_status()

        result = response.json()
        result_text = result["choices"][0]["message"]["content"].strip()

        # Parse the JSON response
        import json
        items = json.loads(result_text)

        # Convert to the expected format
        filtered_items = []
        for item_data in items:
            item_text = item_data.get('item', '').strip()
            reason = item_data.get('reason', '').strip()
            if item_text and reason:
                full_reason = f"{reason} (LLM)"
                filtered_items.append((item_text, full_reason))

        print(f"✅ LLM found {len(filtered_items)} {filter_type} items")
        return filtered_items

    except Exception as e:
        print(f"❌ LLM filtering failed: {e}")
        # Fallback to keyword filtering
        return filter_menu_with_keywords(menu_text, filter_type)

def filter_menu_with_keywords(menu_text: str, filter_type: str) -> list:
    """
    Traditional keyword-based filtering as fallback
    """
    print(f"🔤 Using keyword filtering for {filter_type} items")

    # Split text into potential menu items (by lines, then by common separators)
    lines = menu_text.split('\n')
    menu_items = []

    for line in lines:
        line = line.strip()
        if len(line) < 10 or len(line) > 200:  # Skip very short or very long lines
            continue

        # Look for price patterns to identify menu items
        if re.search(r'\$[\d.]+|\d+\.\d{2}', line):
            menu_items.append(line)

    filtered_items = []

    for item in menu_items:
        classification = classify_menu_item_keywords(item)

        is_vegan = classification['is_vegan']
        is_vegetarian = classification['is_vegetarian']
        reason = classification['reason']

        # Apply filter based on type
        should_include = False

        if filter_type == 'vegan' and is_vegan:
            should_include = True
        elif filter_type == 'vegetarian' and is_vegetarian:
            should_include = True
        elif filter_type == 'all':
            should_include = True

        if should_include:
            full_reason = f"{reason} (Keywords)"
            filtered_items.append((item, full_reason))

    print(f"📝 Keywords found {len(filtered_items)} {filter_type} items")
    return filtered_items

@app.get("/")
async def home(request: Request):
    """Display the main menu filter page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "filtered_items": [],
        "filter_type": "all",
        "error_message": None,
        "menu_url": "",
        "menu_text": ""
    })

@app.post("/")
async def filter_menu(
    request: Request,
    filter_type: str = Form("all"),
    input_type: str = Form(...),
    menu_url: Optional[str] = Form(""),
    menu_text: Optional[str] = Form("")
):
    """Process the menu filtering request"""
    filtered_items = []
    error_message = None

    # Debug: Print received form data
    print(f"DEBUG - input_type: '{input_type}', menu_url: '{menu_url}', menu_text: '{menu_text[:50] if menu_text else ''}...'")

    if input_type == 'url':
        url = (menu_url or "").strip()
        print(f"DEBUG - Processing URL: '{url}'")
        if url:
            menu_content = extract_menu_text(url)
            if menu_content.startswith('Error'):
                error_message = menu_content
            else:
                # Debug: show first 500 characters of extracted content
                print(f"Extracted content preview: {menu_content[:500]}...")
                filtered_items = filter_menu_items(menu_content, filter_type)
                print(f"Found {len(filtered_items)} filtered items")
        else:
            error_message = "Please enter a URL"
            print("DEBUG - No URL provided")

    elif input_type == 'text':
        text = (menu_text or "").strip()
        print(f"DEBUG - Processing text input, length: {len(text)}")
        if text:
            filtered_items = filter_menu_items(text, filter_type)
            print(f"Found {len(filtered_items)} filtered items from text")
        else:
            error_message = "Please enter menu text"
            print("DEBUG - No text provided")
    else:
        error_message = f"Invalid input type: {input_type}. Please select URL or Text input."
        print(f"DEBUG - Invalid input_type: {input_type}")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "filtered_items": filtered_items,
        "filter_type": filter_type,
        "error_message": error_message,
        "menu_url": menu_url or "",
        "menu_text": menu_text or ""
    })

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Vegan Menu Filter App...")
    print("📱 Visit: http://127.0.0.1:8000")
    print("🧪 Test URL: Try https://httpbin.org/html (simple test page)")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
