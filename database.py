# database.py - تهيئة SQLAlchemy وإنشاء الاتصال

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ----------------- إعدادات الاتصال -----------------

# تحديد المسار لقاعدة بيانات SQLite. 
# هذا سيخلق ملفاً باسم './sentiment_analysis.db' في نفس مجلد تشغيل التطبيق.
SQLALCHEMY_DATABASE_URL = "sqlite:///./sentiment_analysis.db"
# يمكن استبدال السطر أعلاه بـ:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host:port/dbname"

# ----------------- إنشاء المحرك (Engine) -----------------

# المحرك هو نقطة الاتصال بقاعدة البيانات.
# check_same_thread=False مطلوب لـ SQLite عند استخدامه مع بيئة مثل Streamlit 
# حيث قد يتم الوصول إليه من أكثر من مؤشر ترابط (Thread).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

# ----------------- إنشاء مصنع الجلسات (SessionLocal) -----------------

# SessionLocal هي جلسة قاعدة بيانات مهيأة.
# سيتم استخدامها في ملف db_helpers.py لإنشاء وإغلاق الاتصالات.
# autocommit=False: الجلسة لن تقوم بحفظ التغييرات تلقائيًا، نحتاج إلى db.commit().
# autoflush=False: لن يتم إرسال الاستعلامات إلى DB قبل commit، مما يعطينا تحكماً أكبر.
# bind=engine: يربط هذه الجلسة بالمحرك الذي أنشأناه.
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# ----------------- إنشاء الفئة الأساسية للنماذج (Base) -----------------

# الفئة الأساسية التي سيتم توريثها في ملف models.py.
# هذه الفئة هي المسؤولة عن ربط نماذج SQLAlchemy بالـ Engine.
Base = declarative_base()

# ----------------- دالة إنشاء الجداول -----------------

def create_db_and_tables():
    """
    تقوم بإنشاء جميع الجداول المعرفة في Base (أي النماذج في models.py).
    
    ملاحظة: هذه الدالة يجب استدعاؤها مرة واحدة عند إعداد التطبيق، 
    وليس في كل مرة يتم فيها بدء تشغيل التطبيق بشكل طبيعي.
    """
    print("⏳ جارٍ التحقق من نماذج قاعدة البيانات وإنشاء الجداول...")
    # Base.metadata.create_all تستخدم الـ Base و Engine لإنشاء الجداول.
    Base.metadata.create_all(bind=engine)
    print("✅ تم إنشاء/التحقق من جميع الجداول بنجاح.")

# ----------------- مثال على الاستدعاء (للتجربة) -----------------

if __name__ == "__main__":
    # يجب استيراد النماذج هنا لضمان معرفة Base بها قبل استدعاء create_all
    # افتراضياً، يجب تشغيل هذه الدالة مرة واحدة فقط في بداية التطبيق.
    try:
        from models import AnalysisRun, Review, SalesOpportunity, EmailNotification
        create_db_and_tables()
    except ImportError as e:
        print(f"❌ فشل استيراد النماذج. تأكد من وجود ملف models.py. الخطأ: {e}")