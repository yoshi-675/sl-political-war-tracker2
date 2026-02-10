import os
import json
import feedparser
import google.generativeai as genai
from datetime import datetime
import pytz
import random

# 1. API Key Check
if "GEMINI_API_KEY" not in os.environ:
    print("Error: GEMINI_API_KEY not found.")
    exit(1)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 2. News Sources
rss_urls = [
    "http://www.adaderana.lk/rss.php",
    "https://www.dailymirror.lk/RSS_Feeds/breaking-news",
    "https://www.newsfirst.lk/feed/",
    "https://colombogazette.com/feed/"
]

def get_intel():
    print("📡 Fetching News...")
    combined_text = ""
    raw_items = []
    
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Top 5 per site
                title = entry.title.replace('"', "'").strip()
                source = url.split('.')[1].title()
                if "adaderana" in url: source = "AdaDerana"
                
                combined_text += f"- [{source}] {title}\n"
                
                raw_items.append({
                    "title": title,
                    "source": source,
                    "link": getattr(entry, 'link', '#'),
                    "pubDate": getattr(entry, 'published', '')
                })
        except:
            continue
    return combined_text, raw_items

def analyze_battlefield(news_text):
    print("🧠 AI Analysis...")
    prompt = f"""
    Analyze the Sri Lanka political situation based on these headlines.
    
    PLAYERS & THEIR KEYWORDS (Count these!):
    1. ANURA: Anura, NPP, JVP, President, Government, AKD, Dissanayake
    2. DILITH: Dilith, MJP, Sarvajana, Star, Jayaweera, Mawbima
    3. SAJITH: Sajith, SJB, Opposition, Premadasa, Samagi
    4. NAMAL: Namal, SLPP, Pohottuwa, Rajapaksa, Mahinda
    5. RANIL: Ranil, UNP, Wickremesinghe, Ex-President

    HEADLINES:
    {news_text}

    TASK:
    Generate a JSON object exactly matching the schema below.
    IMPORTANT: Even if specific news is missing, ESTIMATE values based on general context. DO NOT LEAVE ZEROS unless absolutely silent.
    
    JSON SCHEMA:
    {{
        "war_status": {{
            "intensity": (float 0.0-10.0), "alert_status": "GREEN/ORANGE/RED", 
            "dominant_player": "Name", "crisis_level": "Stable/Volatile"
        }},
        "player_stats": {{
            "anura": {{ "media_share": (int %), "sentiment_score": (float -1 to 1), "mentions": (int), "attack_ratio": (float 0-1), "defense_ratio": (float 0-1) }},
            "dilith": {{ "media_share": (int %), "sentiment_score": (float), "mentions": (int), "attack_ratio": (float), "defense_ratio": (float) }},
            "sajith": {{ "media_share": (int %), "sentiment_score": (float), "mentions": (int), "attack_ratio": (float), "defense_ratio": (float) }},
            "namal": {{ "media_share": (int %), "sentiment_score": (float), "mentions": (int), "attack_ratio": (float), "defense_ratio": (float) }},
            "ranil": {{ "media_share": (int %), "sentiment_score": (float), "mentions": (int), "attack_ratio": (float), "defense_ratio": (float) }}
        }},
        "gap_scores": {{ "anura": (float 0-10), "dilith": (float), "sajith": (float), "namal": (float), "ranil": (float) }},
        "fear_levels": {{ "anura": (float 0-1), "dilith": (float), "sajith": (float), "namal": (float), "ranil": (float) }},
        "war_dynamics": {{
             "anura": {{ "dilith": (int), "sajith": (int), "namal": (int), "ranil": (int) }},
             "dilith": {{ "anura": (int), "sajith": (int), "namal": (int), "ranil": (int) }},
             "sajith": {{ "anura": (int), "dilith": (int), "namal": (int), "ranil": (int) }},
             "namal": {{ "anura": (int), "dilith": (int), "sajith": (int), "ranil": (int) }},
             "ranil": {{ "anura": (int), "dilith": (int), "sajith": (int), "namal": (int) }}
        }},
        "ai_predictions": {{
            "anura": {{ "move": "Text", "confidence": (float), "timing": "24h" }},
            "dilith": {{ "move": "Text", "confidence": (float), "timing": "24h" }},
            "sajith": {{ "move": "Text", "confidence": (float), "timing": "24h" }},
            "namal": {{ "move": "Text", "confidence": (float), "timing": "24h" }},
            "ranil": {{ "move": "Text", "confidence": (float), "timing": "24h" }},
            "coalition": {{ "formation_probability": (float), "likely_leader": "Name" }},
            "crisis_risk": {{ "probability": (int), "timeline": "text", "triggers": ["text"] }}
        }}
    }}
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    return json.loads(response.text.replace('```json', '').replace('```', '').strip())

# 3. Execution
try:
    news_text, raw_news = get_intel()
    if not news_text: 
        print("No news found")
        exit()
        
    data = analyze_battlefield(news_text)
    
    # Metadata
    tz = pytz.timezone('Asia/Colombo')
    data['metadata'] = { "generated_at": datetime.now(tz).isoformat(), "unique_articles": len(raw_news) }
    
    # ADVANCED KEYWORD MATCHING FOR HEADLINES
    processed_headlines = []
    keywords = {
        'anura': ['anura', 'npp', 'jvp', 'president', 'dissanayake', 'govt', 'government'],
        'dilith': ['dilith', 'mjp', 'sarvajana', 'jayaweera', 'star'],
        'sajith': ['sajith', 'sjb', 'opposition', 'premadasa', 'samagi'],
        'namal': ['namal', 'slpp', 'pohottuwa', 'rajapaksa', 'mahinda'],
        'ranil': ['ranil', 'unp', 'wickremesinghe', 'ex-president']
    }
    
    for item in raw_news:
        mentions = {}
        title_lower = item['title'].lower()
        for p, keys in keywords.items():
            mentions[p] = any(k in title_lower for k in keys)
            
        sentiment = 'neutral'
        if any(x in title_lower for x in ['crash', 'crisis', 'fail', 'protest', 'warn']): sentiment = 'negative'
        if any(x in title_lower for x in ['win', 'success', 'record', 'agree']): sentiment = 'positive'

        processed_headlines.append({
            "title": item['title'],
            "source": item['source'],
            "language": "en",
            "sentiment": sentiment,
            "mentions": mentions
        })
    
    data['recent_headlines'] = processed_headlines

    os.makedirs('data', exist_ok=True)
    with open('data/political_data.json', 'w') as f:
        json.dump(data, f, indent=4)
    print("✅ Intelligence Updated.")

except Exception as e:
    print(f"Error: {e}")
