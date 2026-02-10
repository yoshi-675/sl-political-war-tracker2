#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, timedelta
import time

# ==================== CONFIGURATION ====================

PLAYERS = {
    'anura': {
        'names': ['anura', 'kumara', 'dissanayake', 'akd', 'npp', 'jvp', 'අනුර', 'දිසානායක', 'ජවිපෙ', 'පොදුජන පෙරමුණ'],
        'party': 'NPP',
        'role': 'President',
        'color': 'green',
        'fear_triggers': ['aragalaya', 'ranil 2.0', 'imf puppet', 'fail', 'අසමත්', 'පාවී']
    },
    'dilith': {
        'names': ['dilith', 'jayaweera', 'mjp', 'derana', 'sarwajana', 'දිලිත්', 'ජයවීර', 'මජා පෙ', 'දෙරණ'],
        'party': 'MJP',
        'role': 'Opposition Leader',
        'color': 'red',
        'fear_triggers': ['corrupt', 'media mafia', 'rajapaksa puppet', 'චීන', 'අල්ලස']
    },
    'sajith': {
        'names': ['sajith', 'premadasa', 'sjb', 'samagi', 'සජිත්', 'ප්‍රේමදාස', 'සමගි', 'සජබ'],
        'party': 'SJB',
        'role': 'Opposition Leader (Official)',
        'color': 'yellow',
        'fear_triggers': ['loser', 'weak', 'cooperative', 'irrelevant', 'පරාජය', 'දුර්වල']
    },
    'namal': {
        'names': ['namal', 'rajapaksa', 'slpp', 'mahinda', 'gotabaya', 'basil', 'ගෝඨා', 'මහින්ද', 'රාජපක්ෂ', 'නාමල්'],
        'party': 'SLPP',
        'role': 'Dynasty Scion',
        'color': 'blue',
        'fear_triggers': ['corrupt', 'dynasty', '2022 crisis', 'family rule', 'වංචා', 'රාජවංශය']
    },
    'ranil': {
        'names': ['ranil', 'wickremesinghe', 'unp', 'wickremasinghe', 'රනිල්', 'වික්‍රමසිංහ', 'පැරණි ජනපති', 'එක්සත් ජාතික පක්ෂය'],
        'party': 'UNP',
        'role': 'Former President (Jailed)',
        'color': 'purple',
        'fear_triggers': ['old guard', 'failed', 'imf', 'austerity', 'අසමත්', 'පැරණි']
    }
}

NEWS_SOURCES = {
    'aruna': 'https://aruna.lk/',
    'adaderana-sinhala': 'https://www.adaderana.lk/sinhala/news.php',
    'adaderana-english': 'https://www.adaderana.lk/news.php',
    'newsfirst': 'https://www.newsfirst.lk/',
    'news19': 'https://news19.lk/',
    'dailymirror': 'https://www.dailymirror.lk/news',
    'themorning': 'https://www.themorning.lk'
}

# ==================== CORE FUNCTIONS ====================

