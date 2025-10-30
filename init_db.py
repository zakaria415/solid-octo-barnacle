# init_db.py - تهيئة قاعدة البيانات

from database import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("🚀 جاري تهيئة قاعدة البيانات...")
    try:
        init_db()
        logger.info("✅ اكتملت تهيئة قاعدة البيانات بنجاح!")
    except Exception as e:
        logger.error(f"❌ فشلت تهيئة قاعدة البيانات: {e}")
        raise
