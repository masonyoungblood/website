#!/usr/bin/env python3
"""
Scrape press coverage from Altmetric news pages and save as CSV.
Similar to news_coverage.ipynb but outputs CSV format for press list generator.
"""

import os
import csv
import requests
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory
from datetime import datetime
from titlecase import titlecase
from pathlib import Path

# Set a seed for consistent language detection results.
DetectorFactory.seed = 0

# === CONFIGURATION ===

# Output CSV file path
OUTPUT_CSV = "scraped_articles.csv"

# List of Altmetric news page URLs to scrape.
ALTMETRIC_BASE_URLS = [
    "https://nature.altmetric.com/details/49134871/news",
    "https://nature.altmetric.com/details/86875450/news",
    "https://royalsociety.altmetric.com/details/67113987/news",
    "https://cambridge.altmetric.com/details/148065072/news",
    "https://plos.altmetric.com/details/50457092/news",
    "https://www.altmetric.com/details/109906728/news",
    "https://nature.altmetric.com/details/154178347/news",
    "https://www.altmetric.com/details/121359234/news",
    "https://tandf.altmetric.com/details/81579019/news",
    "https://www.altmetric.com/details/142953324/chapter/155827676/news",
    "https://royalsociety.altmetric.com/details/161515855/news",
    "https://www.altmetric.com/details/108380522/news",
    "https://oxfordjournals.altmetric.com/details/168344032/news",
    "https://plos.altmetric.com/details/166068334/news",
    "https://scienceadvances.altmetric.com/details/173863208/news",
    "https://springeropen.altmetric.com/details/163437325/news",
    "https://science.altmetric.com/details/173914272/news"
]

# OPTIONAL: Define which sources are considered important.
IMPORTANT_SOURCES = [
    "National Geographic",
    "Scientific American",
    "New York Times",
    "The Guardian",
    "El País",
    "New Scientist",
    "ABC.net.au",
    "Tech Crunch",
    "Medium US",
    "Phys.org",
    "World Economic Forum",
    "The Conversation",
    "RNZ",
    "Los Angeles Times",
    "CBC",
    "CNN News",
    "Washington Post",
    "Popular Science",
    "Futurity",
    "Yahoo! News",
    "Iflscience"
]

# === SCRAPING FUNCTIONS ===

def scrape_altmetric_news(url):
    """Scrapes a given Altmetric news page URL and returns a list of article dictionaries."""
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('article', class_='post msm')
    article_list = []
    
    for art in articles:
        a_tag = art.find('a', class_='block_link')
        if not a_tag:
            continue
        link = a_tag.get('href')
        
        img_tag = art.find('img', class_='avatar')
        image = img_tag.get('src') if img_tag else ""
        alt_text = img_tag.get('alt') if img_tag else ""
        
        h3_tag = art.find('h3')
        title = h3_tag.get_text(strip=True) if h3_tag else "No Title"
        
        dt = None
        h4_tag = art.find('h4')
        if h4_tag:
            time_tag = h4_tag.find('time')
            if time_tag and time_tag.has_attr("datetime"):
                datetime_str = time_tag["datetime"]
                if datetime_str.endswith("Z"):
                    datetime_str = datetime_str[:-1]
                try:
                    dt = datetime.fromisoformat(datetime_str)
                except Exception:
                    dt = None
            h4_text = h4_tag.get_text(strip=True)
            if ',' in h4_text:
                source, time_text = h4_text.split(',', 1)
                source = source.strip()
                time_text = time_text.strip()
            else:
                source = h4_text.strip()
                time_text = ""
        else:
            source = "Unknown"
            time_text = ""
        
        # Only include articles from important sources.
        if not any(key.lower() in source.lower() for key in IMPORTANT_SOURCES):
            continue
        
        p_tag = art.find('p', class_='summary')
        summary = p_tag.get_text(strip=True) if p_tag else ""
        
        try:
            lang = detect(title)
        except Exception:
            lang = "unknown"
        
        article_data = {
            'link': link,
            'image': image,
            'alt_text': alt_text,
            'title': titlecase(title),
            'source': source,
            'time_text': time_text,
            'summary': summary,
            'lang': lang,
            'dt': dt
        }
        article_list.append(article_data)
    
    return article_list

def scrape_altmetric_news_pages(base_url, max_pages=10):
    """Iterates through multiple pages of an Altmetric base URL and returns a list of article dictionaries."""
    all_articles = []
    for page in range(1, max_pages + 1):
        url = base_url if page == 1 else f"{base_url.rstrip('/')}/page:{page}"
        print(f"Scraping: {url}")
        try:
            articles = scrape_altmetric_news(url)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            break
        if not articles:
            break
        all_articles.extend(articles)
    return all_articles

def get_dt(article):
    """Return a datetime object from an article's 'dt' field.
       If the field is missing or invalid, return datetime.min."""
    dt_val = article.get('dt')
    if dt_val is None:
        return datetime.min
    if isinstance(dt_val, datetime):
        return dt_val
    try:
        return datetime.fromisoformat(dt_val)
    except Exception:
        return datetime.min

def save_to_csv(articles, csv_file):
    """Save articles to CSV file in the format needed for press list generator."""
    fieldnames = ['link', 'image_link', 'title', 'source', 'date', 'description']
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for article in articles:
            # Format date from time_text (e.g., "10 Feb 2025" -> "10 Feb 2025")
            # If time_text is empty, try to format from dt
            date_str = article.get('time_text', '')
            if not date_str and article.get('dt'):
                dt = get_dt(article)
                if dt != datetime.min:
                    date_str = dt.strftime('%d %b %Y')
            
            row = {
                'link': article.get('link', ''),
                'image_link': article.get('image', ''),
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'date': date_str,
                'description': article.get('summary', '')
            }
            writer.writerow(row)

# === MAIN PIPELINE ===

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    output_file = script_dir / OUTPUT_CSV
    
    all_articles = []
    
    # Scrape altmetric pages.
    for base_url in ALTMETRIC_BASE_URLS:
        scraped = scrape_altmetric_news_pages(base_url, max_pages=10)
        all_articles.extend(scraped)
    
    # Remove duplicates based on link
    seen_links = set()
    unique_articles = []
    for article in all_articles:
        link = article.get('link', '')
        if link and link not in seen_links:
            seen_links.add(link)
            unique_articles.append(article)
    
    # Filter to only English articles.
    english_articles = [a for a in unique_articles if a.get('lang', 'unknown') == 'en']
    
    # Sort by date (newest first).
    english_articles.sort(key=get_dt, reverse=True)
    
    # Save to CSV.
    save_to_csv(english_articles, output_file)
    
    print(f"\nCSV file generated: {output_file}")
    print(f"Total articles: {len(english_articles)}")

