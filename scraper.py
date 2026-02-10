import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import random

def scrape_with_headers(url):
    """Scrape with browser-like headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_adaderana():
    """Try multiple Sri Lankan news sources"""
    articles = []
    
    # Source 1: AdaDerana
    try:
        print("Trying AdaDerana...")
        html = scrape_with_headers("https://www.adaderana.lk/news.php")
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            # Look for news titles
            for item in soup.find_all(['h2', 'h3', '.news-title', '.title'])[:8]:
                text = item.get_text(strip=True)
                if len(text) > 20 and len(text) < 200:
                    articles.append({
                        'title': text,
                        'source': 'adaderana',
                        'time': datetime.now().isoformat()
                    })
            print(f"AdaDerana: {len(articles)} articles")
    except Exception as e:
        print(f"AdaDerana failed: {e}")
    
    # Source 2: Daily Mirror (backup)
    if len(articles) < 3:
        try:
            print("Trying Daily Mirror...")
            time.sleep(2)  # Be polite
            html = scrape_with_headers("https://www.dailymirror.lk/news")
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                for item in soup.find_all(['h2', 'h3', '.article-title'])[:5]:
                    text = item.get_text(strip=True)
                    if len(text) > 20 and text not in [a['title'] for a in articles]:
                        articles.append({
                            'title': text,
                            'source': 'dailymirror',
                            'time': datetime.now().isoformat()
                        })
                print(f"Daily Mirror: {len(articles)} total")
        except Exception as e:
            print(f"Daily Mirror failed: {e}")
    
    # Source 3: The Morning (backup)
    if len(articles) < 3:
        try:
            print("Trying The Morning...")
            time.sleep(2)
            html = scrape_with_headers("https://www.themorning.lk")
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                for item in soup.find_all(['h2', 'h3'])[:5]:
                    text = item.get_text(strip=True)
                    if len(text) > 20 and text not in [a['title'] for a in articles]:
                        articles.append({
                            'title': text,
                            'source': 'themorning',
                            'time': datetime.now().isoformat()
                        })
                print(f"The Morning: {len(articles)} total")
        except Exception as e:
            print(f"The Morning failed: {e}")
    
    return articles

def main():
    print("="*50)
    print("Sri Lanka Political News Scraper")
    print("="*50)
    
    # Scrape news
    articles = scrape_adaderana()
    
    # If no articles, create sample data for testing
    if len(articles) == 0:
        print("WARNING: No articles scraped. Using fallback data.")
        articles = [
            {
                'title': 'Scraper active - waiting for news sources',
                'source': 'system',
                'time': datetime.now().isoformat()
            },
            {
                'title': 'Try again in 10 minutes',
                'source': 'system',
                'time': datetime.now().isoformat()
            }
        ]
    
    # Save to file
    os.makedirs('data', exist_ok=True)
    with open('data/news.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(articles)} articles to data/news.json")
    for a in articles[:3]:
        print(f"  - [{a['source']}] {a['title'][:60]}...")

if __name__ == '__main__':
    main()
