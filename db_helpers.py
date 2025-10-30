# db_helpers.py - دوال المساعدة للتفاعل مع قاعدة البيانات

from typing import Any, Optional, Dict
from datetime import datetime
from models import AnalysisRun # يجب أن يكون لديك هذا الملف

# ----------------- 1. دالة الاتصال بقاعدة البيانات (مثال افتراضي) -----------------

def get_db() -> Any:
    """
    تُنشئ اتصالاً بقاعدة البيانات أو تُعيده (حسب طريقة إعداد المشروع).
    
    ملاحظة: في المشاريع الحقيقية، يتم هنا إعداد اتصال SQLAlchemy، 
    أو psycopg2، أو جلب جلسة (Session) قاعدة بيانات.
    """
    # مثال بسيط: يمكنك استبداله بكائن جلسة SQLAlchemy
    print("🌐 تم إنشاء/الحصول على اتصال بقاعدة البيانات.")
    return object() # إرجاع كائن وهمي لتمثيل الاتصال

# ----------------- 2. دوال جلب البيانات -----------------

def get_analysis_run(db: Any, run_id: int) -> Optional[AnalysisRun]:
    """
    تجلب تفاصيل تشغيل التحليل (AnalysisRun) بواسطة المعرّف (ID).
    
    الوسائط:
        db (Any): كائن اتصال قاعدة البيانات.
        run_id (int): معرّف التشغيل المطلوب.
        
    الإرجاع:
        Optional[AnalysisRun]: كائن التشغيل، أو None إذا لم يتم العثور عليه.
    """
    print(f"🔍 جلب تفاصيل التشغيل ID: {run_id}...")
    
    # ⚠️ هنا يتم إضافة منطق الاستعلام الحقيقي
    
    # محاكاة: إرجاع كائن وهمي لغرض الاختبار
    if run_id == 101:
        # محاكاة حالة ناجحة
        return AnalysisRun(
            id=101, 
            target_site="example.com", 
            total_reviews=500,
            positive_count=350,
            negative_count=100,
            positive_percentage=70.0,
            completed_at=datetime.now()
        )
    elif run_id == 202:
         # محاكاة حالة فاشلة أو قيد التشغيل
        return AnalysisRun(
            id=202, 
            target_site="anothersite.org", 
            total_reviews=0,
            positive_count=0,
            negative_count=0,
            positive_percentage=0.0,
            completed_at=None
        )
    return None

def get_review_stats(db: Any, run_id: int) -> Dict[str, Any]:
    """
    تجلب الإحصائيات التفصيلية للمراجعات المتعلقة بتشغيل معين.
    
    الوسائط:
        db (Any): كائن اتصال قاعدة البيانات.
        run_id (int): معرّف التشغيل.
        
    الإرجاع:
        Dict[str, Any]: قاموس يحتوي على الإحصائيات (مثل متوسط التقييم، الكلمات المفتاحية).
    """
    print(f"📊 جلب إحصائيات التشغيل ID: {run_id}...")
    
    # ⚠️ هنا يتم إضافة منطق الاستعلام الحقيقي
    
    # محاكاة: إرجاع قاموس إحصائيات وهمي
    if run_id == 101:
        return {
            "avg_rating": 4.15,
            "most_common_topic": "الشحن والتوصيل",
            "negative_keywords": ["تأخير", "جودة ضعيفة"]
        }
    return {}

# ----------------- 3. دالة تسجيل الإشعارات -----------------

def create_email_notification(
    db: Any, 
    recipient: str, 
    subject: str, 
    body: str, 
    success: bool, 
    error_message: Optional[str] = None
) -> None:
    """
    تسجل محاولة إرسال بريد إلكتروني في جدول سجل الإشعارات (notifications_log).
    
    الوسائط:
        db (Any): كائن اتصال قاعدة البيانات.
        recipient (str): المستلم.
        subject (str): عنوان البريد.
        body (str): محتوى الرسالة (للتوثيق).
        success (bool): هل نجحت عملية الإرسال؟
        error_message (Optional[str]): رسالة الخطأ في حال الفشل.
    """
    print(f"📝 تسجيل محاولة إشعار لـ {recipient}. النجاح: {success}")
    
    # ⚠️ هنا يتم إضافة منطق الإدخال (INSERT) إلى جدول السجلات
    # مثال على البيانات التي يمكن تسجيلها:
    # {
    #     'timestamp': datetime.now(),
    #     'recipient': recipient,
    #     'subject': subject,
    #     'success': success,
    #     'error_message': error_message,
    #     # 'full_body': body # يمكن حذفه لتجنب تخزين نصوص طويلة جداً
    # }
    
    # محاكاة: لا شيء يحدث هنا فعلياً

# ----------------- مثال على كائن النموذج (يجب أن يكون في models.py) -----------------
class AnalysisRun:
    """ كائن نموذجي لتمثيل صف من جدول 'analysis_runs'. """
    def __init__(self, id, target_site, total_reviews, positive_count, negative_count, positive_percentage, completed_at):
        self.id = id
        self.target_site = target_site
        self.total_reviews = total_reviews
        self.positive_count = positive_count
        self.negative_count = negative_count
        self.positive_percentage = positive_percentage
        self.completed_at = completed_at
        self.started_at = datetime.now()