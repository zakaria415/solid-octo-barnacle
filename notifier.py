# notifier.py - خدمة الإشعارات التلقائية وإرسال التقارير

import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
from typing import Optional

# افتراض أنك تعمل ضمن بيئة مشروع بايثون
# من الضروري توفر الملفات والوحدات التالية:
# - db_helpers: يحتوي على دوال التفاعل مع قاعدة البيانات مثل get_review_stats
# - models: يحتوي على تعريف الكلاس AnalysisRun
from db_helpers import get_db, create_email_notification, get_review_stats, get_analysis_run
from models import AnalysisRun 

# ----------------- إعدادات الإرسال (يجب تخصيصها) -----------------
# التوصية: استخدم os.getenv() لقراءة متغيرات البيئة بدلاً من الثوابت المباشرة
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com") 
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "notifications@yourdomain.com") 
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "YOUR_APP_PASSWORD") 
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "system@analysisapp.com")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@yourcompany.com")

# ----------------- 1. دوال بناء محتوى البريد الإلكتروني (المقدمة من المستخدم) -----------------

def build_report_body(run: AnalysisRun, stats: dict) -> str:
    """ بناء محتوى رسالة البريد الإلكتروني على هيئة HTML لتقرير مكتمل. """
    
    # تأمين القيمة في حالة كانت None
    completed_at_str = run.completed_at.strftime('%Y-%m-%d %H:%M:%S') if run.completed_at else 'N/A'
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">
                <h2 style="color: #4CAF50;">✅ اكتمال تحليل مراجعات الموقع - تقرير موجز</h2>
                <p><strong>معرّف التشغيل (ID):</strong> {run.id}</p>
                <p><strong>الموقع المستهدف:</strong> {run.target_site}</p>
                <p><strong>حالة التشغيل:</strong> <span style="color: green; font-weight: bold;">مكتملة</span></p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                
                <h3>الإحصائيات الرئيسية:</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="padding: 5px 0;"><strong>إجمالي المراجعات:</strong> {run.total_reviews}</li>
                    <li style="padding: 5px 0;"><strong>متوسط التقييم (من 5):</strong> {stats.get('avg_rating', 'N/A'):.2f}</li>
                    <li style="padding: 5px 0;"><strong>النسبة الإيجابية:</strong> {run.positive_percentage:.2f}% ({run.positive_count} مراجعة)</li>
                    <li style="padding: 5px 0;"><strong>المشاعر السلبية:</strong> {run.negative_count} مراجعة</li>
                </ul>
                
                <p style="margin-top: 20px;">تم إكمال التحليل في: {completed_at_str}</p>
                <p style="font-size: 12px; color: #777;">يرجى مراجعة لوحة التحكم للتفاصيل الكاملة.</p>
            </div>
        </body>
    </html>
    """
    return html_body

def build_failure_body(run: AnalysisRun, error_message: str) -> str:
    """ بناء محتوى رسالة البريد الإلكتروني على هيئة HTML لتقرير فشل التشغيل. """
    
    started_at_str = run.started_at.strftime('%Y-%m-%d %H:%M:%S') if run.started_at else 'N/A'
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">
                <h2 style="color: #D32F2F;">❌ فشل تشغيل التحليل</h2>
                <p><strong>معرّف التشغيل (ID):</strong> {run.id}</p>
                <p><strong>الموقع المستهدف:</strong> {run.target_site}</p>
                <p><strong>حالة التشغيل:</strong> <span style="color: red; font-weight: bold;">فشل</span></p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                
                <h3>رسالة الخطأ:</h3>
                <p style="background-color: #ffebee; border-left: 5px solid #D32F2F; padding: 10px;">
                    {error_message}
                </p>
                
                <p style="margin-top: 20px;">تم بدء التحليل في: {started_at_str}</p>
                <p style="font-size: 12px; color: #777;">تم إرسال هذا الإشعار إلى فريق الإدارة للمراجعة.</p>
            </div>
        </body>
    </html>
    """
    return html_body

# ----------------- 2. دالة الإرسال الأساسية -----------------

