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
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
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
    """Extract raw text content from a webpage - no processing"""
    try:
        # Add headers to appear more like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        # Get raw text without any processing
        soup = BeautifulSoup(response.content, 'html5lib')
        
        # Remove only script and style tags to get clean text
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get all text - let LLM handle the filtering
        raw_text = soup.get_text(separator='\n', strip=True)
        
        print(f"📄 Extracted {len(raw_text)} characters of raw text from URL")
        return raw_text

    except requests.exceptions.RequestException as e:
        return f"Error fetching menu: Network error - {str(e)}"
    except Exception as e:
        return f"Error fetching menu: {str(e)}"

def filter_menu_items(menu_text: str, filter_type: str) -> list:
    """
    Filter menu items using LLM to analyze entire menu and return only matching items
    """
    print(f"\n{'='*60}")
    print(f"🤖 filter_menu_items called")
    print(f"{'='*60}")
    print(f"Menu text length: {len(menu_text)} characters")
    print(f"Filter type: {filter_type}")
    print(f"Menu text content (first 500 chars):\n{menu_text[:500]}")
    print(f"Full menu text:\n{repr(menu_text)}")
    print(f"{'='*60}\n")

    try:
        if USE_LLM:
            print(f"🧠 Using LLM filtering for filter_type={filter_type}")
            result = filter_menu_with_llm(menu_text, filter_type)
            print(f"🔵 filter_menu_with_llm returned: {type(result)}, length: {len(result) if result else 'None'}")
        else:
            print(f"🔤 Using keyword filtering for filter_type={filter_type}")
            result = filter_menu_with_keywords(menu_text, filter_type)
            print(f"🔵 filter_menu_with_keywords returned: {type(result)}, length: {len(result) if result else 'None'}")

        # Ensure we always return a list
        if result is None:
            print("⚠️  Function returned None, using empty list")
            return []
        if not isinstance(result, list):
            print(f"⚠️  Function returned {type(result)} instead of list, converting to empty list")
            return []
        
        print(f"✅ filter_menu_items returning {len(result)} items")
        return result
    except Exception as e:
        print(f"❌ filter_menu_items failed: {e}")
        import traceback
        print(f"🐛 Full traceback: {traceback.format_exc()}")
        # Ultimate fallback - return empty list
        return []

def filter_menu_with_llm(menu_text: str, filter_type: str) -> list:
    """
    Use LLM to analyze entire menu and extract only items matching the filter criteria
    """
    print(f"🔵 Entered filter_menu_with_llm with filter_type={filter_type}")
    
    # Truncate menu text to prevent LLM overload
    truncated_menu = menu_text

    print(f"🧠 Sending menu to LLM for {filter_type} filtering...")

    if not OPENAI_API_KEY:
        print("⚠️  No OpenAI API key, falling back to keyword filtering")
        result = filter_menu_with_keywords(menu_text, filter_type)
        print(f"🔙 Keyword filtering returned {len(result) if result else 0} items")
        return result if result else []

    # Debug: Show menu preview
    menu_preview = menu_text[:200] + "..." if len(menu_text) > 200 else menu_text
    print(f"📄 Menu preview: {menu_preview.replace(chr(10), ' | ')}")
    print(f"📏 Full menu text length: {len(menu_text)} characters")
    print(f"📏 Menu text content (first 500 chars):\n{menu_text[:500]}")

    # Define filter criteria based on type
    if filter_type == 'all':
        # For "all items", we want to extract all menu items without filtering
        print("🔄 Calling extract_all_menu_items_llm for 'all' filter")
        result = extract_all_menu_items_llm(menu_text)
        print(f"🔵 extract_all_menu_items_llm returned {len(result) if result else 0} items")
        return result if result else []
    
    print(f"📝 Building plain text prompt for filter_type={filter_type}")
    
    # Build simple prompt that returns plain text list
    if filter_type == 'vegetarian':
        prompt = f"""Look at this restaurant menu text and list ONLY the vegetarian dishes (no meat/fish/seafood).

List each item on a new line. Include the price if visible.

Menu Text:
{menu_text}

Your response (just list the items, one per line):"""
    elif filter_type == 'vegan':
        prompt = f"""Look at this restaurant menu text and list ONLY the vegan dishes (no animal products).

List each item on a new line. Include the price if visible.

Menu Text:
{menu_text}

Your response (just list the items, one per line):"""
    elif filter_type == 'nonvegetarian':
        prompt = f"""Look at this restaurant menu text and list ONLY the dishes with meat, fish, or seafood.

List each item on a new line. Include the price if visible.

Menu Text:
{menu_text}

Your response (just list the items, one per line):"""
    else:
        print(f"⚠️  Unknown filter_type: {filter_type}, using keyword filtering")
        result = filter_menu_with_keywords(menu_text, filter_type)
        return result if result else []
    
    print(f"✅ Created prompt of {len(prompt)} characters")
    print(f"📋 Prompt preview (first 500 chars):\n{prompt[:500]}...")

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
            "max_tokens": 2000  # More tokens for plain text response
        }

        print(f"🔗 Calling OpenAI API...")
        print(f"   Model: {LLM_MODEL}")
        print(f"   API Key: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:] if OPENAI_API_KEY and len(OPENAI_API_KEY) > 14 else 'INVALID'}")
        print(f"   Endpoint: {url}")
        print(f"   Prompt length: {len(prompt)} characters")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API Error Response:")
            print(response.text)
            return filter_menu_with_keywords(menu_text, filter_type)
        
        response.raise_for_status()
        print(f"✅ API call successful!")

        result = response.json()
        result_text = result["choices"][0]["message"]["content"].strip()
        
        print(f"\n{'='*60}")
        print(f"📨 RAW LLM OUTPUT ({len(result_text)} characters):")
        print(f"{'='*60}")
        print(result_text)
        print(f"{'='*60}\n")

        # Parse plain text response - each line is a menu item
        filtered_items = []
        lines = result_text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, numbers, or very short text
            if not line or len(line) < 5:
                continue
            # Skip lines that look like headings or instructions
            if line.endswith(':') or line.lower().startswith('here') or line.lower().startswith('note'):
                continue
            # Clean up markdown/bullets
            line = line.lstrip('*-•123456789. ')
            
            if line:
                filtered_items.append((line, f"{filter_type} (LLM)"))

        print(f"✅ LLM returned {len(filtered_items)} {filter_type} items after conversion")
        # Debug: Show first few results
        if filtered_items:
            print(f"📋 Sample results: {filtered_items[:3]}")
        else:
            print(f"⚠️  No items after conversion - LLM returned empty list or invalid format")
        
        print(f"🔵 filter_menu_with_llm returning list with {len(filtered_items)} items")
        return filtered_items

    except Exception as e:
        print(f"❌ LLM filtering failed: {e}")
        import traceback
        print(f"🐛 Full traceback: {traceback.format_exc()}")
        print(f"🔄 Falling back to keyword filtering for {filter_type}")
        # Fallback to keyword filtering
        result = filter_menu_with_keywords(menu_text, filter_type)
        print(f"📝 Keyword filtering returned {len(result) if result else 0} items")
        return result if result else []

