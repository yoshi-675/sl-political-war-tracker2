import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

def scrape_with_headers(url):
    """Scrape with browser-like headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,si;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return None

def scrape_aruna():
    """Aruna.lk - Sinhala"""
    articles = []
    try:
        print("Trying Aruna.lk...")
        html = scrape_with_headers("https://aruna.lk/")
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            # Aruna uses h3 for headlines
            for item in soup.find_all('h3', class_='entry-title')[:10]:
                link = item.find('a')
                if link:
                    title = link.get_text(strip=True)
                    if len(title) > 10:
                        articles.append({
                            'title': title,
                            'source': 'aruna',
                            'language': 'si',
                            'time': datetime.now().isoformat()
                        })
            print(f"Aruna: {len(articles)} articles")
    except Exception as e:
        print(f"Aruna failed: {e}")
    return articles

def scrape_adaderana_sinhala():
    """Ada Derana Sinhala"""
    articles = []
    try:
        print("Trying Ada Derana Sinhala...")
        html = scrape_with_headers("https://www.adaderana.lk/sinhala/news.php")
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            for item in soup.find_all(['h2', 'h3'])[:10]:
                text = item.get_text(strip=True)
                if len(text) > 20 and 'අද දෙරණ' not in text:
                    articles.append({
                        'title': text,
                        'source': 'adaderana-sinhala',
                        'language': 'si',
                        'time': datetime.now().isoformat()
                    })
            print(f"Ada Derana Sinhala: {len(articles)} articles")
    except Exception as e:
        print(f"Ada Derana Sinhala failed: {e}")
    return articles

def scrape_newsfirst():
    """NewsFirst Sri Lanka"""
    articles = []
    try:
        print("Trying NewsFirst...")
        html = scrape_with_headers("https://www.newsfirst.lk/")
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            for item in soup.find_all(['h2', 'h3', '.news-title', '.title'])[:10]:
                text = item.get_text(strip=True)
                if len(text) > 20:
                    articles.append({
                        'title': text,
                        'source': 'newsfirst',
                        'language': 'en',
                        'time': datetime.now().isoformat()
                    })
            print(f"NewsFirst: {len(articles)} articles")
    except Exception as e:
        print(f"NewsFirst failed: {e}")
    return articles

def scrape_news19():
    """News19 Sri Lanka"""
    articles = []
    try:
        print("Trying News19...")
        html = scrape_with_headers("https://news19.lk/")
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            for item in soup.find_all(['h2', 'h3', '.entry-title', '.post-title'])[:10]:
                text = item.get_text(strip=True)
                if len(text) > 20:
                    articles.append({
                        'title': text,
                        'source': 'news19',
                        'language': 'si',
                        'time': datetime.now().isoformat()
                    })
            print(f"News19: {len(articles)} articles")
    except Exception as e:
        print(f"News19 failed: {e}")
    return articles

def main():
    print("="*60)
    print("Sri Lanka Political News Scraper - Sinhala + English")
    print("="*60)
    
    all_articles = []
    
    # Scrape all sources
    all_articles.extend(scrape_aruna())
    time.sleep(2)
    
    all_articles.extend(scrape_adaderana_sinhala())
    time.sleep(2)
    
    all_articles.extend(scrape_newsfirst())
    time.sleep(2)
    
    all_articles.extend(scrape_news19())
    
    # Remove duplicates (same title)
    seen = set()
    unique_articles = []
    for a in all_articles:
        if a['title'] not in seen:
            seen.add(a['title'])
            unique_articles.append(a)
    
    # Fallback if empty
    if len(unique_articles) == 0:
        print("WARNING: No articles found. Using fallback.")
        unique_articles = [
            {
                'title': 'නවතම පුවත් ලබා ගැනීමට ක්‍රියාකාරී වෙමින් - Latest news loading',
                'source': 'system',
                'language': 'si',
                'time': datetime.now().isoformat()
            }
        ]
    
    # Save
    os.makedirs('data', exist_ok=True)
    with open('data/news.json', 'w', encoding='utf-8') as f:
        json.dump(unique_articles, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ TOTAL: {len(unique_articles)} unique articles saved")
    for a in unique_articles[:5]:
        lang = '🇱🇰' if a.get('language') == 'si' else '🇬🇧'
        print(f"  {lang} [{a['source']}] {a['title'][:50]}...")

if __name__ == '__main__':
    main()
