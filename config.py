# config.py

import os # إضافة مكتبة os لقراءة متغيرات البيئة

# --- Database Settings ---
# يتم الآن تحميل رابط قاعدة البيانات من متغيرات البيئة لضمان الأمان
# المتغير المطلوب هو: DATABASE_URL
DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost:5432/scraped_data" # قيمة افتراضية للاختبار المحلي
)

# --- Scraper Settings ---
DEFAULT_PAGES_TO_SCRAPE = 5
DEFAULT_CONCURRENCY_LIMIT = 5
DEFAULT_START_URL = os.getenv("START_URL", "http://example.com")