def extract_all_menu_items_llm(menu_text: str) -> list:
    """
    Use LLM to extract ALL menu items without filtering
    """
    print("🔵 Entered extract_all_menu_items_llm")

    if not OPENAI_API_KEY:
        print("⚠️  No OpenAI API key, falling back to keyword extraction")
        result = filter_menu_with_keywords(menu_text, 'all')
        print(f"🔙 Keyword extraction returned {len(result) if result else 0} items")
        return result if result else []

    prompt = f"""Look at this restaurant menu/webpage text and list ALL the food dishes you find.

List each item on a new line. Include prices if you see them.

Text:
{menu_text}

Your response (just list the items, one per line):"""

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
            "max_tokens": 2000  # More tokens for plain text
        }

        print(f"🔗 Calling OpenAI API to extract all items...")
        print(f"   Model: {LLM_MODEL}")
        print(f"   API Key: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:] if OPENAI_API_KEY and len(OPENAI_API_KEY) > 14 else 'INVALID'}")
        print(f"   Prompt length: {len(prompt)} characters")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API Error Response:")
            print(response.text)
            return filter_menu_with_keywords(menu_text, 'all')
        
        response.raise_for_status()
        print(f"✅ API call successful!")

        result = response.json()
        result_text = result["choices"][0]["message"]["content"].strip()
        
        print(f"\n{'='*60}")
        print(f"📨 RAW LLM OUTPUT FOR 'ALL ITEMS' ({len(result_text)} characters):")
        print(f"{'='*60}")
        print(result_text)
        print(f"{'='*60}\n")

        # Parse plain text response - each line is a menu item
        filtered_items = []
        lines = result_text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Skip empty lines or very short text
            if not line or len(line) < 5:
                continue
            # Skip headings or instructions
            if line.endswith(':') or line.lower().startswith('here') or line.lower().startswith('note'):
                continue
            # Clean up markdown/bullets
            line = line.lstrip('*-•123456789. ')
            
            if line:
                filtered_items.append((line, "all items (LLM)"))

        print(f"✅ LLM extracted {len(filtered_items)} total menu items")
        # Debug: Show first few results
        if filtered_items:
            print(f"📋 Sample extracted items: {filtered_items[:3]}")
        else:
            print(f"⚠️  No items extracted - check LLM response format")
        
        print(f"🔵 extract_all_menu_items_llm returning {len(filtered_items)} items")
        return filtered_items

    except Exception as e:
        print(f"❌ LLM extraction failed: {e}")
        import traceback
        print(f"🐛 Full traceback: {traceback.format_exc()}")
        # Fallback to keyword extraction
        result = filter_menu_with_keywords(menu_text, 'all')
        print(f"🔙 Keyword extraction fallback returned {len(result) if result else 0} items")
        return result if result else []

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
        elif filter_type == 'nonvegetarian' and not is_vegetarian:
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
                if filtered_items is None:
                    filtered_items = []
                    print("⚠️  Warning: filter_menu_items returned None, using empty list")
                print(f"Found {len(filtered_items)} filtered items")
        else:
            error_message = "Please enter a URL"
            print("DEBUG - No URL provided")

    elif input_type == 'text':
        text = (menu_text or "").strip()
        print(f"\n{'='*60}")
        print(f"DEBUG - Processing text input")
        print(f"{'='*60}")
        print(f"Text length: {len(text)}")
        print(f"Text content (first 500 chars):\n{text[:500]}")
        print(f"Full text:\n{repr(text)}")
        print(f"{'='*60}\n")
        
        if text:
            filtered_items = filter_menu_items(text, filter_type)
            if filtered_items is None:
                filtered_items = []
                print("⚠️  Warning: filter_menu_items returned None, using empty list")
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
