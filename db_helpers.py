# db_helpers.py (النسخة المكتملة والمناسبة للتجربة)

from typing import Any, Optional, Dict
from datetime import datetime
from contextlib import contextmanager
import random
# نفترض استيراد هذه الأنواع من SQLAlchemy
from sqlalchemy.orm import Session 
from sqlalchemy.exc import SQLAlchemyError 

# ----------------- نموذج وهمي (للتشغيل السريع) -----------------
# هذا الكلاس يجب أن يكون في models.py لكن نضعه هنا للتجربة
class AnalysisRun:
    def __init__(self, id, target_site, status, created_at, 
                 total_reviews=0, positive_count=0, negative_count=0, 
                 positive_percentage=0.0, finished_at=None):
        self.id = id
        self.target_site = target_site
        self.status = status
        self.created_at = created_at
        self.total_reviews = total_reviews
        self.positive_count = positive_count
        self.negative_count = negative_count
        self.positive_percentage = positive_percentage
        self.finished_at = finished_at

# ----------------- 1. دالة الاتصال كمدير سياق -----------------

@contextmanager
def get_db():
    # ... (كما هو موضح في الرمز الذي شاركته) ...
    db_session = object() 
    print("🌐 تم إنشاء/الحصول على اتصال بقاعدة البيانات (Session Open).")
    try:
        yield db_session
    finally:
        print("🛑 تم إغلاق اتصال قاعدة البيانات (Session Closed).")

# ----------------- 2. دوال جلب البيانات (يجب إكمالها) -----------------

def get_analysis_run(db: Any, run_id: int) -> Optional[AnalysisRun]:
    """
    تجلب تفاصيل تشغيل التحليل (AnalysisRun) بواسطة المعرّف (ID).
    (منطق المحاكاة الذي قدمته سابقاً)
    """
    print(f"🔍 جلب تفاصيل التشغيل ID: {run_id}...")
    if run_id == 101 or run_id == 202:
        # محاكاة لإرجاع كائن قابل للتحديث في دالة update_analysis_run
        return AnalysisRun(id=run_id, target_site="simulated.com", status="pending", created_at=datetime.now())
    return None

# ----------------- 3. دالة إنشاء سجل جديد -----------------

def create_analysis_run(db: Session, run_data: Dict[str, Any]) -> Optional[AnalysisRun]:
    # ... (كما هو موضح في الرمز الذي شاركته) ...
    # هنا تم تفعيل الـ random بعد استيراده
    try:
        new_run_id = random.randint(300, 999)
        return AnalysisRun(id=new_run_id, **run_data)
    except Exception as e: # تم تغيير SQLAlchemyError إلى Exception لأننا نستخدم محاكاة
        print(f"❌ خطأ في إنشاء السجل: {e}")
        return None

# ----------------- 4. دالة تحديث سجل موجود -----------------

def update_analysis_run(db: Session, run_id: int, updates: dict) -> Optional[AnalysisRun]:
    # ... (كما هو موضح في الرمز الذي شاركته) ...
    try:
        run_to_update = get_analysis_run(db, run_id) 
        
        if not run_to_update:
            return None
        
        for key, value in updates.items():
            if hasattr(run_to_update, key):
                setattr(run_to_update, key, value)
        
        print(f"🔄 تم تحديث المعرّف {run_id} بالحقول: {list(updates.keys())}")
        return run_to_update
        
    except SQLAlchemyError as e:
        print(f"❌ حدث خطأ في قاعدة البيانات أثناء التحديث: {e}")
        return None
