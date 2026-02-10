import os
import json
import feedparser
import google.generativeai as genai
from datetime import datetime, timedelta
import pytz

# 1. API Setup
if "GEMINI_API_KEY" not in os.environ:
    print("Error: GEMINI_API_KEY not found.")
    exit(1)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 2. File Paths
HISTORY_FILE = 'data/history.json'
CURRENT_FILE = 'data/political_data.json'

# 3. News Sources
rss_urls = [
    "http://www.adaderana.lk/rss.php",
    "https://www.dailymirror.lk/RSS_Feeds/breaking-news",
    "https://www.newsfirst.lk/feed/",
    "https://colombogazette.com/feed/"
]

def get_news():
    print("📡 Fetching Today's News...")
    combined_text = ""
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                combined_text += f"- {entry.title}\n"
        except:
            continue
    return combined_text

def generate_past_history():
    print("📜 History file missing. Asking AI to reconstruct past data (Sep 2024 - Today)...")
    
    prompt = """
    You are a political data archivist. 
    Create a JSON dataset of Sri Lanka's political stability trend from September 23, 2024 (Anura Kumara's victory) to TODAY.
    
    Select key dates/events (approx 1 entry per 2 weeks + major events).
    
    Return a JSON ARRAY of objects. Schema:
    [
        {
            "date": "YYYY-MM-DD",
            "event": "Short Event Name (e.g., IMF Approval, Budget 2025)",
            "gap_score": (float 1.0-10.0, rising means dissatisfaction),
            "intensity": (float 1.0-10.0),
            "dominant_player": "Anura" or "Dilith" or "Sajith" or "Namal"
        },
        ...
    ]
    Make the data realistic based on actual Sri Lankan history.
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    try:
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return []

def analyze_today(news_text):
    print("🧠 Analyzing Today's Situation...")
    
    prompt = f"""
    Analyze today's news headlines in Sri Lanka:
    {news_text}
    
    1. Generate current status JSON (Player stats, etc).
    2. Generate a single history entry object for TODAY.
    
    Output JSON Schema:
    {{
        "dashboard_data": {{
             "war_status": {{ "intensity": (float), "alert_status": "TEXT", "dominant_player": "TEXT" }},
             "player_stats": {{ "anura": {{ "media_share": (int), "sentiment": (float) }}, ...other players... }},
             "gap_scores": {{ "anura": (float), ...others... }}
        }},
        "history_entry": {{
            "date": "TODAY_DATE",
            "event": "Main Headline Topic",
            "gap_score": (float),
            "intensity": (float),
            "dominant_player": "Name"
        }}
    }}
    Use estimated data if news is scarce. No zeros.
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    return json.loads(response.text.replace('```json', '').replace('```', '').strip())

# --- MAIN EXECUTION ---
try:
    os.makedirs('data', exist_ok=True)
    
    # Step 1: Handle History (Memory)
    if os.path.exists(HISTORY_FILE):
        print("📂 Loading existing history...")
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    else:
        # If no file exists, AI generates the timeline from 2024 Sep
        history = generate_past_history()
    
    # Step 2: Analyze Today
    news_text = get_news()
    if not news_text: news_text = "No major news. Assume stable situation."
    
    analysis = analyze_today(news_text)
    
    # Step 3: Update History
    # Set today's date
    tz = pytz.timezone('Asia/Colombo')
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    
    # Check if today already exists to avoid duplicates
    if not any(d['date'] == today_str for d in history):
        today_entry = analysis['history_entry']
        today_entry['date'] = today_str # Ensure date is correct
        history.append(today_entry)
        print(f"➕ Added entry for {today_str}")
    
    # Keep only last 60 entries to save space
    if len(history) > 60: history = history[-60:]
    
    # Step 4: Inject History into Dashboard Data
    # We send the history array to the frontend so it can draw charts
    final_data = analysis['dashboard_data']
    final_data['history_trend'] = history
    final_data['metadata'] = { "generated_at": datetime.now(tz).isoformat() }

    # Step 5: Save Files
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)
        
    with open(CURRENT_FILE, 'w') as f:
        json.dump(final_data, f, indent=4)
        
    print("✅ Intelligence & History Updated Successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
