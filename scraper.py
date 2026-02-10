import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def scrape_news():
    """Simple news scraper"""
    print("Starting scraper...")
    
    # Try to get news from AdaDerana
    try:
        url = "https://www.adaderana.lk/news.php"
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = []
        # Find all headlines
        for item in soup.find_all(['h2', 'h3'])[:10]:
            text = item.get_text(strip=True)
            if len(text) > 20:
                articles.append({
                    'title': text,
                    'source': 'adaderana',
                    'time': datetime.now().isoformat()
                })
        
        print(f"Found {len(articles)} articles")
        
        # Save to file
        os.makedirs('data', exist_ok=True)
        with open('data/news.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print("Saved successfully!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        # Create empty file even if error
        os.makedirs('data', exist_ok=True)
        with open('data/news.json', 'w') as f:
            json.dump([], f)
        return False

if __name__ == '__main__':
    scrape_news()