def scrape_with_headers(url):
    """Scrape with realistic browser headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,si;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  Error: {e}")
        return None

def detect_players(text):
    """Detect which players are mentioned in text"""
    text_lower = text.lower()
    mentions = {}
    
    for player, data in PLAYERS.items():
        score = 0
        for name in data['names']:
            if name in text_lower:
                score += 3 if len(name) > 4 else 1
        mentions[player] = score > 0
    
    return mentions

def analyze_sentiment_advanced(text):
    """Advanced sentiment analysis for Sinhala + English"""
    text_lower = text.lower()
    
    # Positive indicators (English + Sinhala)
    positive = [
        'win', 'victory', 'success', 'good', 'great', 'excellent', 'superb', 'achieve',
        'deliver', 'promise kept', 'strong', 'leader', 'hope', 'change',
        'ජයග්‍රහණය', 'සුපිරි', 'නියම', 'ශක්තිමත්', 'ජනප්‍රිය', 'වෙනස', 'සාර්ථක'
    ]
    
    # Negative indicators
    negative = [
        'fail', 'loss', 'bad', 'worst', 'corrupt', 'lie', 'cheat', 'disaster',
        'crisis', 'broken', 'useless', 'pathetic', 'weak', 'shame', 'scandal',
        'පාවී', 'අසමත්', 'වැරදි', 'වංචා', 'දුර්වල', 'අපරාධ', 'අර්බුදය', 'විනාශය'
    ]
    
    # Crisis words
    crisis = [
        'protest', 'strike', 'uprising', 'revolution', 'topple', 'overthrow',
        'emergency', 'crisis', 'collapse', 'imf', 'tariff', 'unemployment', 'inflation',
        'උද්ඝෝෂණ', 'වර්ජන', 'අර්බුදය', 'අත්හිටුවීම', 'පෙරළීම', 'ආපදාව'
    ]
    
    # Power dynamics
    attack_words = ['slams', 'blasts', 'criticizes', 'attacks', 'destroys', 'exposes',
                   'condemns', 'warns', 'threatens', 'ප්‍රහාරය', 'විවේචනය', 'චෝදනා', 'අනතුරු']
    defense_words = ['defends', 'denies', 'clarifies', 'explains', 'justifies',
                    'පිළිතුර', 'පිළිගැනීම', 'සාධාරණීකරණය']
    
    # Count occurrences
    pos_count = sum(1 for w in positive if w in text_lower)
    neg_count = sum(1 for w in negative if w in text_lower)
    crisis_count = sum(1 for w in crisis if w in text_lower)
    attack_count = sum(1 for w in attack_words if w in text_lower)
    defense_count = sum(1 for w in defense_words if w in text_lower)
    
    # Calculate base sentiment (-1 to 1)
    if pos_count > neg_count:
        sentiment = 'positive'
        score = min(0.5 + (pos_count - neg_count) * 0.1, 1.0)
    elif neg_count > pos_count:
        sentiment = 'negative'
        score = max(0.5 - (neg_count - pos_count) * 0.1, 0.0)
    else:
        sentiment = 'neutral'
        score = 0.5
    
    # Determine power dynamic
    if attack_count > defense_count:
        power_dynamic = 'attacking'
    elif defense_count > attack_count:
        power_dynamic = 'defending'
    else:
        power_dynamic = 'neutral'
    
    # Calculate intensity (0-1)
    intensity = min(1.0, (pos_count + neg_count + crisis_count) * 0.05)
    
    return {
        'sentiment': sentiment,
        'score': round(score, 2),
        'crisis_indicators': crisis_count,
        'power_dynamic': power_dynamic,
        'intensity': round(intensity, 2),
        'positive_signals': pos_count,
        'negative_signals': neg_count
    }

def scrape_source(name, url):
    """Scrape a single news source"""
    print(f"\n📰 Scraping {name}...")
    html = scrape_with_headers(url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    
    # Different parsing for different sites
    selectors = {
        'aruna': ['h3.entry-title a', 'h2.entry-title a', '.post-title a'],
        'adaderana-sinhala': ['h2', 'h3', '.news-title', '.title'],
        'adaderana-english': ['h2', 'h3', '.news-title'],
        'newsfirst': ['h2', 'h3', '.news-title', '.title'],
        'news19': ['h2', 'h3', '.entry-title', '.post-title'],
        'dailymirror': ['h2', 'h3', '.title'],
        'themorning': ['h2', 'h3', '.article-title']
    }
    
    selectors_to_try = selectors.get(name, ['h2', 'h3'])
    
    for selector in selectors_to_try:
        items = soup.select(selector) if '[' in selector else soup.find_all(selector)
        for item in items[:15]:
            # Get text
            if hasattr(item, 'get_text'):
                text = item.get_text(strip=True)
            else:
                text = item.text if hasattr(item, 'text') else str(item)
            
            # Clean and validate
            if len(text) > 20 and len(text) < 300:
                # Skip common junk
                skip_words = ['home', 'about', 'contact', 'privacy', 'cookie', 'මුල් පිටුව']
                if not any(skip in text.lower() for skip in skip_words):
                    articles.append({
                        'title': text,
                        'source': name,
                        'language': 'si' if '-sinhala' in name or name in ['aruna', 'news19'] else 'en',
                        'scraped_at': datetime.now().isoformat()
                    })
        
        if len(articles) >= 5:
            break  # Got enough, stop trying selectors
    
    print(f"  ✅ Found {len(articles)} articles")
    return articles

# ==================== ADVANCED ANALYTICS ====================

def calculate_gap_score(player_stats, articles):
    """
    Gap Score = Promise - Delivery + External Pressure
    Measures how much a leader is underperforming expectations
    """
    gap_scores = {}
    
    for player, stats in player_stats.items():
        mentions = stats['mentions']
        if mentions == 0:
            gap_scores[player] = 5.0  # Neutral if no data
            continue
        
        # Promise indicators (will, going to, plan)
        promise_words = ['promise', 'will', 'pledge', 'plan', 'going to', 'අපේක්ෂාව', 'පොරොන්දු']
        promises = sum(1 for a in stats['headlines'] 
                      if any(w in a['title'].lower() for w in promise_words))
        
        # Delivery indicators (done, completed, launched)
        delivery_words = ['done', 'completed', 'launched', 'implemented', 'achieved',
                         'කළා', 'සම්පූර්ණ', 'අරඹයි', 'සාර්ථක']
        deliveries = sum(1 for a in stats['headlines']
                        if any(w in a['title'].lower() for w in delivery_words))
        
        # External pressure (attacks from others)
        attacks_received = stats['negative']
        
        # Calculate gap
        promise_gap = max(0, promises - deliveries)
        pressure_score = attacks_received / max(1, mentions) * 3
        
        gap = min(10, 5.0 + promise_gap * 0.8 + pressure_score)
        gap_scores[player] = round(gap, 1)
    
    return gap_scores

def calculate_war_dynamics(player_stats, articles):
    """Calculate who is attacking whom"""
    relationships = {p: {op: 0 for op in player_stats if op != p} 
                    for p in player_stats}
    
    for article in articles:
        mentions = detect_players(article['title'])
        sentiment = analyze_sentiment_advanced(article['title'])
        
        # Find mentioned players
        mentioned = [p for p, m in mentions.items() if m]
        
        # If 2+ players mentioned, check for attack language
        if len(mentioned) >= 2 and sentiment['power_dynamic'] == 'attacking':
            # Simple heuristic: first mentioned is attacker
            # This can be improved with NLP
            attacker = mentioned[0]
            for target in mentioned[1:]:
                if attacker != target:
                    relationships[attacker][target] += 1
    
    return relationships

def calculate_fear_levels(player_stats, gap_scores):
    """Calculate fear/stress levels for each player"""
    fear_levels = {}
    
    for player, stats in player_stats.items():
        fear = 0.5  # Base level
        
        # Higher gap = higher fear
        gap = gap_scores.get(player, 5.0)
        fear += (gap - 5) * 0.05
        
        # More negative coverage = higher fear
        neg_ratio = stats['negative'] / max(1, stats['mentions'])
        fear += neg_ratio * 0.3
        
        # Crisis exposure
        fear += min(0.2, stats['crisis_exposure'] * 0.02)
        
        fear_levels[player] = round(min(1.0, max(0.0, fear)), 2)
    
    return fear_levels

def generate_ai_predictions(player_stats, gap_scores, fear_levels, war_dynamics):
    """Generate AI predictions for next moves"""
    predictions = {}
    
    # Anura prediction
    anura_gap = gap_scores.get('anura', 5.0)
    anura_fear = fear_levels.get('anura', 0.5)
    
    if anura_gap > 6.5 or anura_fear > 0.75:
        predictions['anura'] = {
            'move': 'Emergency populist measure (fuel subsidy/teacher wage hike) + media blitz',
            'confidence': 0.87,
            'timing': '24-48 hours',
            'trigger': f'Gap Score {anura_gap}, Fear Level {anura_fear}',
            'expected_outcome': 'Temporary approval boost, opposition deflection'
        }
    elif anura_gap > 5.5:
        predictions['anura'] = {
            'move': 'Defensive parliamentary speech + blame "conspiracy"',
            'confidence': 0.79,
            'timing': '48 hours',
            'trigger': f'Rising pressure (Gap {anura_gap})',
            'expected_outcome': 'Base consolidation, neutral swing voters alienated'
        }
    else:
        predictions['anura'] = {
            'move': 'Continue IMF path, ignore opposition noise',
            'confidence': 0.72,
            'timing': 'Ongoing',
            'trigger': 'Stable metrics',
            'expected_outcome': 'Gradual erosion if economy doesn\'t improve'
        }
    
    # Dilith prediction
    dilith_momentum = player_stats['dilith']['mentions'] / max(1, sum(s['mentions'] for s in player_stats.values()))
    dilith_sentiment = player_stats['dilith']['sentiment_score']
    
    if dilith_momentum > 0.25 and dilith_sentiment > 0.1:
        predictions['dilith'] = {
            'move': 'Formalize opposition coalition, demand snap elections',
            'confidence': 0.84,
            'timing': '1-2 weeks',
            'trigger': f'Strong momentum ({dilith_momentum:.0%} share, +{dilith_sentiment} sentiment)',
            'expected_outcome': 'Sajith/Namal forced to join or become irrelevant'
        }
    elif dilith_momentum > 0.20:
        predictions['dilith'] = {
            'move': 'Escalate "Ranil 2.0" attacks, Budget day offensive',
            'confidence': 0.81,
            'timing': 'Next week',
            'trigger': 'Rising trend',
            'expected_outcome': 'Gap Score increase for Anura'
        }
    else:
        predictions['dilith'] = {
            'move': 'Consolidate media gains, prepare for long game',
            'confidence': 0.68,
            'timing': '2-4 weeks',
            'trigger': 'Momentum building',
            'expected_outcome': 'Gradual narrative shift'
        }
    
    # Coalition prediction
    opposition_united = (war_dynamics.get('dilith', {}).get('sajith', 0) > 0 or
                        war_dynamics.get('dilith', {}).get('namal', 0) > 0)
    
    opposition_strength = (player_stats['dilith']['mentions'] + 
                          player_stats['sajith']['mentions'] + 
                          player_stats['namal']['mentions'])
    total_strength = sum(s['mentions'] for s in player_stats.values())
    
    if opposition_strength > total_strength * 0.6 and not opposition_united:
        coalition_prob = 0.78
        timeline = '2-3 weeks'
        leader = 'dilith'
    elif opposition_strength > total_strength * 0.5:
        coalition_prob = 0.65
        timeline = '1-2 months'
        leader = 'dilith (contested)'
    else:
        coalition_prob = 0.42
        timeline = 'Uncertain'
        leader = 'none'
    
    predictions['coalition'] = {
        'formation_probability': coalition_prob,
        'timeline': timeline,
        'likely_leader': leader,
        'obstacles': ['Sajith-Namal rivalry', 'Dilith dominance fears', 'Anura divide-and-rule']
    }
    
    # Crisis prediction
    avg_gap = sum(gap_scores.values()) / len(gap_scores)
    max_fear = max(fear_levels.values())
    crisis_risk = min(100, (avg_gap - 4) * 10 + max_fear * 20)
    
    predictions['crisis_risk'] = {
        'probability': round(crisis_risk, 1),
        'triggers': ['US tariff shock', 'IMF review failure', 'Mass protest'],
        'timeline': '30 days' if crisis_risk > 60 else '60 days' if crisis_risk > 40 else '90 days'
    }
    
    return predictions

# ==================== MAIN EXECUTION ====================

def main():
    print("=" * 70)
    print("🇱🇰 SRI LANKA POLITICAL WAR TRACKER - ADVANCED EDITION")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Scrape all sources
    all_articles = []
    
    sources_to_scrape = [
        ('aruna', NEWS_SOURCES['aruna']),
        ('adaderana-sinhala', NEWS_SOURCES['adaderana-sinhala']),
        ('adaderana-english', NEWS_SOURCES['adaderana-english']),
        ('newsfirst', NEWS_SOURCES['newsfirst']),
        ('news19', NEWS_SOURCES['news19']),
    ]
    
    for name, url in sources_to_scrape:
        articles = scrape_source(name, url)
        all_articles.extend(articles)
        if len(sources_to_scrape) > 1:
            time.sleep(2)  # Be polite
    
    print(f"\n{'='*70}")
    print(f"TOTAL ARTICLES: {len(all_articles)}")
    print(f"{'='*70}")
    
    # Remove duplicates
    seen = set()
    unique_articles = []
    for a in all_articles:
        key = a['title'][:50]  # First 50 chars as key
        if key not in seen:
            seen.add(key)
            unique_articles.append(a)
    
    print(f"UNIQUE ARTICLES: {len(unique_articles)}")
    
    # Analyze each article
    analyzed_articles = []
    for article in unique_articles:
        mentions = detect_players(article['title'])
        sentiment = analyze_sentiment_advanced(article['title'])
        
        article['mentions'] = mentions
        article['sentiment'] = sentiment
        analyzed_articles.append(article)
    
    # Calculate player stats
    player_stats = {p: {
        'mentions': 0,
        'positive': 0,
        'negative': 0,
        'neutral': 0,
        'crisis_exposure': 0,
        'headlines': [],
        'sentiment_score': 0,
        'attack_count': 0,
        'defense_count': 0
    } for p in PLAYERS}
    
    for article in analyzed_articles:
        for player, mentioned in article['mentions'].items():
            if mentioned:
                stats = player_stats[player]
                stats['mentions'] += 1
                stats['headlines'].append({
                    'title': article['title'],
                    'source': article['source'],
                    'sentiment': article['sentiment']['sentiment']
                })
                
                if article['sentiment']['sentiment'] == 'positive':
                    stats['positive'] += 1
                elif article['sentiment']['sentiment'] == 'negative':
                    stats['negative'] += 1
                else:
                    stats['neutral'] += 1
                
                stats['crisis_exposure'] += article['sentiment']['crisis_indicators']
                
                if article['sentiment']['power_dynamic'] == 'attacking':
                    stats['attack_count'] += 1
                elif article['sentiment']['power_dynamic'] == 'defending':
                    stats['defense_count'] += 1
    
    # Calculate percentages and scores
    total_mentions = sum(s['mentions'] for s in player_stats.values())
    
    for player, stats in player_stats.items():
        if stats['mentions'] > 0:
            stats['media_share'] = round(stats['mentions'] / max(1, total_mentions) * 100, 1)
            stats['sentiment_score'] = round(
                (stats['positive'] - stats['negative']) / stats['mentions'], 2
            )
            stats['attack_ratio'] = round(stats['attack_count'] / stats['mentions'], 2)
            stats['defense_ratio'] = round(stats['defense_count'] / stats['mentions'], 2)
        else:
            stats['media_share'] = 0
            stats['sentiment_score'] = 0
            stats['attack_ratio'] = 0
            stats['defense_ratio'] = 0
    
    # Calculate advanced metrics
    print("\n📊 CALCULATING ADVANCED METRICS...")
    
    gap_scores = calculate_gap_score(player_stats, analyzed_articles)
    print(f"  Gap Scores: {gap_scores}")
    
    fear_levels = calculate_fear_levels(player_stats, gap_scores)
    print(f"  Fear Levels: {fear_levels}")
    
    war_dynamics = calculate_war_dynamics(player_stats, analyzed_articles)
    print(f"  War dynamics calculated")
    
    predictions = generate_ai_predictions(player_stats, gap_scores, fear_levels, war_dynamics)
    print(f"  AI predictions generated")
    
    # Calculate war intensity
    war_intensity = min(10, 
        sum(s['crisis_exposure'] for s in player_stats.values()) / max(1, len(analyzed_articles)) * 5 +
        sum(gap_scores.values()) / len(gap_scores) * 0.5
    )
    
    # Determine dominant narrative
    dominant = max(player_stats.items(), key=lambda x: x[1]['mentions'])[0] if total_mentions > 0 else 'none'
    
    # Build final output
    output = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'articles_scraped': len(all_articles),
            'unique_articles': len(unique_articles),
            'sources_used': len(sources_to_scrape),
            'scraping_duration': 'completed'
        },
        'war_status': {
            'intensity': round(war_intensity, 1),
            'dominant_player': dominant,
            'total_mentions': total_mentions,
            'crisis_level': 'HIGH' if war_intensity > 7 else 'MEDIUM' if war_intensity > 5 else 'LOW',
            'alert_status': 'RED' if war_intensity > 7 else 'ORANGE' if war_intensity > 5 else 'YELLOW'
        },
        'player_stats': player_stats,
        'gap_scores': gap_scores,
        'fear_levels': fear_levels,
        'war_dynamics': war_dynamics,
        'ai_predictions': predictions,
        'recent_headlines': [
            {
                'title': a['title'],
                'source': a['source'],
                'language': a['language'],
                'mentions': {p: v for p, v in a['mentions'].items() if v},
                'sentiment': a['sentiment']['sentiment']
            } for a in analyzed_articles[:20]
        ]
    }
    
    # Save to file
    os.makedirs('data', exist_ok=True)
    with open('data/political_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*70}")
    print("📈 WAR STATUS SUMMARY")
    print(f"{'='*70}")
    print(f"War Intensity: {war_intensity:.1f}/10 ({output['war_status']['crisis_level']})")
    print(f"Dominant Player: {dominant.upper()}")
    print(f"Alert: {output['war_status']['alert_status']}")
    print(f"\nPlayer Rankings:")
    for player, stats in sorted(player_stats.items(), 
                               key=lambda x: x[1]['mentions'], reverse=True):
        gap = gap_scores.get(player, 5.0)
        fear = fear_levels.get(player, 0.5)
        print(f"  {player.upper():8} | Media: {stats['media_share']:5.1f}% | "
              f"Sentiment: {stats['sentiment_score']:+.2f} | Gap: {gap:.1f} | Fear: {fear:.2f}")
    
    print(f"\n🔮 AI PREDICTIONS:")
    for player, pred in predictions.items():
        if isinstance(pred, dict) and 'move' in pred:
            print(f"  {player.upper():10} | {pred['move'][:50]}... ({pred['confidence']:.0%})")
    
    print(f"\n✅ Data saved to data/political_data.json")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
