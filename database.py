# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config # لاستيراد DEFAULT_DB_URL
import os

# ----------------- إعدادات الاتصال -----------------
SQLALCHEMY_DATABASE_URL = config.DEFAULT_DB_URL

# ----------------- إنشاء المحرك (Engine) -----------------
# check_same_thread=False مطلوب لـ SQLite فقط
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)

# ----------------- إنشاء مصنع الجلسات (SessionLocal) -----------------
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# ----------------- إنشاء الفئة الأساسية للنماذج (Base) -----------------
Base = declarative_base()

# ----------------- دالة إنشاء الجداول -----------------
def create_db_and_tables():
    """
    تقوم بإنشاء جميع الجداول المعرفة في Base.
    """
    print("⏳ جارٍ التحقق من نماذج قاعدة البيانات وإنشاء الجداول...")
    # يجب استدعاء Base.metadata.create_all بعد استيراد النماذج
    Base.metadata.create_all(bind=engine)
    print("✅ تم إنشاء/التحقق من جميع الجداول بنجاح.")
