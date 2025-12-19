# Vegan/Vegetarian Menu Filter

A FastAPI web application that helps you find vegan and vegetarian options from restaurant menus.

## What This Does

This app takes restaurant menu information (either from a website URL or pasted text) and filters it to show only:
- **Vegan options**: Plant-based items with no animal products
- **Vegetarian options**: Items with no meat (may include dairy/eggs)
- **All items**: Shows everything for comparison

## How It Works

### LLM-Powered Classification (Recommended)
When enabled, the app uses OpenAI's GPT models to intelligently analyze menu items:

- **Contextual Understanding**: Recognizes items like "tofu stir-fry" as vegan even without explicit labels
- **Ingredient Analysis**: Understands complex ingredients and cooking methods
- **Ambiguity Resolution**: Makes conservative decisions when uncertain
- **Detailed Explanations**: Provides reasons for each classification

### Keyword-Based Classification (Fallback)
If LLM is disabled, uses traditional keyword matching:
- **Vegan detection**: Items labeled "vegan", "plant-based", or containing no meat/dairy/eggs
- **Vegetarian detection**: Items labeled "vegetarian" or containing no meat

## Getting Started

### 1. Install Python Dependencies

Make sure you have Python installed (version 3.7 or higher), then run:

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables (For LLM Features)

Create a `.env` file in the project root:

```bash
cp env_template.txt .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
USE_LLM=true
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.1
```

**Note:** We use direct API calls to OpenAI (no external library dependencies), which ensures maximum compatibility.

**Efficiency:** LLM processes entire menus in one API call instead of calling for each item individually - much faster and cheaper!

**Note:** The app works without LLM (uses keyword matching), but LLM provides much better accuracy!

### 3. Run the Application

```bash
python app.py
```

The app will start at http://127.0.0.1:8000

Alternatively, you can run it directly with uvicorn:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### 3. Test the App

**URL Testing:** Try these test URLs:
- `https://httpbin.org/html` - Simple HTML test page
- `https://example.com` - Basic webpage
- Restaurant websites (may not work if they use JavaScript)

**Text Testing:** Copy-paste menu content directly:

```
Grilled Chicken Breast $16.99 - Marinated chicken with herbs
Caesar Salad $12.99 - Romaine lettuce, parmesan, croutons
Vegan Buddha Bowl $14.99 - Quinoa, roasted vegetables, tahini dressing
Cheese Pizza $13.99 - Tomato sauce, mozzarella, fresh basil
Vegetable Stir Fry $11.99 - Mixed vegetables with tofu
Beef Burger $15.99 - Angus beef patty with cheese
```

### 3. Use the App

1. **Option A - Enter a Restaurant URL:**
   - Click "Enter Restaurant URL"
   - Paste the menu webpage URL
   - Choose your filter preference
   - Click "Filter Menu"

2. **Option B - Paste Menu Text:**
   - Click "Paste Menu Text"
   - Copy menu items from a website or takeout menu
   - Paste them in the text box
   - Choose your filter preference
   - Click "Filter Menu"

## Example Usage

Try these sample menu items by pasting them into the text input:

```
Grilled Chicken Breast $16.99 - Marinated chicken with herbs
Caesar Salad $12.99 - Romaine lettuce, parmesan, croutons
Vegan Buddha Bowl $14.99 - Quinoa, roasted vegetables, tahini dressing
Cheese Pizza $13.99 - Tomato sauce, mozzarella, fresh basil
Vegetable Stir Fry $11.99 - Mixed vegetables with tofu
Beef Burger $15.99 - Angus beef patty with cheese
```

With "Vegan Only" filter, it should show: "Vegan Buddha Bowl" and "Vegetable Stir Fry"
With "Vegetarian Only" filter, it should show: "Vegan Buddha Bowl", "Vegetable Stir Fry", "Caesar Salad", and "Cheese Pizza"

## LLM vs Keyword Comparison

| Feature | LLM Classification | Keyword Matching |
|---------|-------------------|------------------|
| **Accuracy** | High - understands context | Medium - relies on labels |
| **Examples** | "Beyond Burger" → Vegan | Needs "vegan" keyword |
| **Edge Cases** | Handles "mock duck", "plant milk" | May miss unlabeled items |
| **Cost** | One API call per menu | Free |
| **Speed** | Smart (analyzes whole menu) | Instant |
| **Approach** | LLM extracts matching items | Keyword filtering |

### LLM Examples:
- ✅ "Tofu Pad Thai with vegetables" → Vegan (understands tofu is plant-based)
- ✅ "Black Bean Burger" → Vegan (recognizes beans as plant-based)
- ✅ "Caesar Salad with parmesan" → Vegetarian (no meat, has dairy)
- ❌ "Grilled Chicken Breast" → Neither (contains meat)
- ❌ "Grilled Salmon" → Neither (salmon is fish, not vegetarian)
- ❌ "Shrimp Scampi" → Neither (shrimp is seafood, not vegan)

## How the Filtering Logic Works

### LLM-Powered Classification (When Enabled)
Uses OpenAI's GPT models to analyze entire menu text and extract only matching items:
- **Whole Menu Analysis**: LLM reads the entire menu and finds items matching your criteria
- **Smart Extraction**: Identifies menu items and prices from unstructured text
- **Contextual Understanding**: Considers the full menu context for better accuracy
- **One API Call**: Processes entire menu in a single request (most efficient!)

### Keyword-Based Classification (Fallback)
Traditional keyword matching for basic functionality:

### Vegan Keywords (items to include):
- "vegan", "plant-based", "plant based"
- "no dairy", "dairy-free"
- "no eggs", "egg-free"

### Non-Vegan Keywords (items to exclude):
- "beef", "chicken", "pork", "fish", "seafood"
- "salmon", "tuna", "shrimp", "crab", "lobster"
- "cheese", "milk", "butter", "cream", "egg"
- "bacon", "sausage", "ham", "steak"

### Vegetarian Logic:
- Shows items labeled as vegetarian/vegan
- Shows items that don't contain meat keywords
- May include dairy and eggs

## Limitations

- Relies on menu descriptions being accurate
- May miss items that aren't clearly labeled
- Works best with structured menu text that includes prices
- Web scraping depends on the website's structure

## Next Steps

If you'd like to extend this app, you could:
- Add more sophisticated text analysis
- Support for specific restaurant chains
- Export filtered menus as PDF
- Add nutritional information lookup