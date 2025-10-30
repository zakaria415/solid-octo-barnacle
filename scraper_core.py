# scraper_core.py (Final Version with Dynamic Scraping)

import aiohttp
import asyncio
import re
import nltk
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from db_helpers import save_analysis_result 
from urllib.parse import urljoin # إضافة استيراد urljoin
from app import load_config # افتراض أن load_config موجودة في app.py

# --- Initialization ---
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except nltk.downloader.DownloadError:
    nltk.download('vader_lexicon')

analyzer = SentimentIntensityAnalyzer()

# --- Core Asynchronous Functions ---

async def fetch_page(session, url):
    """Fetches content from a single URL."""
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()  
            return await response.text()
    except aiohttp.ClientError as e:
        print(f"Error fetching {url}: {e}")
        return None
    except asyncio.TimeoutError:
        print(f"Timeout occurred while fetching {url}.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching {url}: {e}")
        return None

def extract_text(html_content):
    """Extracts clean, non-script/style text content from HTML."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose() 
        text = soup.get_text()
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        return cleaned_text
    except Exception as e:
        print(f"Error during text extraction: {e}")
        return ""

def analyze_sentiment(text):
    """Analyzes the sentiment of a given text using VADER."""
    if not text:
        return 0.0 
    score = analyzer.polarity_scores(text)
    return score['compound'] 

# --- NEW: Dynamic Link Discovery Function ---
def get_next_page_url(html_content, current_url):
    """
    يستخرج رابط الصفحة التالية بناءً على مُحدد CSS في config.json.
    """
    if not html_content:
        return None
    
    try:
        config = load_config() # تحميل إعدادات config.json
        # استخدام التحديد الصحيح لـ next_page
        next_page_selector = config.get('selectors', {}).get('next_page')
        base_url = config.get('base_url')
        
        if not next_page_selector or not base_url:
            return None
            
        soup = BeautifulSoup(html_content, 'html.parser')
        next_page_link = soup.select_one(next_page_selector)
        
        if next_page_link and 'href' in next_page_link.attrs:
            # استخدام urljoin للتعامل مع الروابط النسبية
            next_url = urljoin(base_url, next_page_link['href'])
            return next_url
            
    except Exception as e:
        # print(f"⚠️ خطأ في استخلاص رابط الصفحة التالية من {current_url}: {e}") # إزالة الطباعة المتكررة
        return None

# --- NEW: Orchestration Function with Dynamic Crawling ---
def run_scraper_and_analysis(db_url, start_url, pages_to_scrape, concurrency):
    """
    Orchestrates the scraping and sentiment analysis process using a dynamic queue.
    """
    print(f"\n--- Starting Scraping and Analysis (Dynamic) ---")
    print(f"Target URL: {start_url}")
    print(f"Pages to scrape limit: {pages_to_scrape}")
    print(f"Concurrency limit: {concurrency}")

    urls_queue = asyncio.Queue()
    urls_queue.put_nowait(start_url)
    scraped_urls = {start_url} # لضمان عدم تكرار زحف نفس الرابط
    all_results = [] 
    
    try:
        loop = asyncio.get_event_loop()
        
        async def scraper_worker(session):
            nonlocal all_results
            pages_counter = 0
            
            # الحلقة تستمر ما دامت الروابط في الطابور لم تنتهِ ولم يتجاوز عداد الصفحات الحد الأقصى
            while pages_counter < pages_to_scrape and not urls_queue.empty():
                try:
                    url = await asyncio.wait_for(urls_queue.get(), timeout=1) # timeout للحماية
                    if url is None: continue
                    
                    print(f"🌐 جاري الزحف إلى: {url} (الصفحة: {pages_counter + 1} من {pages_to_scrape})")
                    html_content = await fetch_page(session, url)
                    
                    if html_content:
                        # 1. تحليل المحتوى واستخلاص النصوص والمشاعر
                        extracted_text = extract_text(html_content)
                        sentiment_score = analyze_sentiment(extracted_text)
                        
                        all_results.append({
                            'url': url,
                            'sentiment_score': sentiment_score,
                            'text_content': extracted_text
                        })
                        
                        # 2. اكتشاف الصفحة التالية وإضافتها للطابور
                        next_url = get_next_page_url(html_content, url)
                        if next_url and next_url not in scraped_urls:
                            urls_queue.put_nowait(next_url)
                            scraped_urls.add(next_url)
                            print(f"-> تم اكتشاف الرابط التالي وإضافته: {next_url}")

                        pages_counter += 1
                    
                    urls_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # قد يحدث عند انتظار رابط جديد في الطابور
                    print("⌛ انتهى انتظار الروابط، جاري إنهاء العمل.")
                    break 
                except Exception as worker_error:
                    print(f"⚠️ خطأ في Worker عند {url}: {worker_error}")
                    urls_queue.task_done()

        # تشغيل المهام غير المتزامنة
        async def main_scraper_task():
            async with aiohttp.ClientSession() as session:
                # إنشاء عمال بعدد يساوي قيمة التزامن (concurrency)
                workers = [asyncio.create_task(scraper_worker(session)) for _ in range(concurrency)]
                await urls_queue.join()
                
                # إيقاف جميع العمال بمجرد إفراغ الطابور
                for worker in workers:
                    worker.cancel()

        loop.run_until_complete(main_scraper_task())

        print(f"\n✅ Finished dynamic scraping. Found {len(all_results)} analysis results.")

        # Process results and save to database
        for result in all_results:
            try:
                save_analysis_result(
                    db_url, 
                    result['url'], 
                    result['sentiment_score'], 
                    result['text_content']
                )
                # print(f"-> Saved analysis for {result['url']}")
            except Exception as db_error:
                print(f"⚠️ Error saving analysis for {result['url']}: {db_error}")

    except Exception as e:
        print(f"❌ An error occurred during the overall process: {e}")

    print("--- Process Finished ---\n")