def send_email(subject: str, body: str, recipient_email: str) -> bool:
    """ 
    تقوم بإرسال بريد إلكتروني باستخدام بروتوكول SMTP.

    الوسائط:
        subject (str): عنوان البريد الإلكتروني.
        body (str): محتوى البريد الإلكتروني (بصيغة HTML).
        recipient_email (str): عنوان البريد الإلكتروني للمستلم.

    الإرجاع:
        bool: True إذا تم الإرسال بنجاح، False في حال حدوث خطأ.
    """
    try:
        # إنشاء كائن الرسالة MIMEText
        msg = MIMEText(body, 'html', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email

        # الاتصال بخادم SMTP والبدء في الإرسال
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # تفعيل التشفير
            server.login(SMTP_USERNAME, SMTP_PASSWORD) # تسجيل الدخول
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        
        # تسجيل الإشعار في قاعدة البيانات
        # ملاحظة: يجب أن تكون لديك دالة get_db() جاهزة للاستخدام هنا
        db = get_db() 
        create_email_notification(db, recipient_email, subject, body, success=True)
        print(f"✅ تم إرسال البريد بنجاح إلى: {recipient_email} بعنوان: {subject}")
        return True
        
    except Exception as e:
        # تسجيل الإشعار في حالة الفشل
        db = get_db()
        create_email_notification(db, recipient_email, subject, body, success=False, error_message=str(e))
        print(f"❌ خطأ في إرسال البريد إلى {recipient_email}: {e}")
        return False

# ----------------- 3. دوال منطق الإشعارات -----------------

def notify_completion(run_id: int) -> Optional[bool]:
    """ 
    منطق الإشعار عند اكتمال عملية تحليل بنجاح.
    
    الخطوات:
    1. جلب بيانات التشغيل (AnalysisRun) من قاعدة البيانات.
    2. جلب إحصائيات المراجعة.
    3. بناء محتوى البريد الإلكتروني.
    4. إرسال البريد الإلكتروني للمدير (ADMIN_EMAIL).
    """
    try:
        # 1. جلب بيانات التشغيل (نحتاج get_analysis_run في db_helpers)
        db = get_db()
        run = get_analysis_run(db, run_id)
        
        if not run:
            print(f"⚠️ لم يتم العثور على تشغيل بالمعرّف {run_id}. الإشعار ألغي.")
            return None

        # 2. جلب الإحصائيات (نفترض أن الدالة جاهزة)
        stats = get_review_stats(db, run_id)
        
        # 3. بناء الرسالة
        subject = f"[تقرير مكتمل] تحليل الموقع {run.target_site} (#{run.id})"
        body = build_report_body(run, stats)
        
        # 4. إرسال البريد الإلكتروني
        return send_email(subject, body, ADMIN_EMAIL)
        
    except Exception as e:
        print(f"❌ خطأ عام في عملية إشعار الاكتمال لـ {run_id}: {e}")
        return False

def notify_failure(run_id: int, error_message: str) -> Optional[bool]:
    """ 
    منطق الإشعار عند فشل عملية تحليل.
    يتم إرسال إشعار فشل بسيط إلى المسؤول.
    """
    try:
        db = get_db()
        run = get_analysis_run(db, run_id)
        
        if not run:
            print(f"⚠️ لم يتم العثور على تشغيل بالمعرّف {run_id}. الإشعار ألغي.")
            return None
        
        # بناء الرسالة
        subject = f"[فشل] تحليل الموقع {run.target_site} - عاجل (#{run.id})"
        body = build_failure_body(run, error_message)
        
        # إرسال البريد الإلكتروني
        return send_email(subject, body, ADMIN_EMAIL)
        
    except Exception as e:
        print(f"❌ خطأ عام في عملية إشعار الفشل لـ {run_id}: {e}")
        return False

# ----------------- مثال على كيفية التنفيذ -----------------

if __name__ == "__main__":
    # هذا الجزء يستخدم للمحاكاة واختبار عمل الدوال
    print("بدء اختبار وحدة الإشعارات...")
    
    # ⚠️ ملاحظة هامة: لتشغيل هذا الجزء بنجاح، يجب:
    # 1. تثبيت مكتبات مثل SQLAlchemy أو أي أداة اتصال بقاعدة البيانات التي تستخدمها.
    # 2. التأكد من أن دوال get_db, get_analysis_run, get_review_stats و AnalysisRun كلها مُعرّفة وتعمل بشكل صحيح.
    # 3. تعديل ثوابت SMTP_USERNAME و SMTP_PASSWORD لقيم حقيقية.
    
    # مثال على محاكاة كائن AnalysisRun لغرض الاختبار
    class MockAnalysisRun:
        def __init__(self, id, site, total, positive, negative):
            self.id = id
            self.target_site = site
            self.total_reviews = total
            self.positive_count = positive
            self.negative_count = negative
            self.positive_percentage = (positive / total) * 100 if total > 0 else 0
            self.completed_at = datetime.now()
            self.started_at = datetime.now()
    
    # محاكاة لدوال قاعدة البيانات غير المتوفرة حالياً
    def get_db(): return object()
    def get_analysis_run(db, run_id): 
        # محاكاة جلب تشغيل ناجح
        if run_id == 101:
            return MockAnalysisRun(101, "example.com", 500, 350, 100)
        # محاكاة جلب تشغيل فاشل
        if run_id == 202:
            return MockAnalysisRun(202, "anothersite.org", 0, 0, 0)
        return None
        
    def get_review_stats(db, run_id):
        # محاكاة إحصائيات
        if run_id == 101:
            return {"avg_rating": 4.15, "most_common_topic": "Shipping"}
        return {}

    def create_email_notification(db, to, subject, body, success, error_message=None):
        pass # لا تفعل شيئاً في المحاكاة
        
    # **الاختبار الأول: إشعار اكتمال ناجح**
    # print("\n--- اختبار إشعار الاكتمال ---")
    # notify_completion(101) # قم بتعطيل هذا السطر حتى تعديل الإعدادات

    # **الاختبار الثاني: إشعار فشل**
    # print("\n--- اختبار إشعار الفشل ---")
    # notify_failure(202, "Database connection timeout during sentiment analysis step.") # قم بتعطيل هذا السطر حتى تعديل الإعدادات
    
    print("انتهى اختبار وحدة الإشعارات (يرجى تعديل الإعدادات لاختبار الإرسال الفعلي).")