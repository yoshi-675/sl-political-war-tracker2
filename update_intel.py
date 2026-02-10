import os
import json
import feedparser
import google.generativeai as genai
from datetime import datetime
import pytz
import time

# 1. Setup Gemini API
# GitHub Secrets වලින් API Key එක ගනී
if "GEMINI_API_KEY" not in os.environ:
    print("Error: GEMINI_API_KEY not found. Please add it to GitHub Secrets.")
    exit(1)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# 2. News Sources (ලංකාවේ ප්‍රධාන පුවත් අඩවි)
rss_urls = [
    "http://www.adaderana.lk/rss.php",
    "https://www.dailymirror.lk/RSS_Feeds/breaking-news",
    "https://www.newsfirst.lk/feed/",
    "https://colombogazette.com/feed/"
]

def get_intel():
    print("📡 Intercepting signals (Fetching News)...")
    combined_text = ""
    raw_items = []
    
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            # වෙබ් අඩවියකින් පුවත් 4 බැගින් ගනී (වැඩිපුර ගත්තොත් AI එකට දරාගන්න බැරි වෙයි)
            for entry in feed.entries[:4]:
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
        except Exception as e:
            print(f"⚠️ Signal lost from {url}: {e}")
            
    return combined_text, raw_items

def analyze_battlefield(news_text):
    print("🧠 Engaging Neural Engine (AI Analysis)...")
    
    # AI එකට දෙන උපදෙස් (System Prompt)
    prompt = f"""
    You are a military-grade political intelligence AI analyzing Sri Lanka.
    
    The Players:
    1. ANURA (Govt): NPP, JVP, President, Government, Dissanayake, AKD
    2. DILITH (Challenger): MJP, Dilith, Sarvajana, Star, Derana
    3. SAJITH (Opposition): SJB, Opposition Leader, Premadasa, Samagi
    4. NAMAL (Dynasty): SLPP, Pohottuwa, Rajapaksa, Mahinda
    5. RANIL (Veteran): UNP, Wickremesinghe, Ex-President, Gas Cylinder

    Analyze these headlines:
    {news_text}

    RETURN JSON matching this EXACT schema. Do not use Markdown.
    {{
        "war_status": {{
            "intensity": (float 0.0-10.0),
            "alert_status": "GREEN" or "ORANGE" or "RED",
            "dominant_player": "Name",
            "crisis_level": "Stable" or "Volatile"
        }},
        "player_stats": {{
            "anura": {{ "media_share": (int %), "sentiment_score": (float -1.0 to 1.0), "mentions": (int), "attack_ratio": (float 0-1), "defense_ratio": (float 0-1) }},
            "dilith": {{ "media_share": (int %), "sentiment_score": (float), "mentions": (int), "attack_ratio": (float), "defense_ratio": (float) }},
            "sajith": {{ "media_share": (int %), "sentiment_score": (float), "mentions": (int), "attack_ratio": (float), "defense_ratio": (float) }},
            "namal": {{ "media_share": (int %), "sentiment_score": (float), "mentions": (int), "attack_ratio": (float), "defense_ratio": (float) }},
            "ranil": {{ "media_share": (int %), "sentiment_score": (float), "mentions": (int), "attack_ratio": (float), "defense_ratio": (float) }}
        }},
        "gap_scores": {{
            "anura": (float 0-10), "dilith": (float), "sajith": (float), "namal": (float), "ranil": (float)
        }},
        "fear_levels": {{
            "anura": (float 0-1), "dilith": (float), "sajith": (float), "namal": (float), "ranil": (float)
        }},
        "war_dynamics": {{
             "anura": {{ "dilith": (int), "sajith": (int), "namal": (int), "ranil": (int) }},
             "dilith": {{ "anura": (int), "sajith": (int), "namal": (int), "ranil": (int) }},
             "sajith": {{ "anura": (int), "dilith": (int), "namal": (int), "ranil": (int) }},
             "namal": {{ "anura": (int), "dilith": (int), "sajith": (int), "ranil": (int) }},
             "ranil": {{ "anura": (int), "dilith": (int), "sajith": (int), "namal": (int) }}
        }},
        "ai_predictions": {{
            "anura": {{ "move": "Prediction", "confidence": (float), "timing": "24h" }},
            "dilith": {{ "move": "Prediction", "confidence": (float), "timing": "24h" }},
            "sajith": {{ "move": "Prediction", "confidence": (float), "timing": "24h" }},
            "namal": {{ "move": "Prediction", "confidence": (float), "timing": "24h" }},
            "ranil": {{ "move": "Prediction", "confidence": (float), "timing": "24h" }},
            "coalition": {{ "formation_probability": (float), "likely_leader": "Name" }},
            "crisis_risk": {{ "probability": (int), "timeline": "text", "triggers": ["trigger1"] }}
        }}
    }}
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    # JSON එක සුද්ද කිරීම (Markdown අයින් කිරීම)
    cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(cleaned_text)

# 3. Main Execution
try:
    news_text, raw_news = get_intel()
    
    if not news_text:
        print("❌ No news found.")
        exit()
        
    data = analyze_battlefield(news_text)
    
    # Metadata එකතු කිරීම (වෙලාව සහ දිනය)
    tz = pytz.timezone('Asia/Colombo')
    data['metadata'] = {
        "generated_at": datetime.now(tz).isoformat(),
        "unique_articles": len(raw_news)
    }
    
    # Headlines ලස්සනට හදාගැනීම (Keyword matching)
    processed_headlines = []
    keywords = {
        'anura': ['anura', 'npp', 'jvp', 'president', 'dissanayake', 'govt', 'government', 'akd'],
        'dilith': ['dilith', 'mjp', 'sarvajana', 'jayaweera', 'star', 'derana'],
        'sajith': ['sajith', 'sjb', 'opposition', 'premadasa', 'samagi'],
        'namal': ['namal', 'slpp', 'pohottuwa', 'rajapaksa', 'mahinda'],
        'ranil': ['ranil', 'unp', 'wickremesinghe', 'ex-president', 'gas cylinder']
    }
    
    for item in raw_news:
        mentions = {}
        title_lower = item['title'].lower()
        
        # එක් එක් Player ගේ නම Headline එකේ තියෙනවද බැලීම
        for p, keys in keywords.items():
            mentions[p] = any(k in title_lower for k in keys)
            
        # Sentiment එක නිකන්ම Check කිරීම (Positive/Negative වචන වලින්)
        sentiment = 'neutral'
        if any(x in title_lower for x in ['crash', 'crisis', 'fail', 'protest', 'warn', 'danger', 'loss']): sentiment = 'negative'
        if any(x in title_lower for x in ['win', 'success', 'record', 'agree', 'boost', 'victory']): sentiment = 'positive'

        processed_headlines.append({
            "title": item['title'],
            "source": item['source'],
            "language": "en",
            "sentiment": sentiment,
            "mentions": mentions
        })
    
    data['recent_headlines'] = processed_headlines

    # data ෆෝල්ඩරය නැත්නම් හදනවා
    os.makedirs('data', exist_ok=True)
    
    # data/political_data.json ලෙස Save කිරීම
    with open('data/political_data.json', 'w') as f:
        json.dump(data, f, indent=4)
        
    print("✅ Intelligence Updated Successfully.")

except Exception as e:
    print(f"💥 Error: {e}")
