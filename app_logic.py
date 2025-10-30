# analyzer.py - منطق عمل التطبيق
# هذا الملف يعتمد على وظائف المساعدة في db_helpers.py

from datetime import datetime
from db_helpers import get_db, create_analysis_run
from models import AnalysisRun # نستورد النموذج للعرض فقط

def start_new_analysis_run(target_site: str, start_url: str) -> AnalysisRun | None:
    """
    تبدأ عملية تحليل جديدة عن طريق إنشاء سجل AnalysisRun في قاعدة البيانات.

    الافتراض: هذه الدالة هي الخطوة الأولى قبل بدء الاستخلاص الفعلي للبيانات.

    الوسائط:
        target_site (str): اسم الموقع أو النظام الذي يتم تحليله.
        start_url (str): رابط الويب الذي تبدأ منه عملية الاستخلاص (Scraping).

    الناتج:
        AnalysisRun | None: كائن AnalysisRun الذي تم إنشاؤه، أو None في حالة الفشل.
    """
    
    # 1. إعداد البيانات المطلوبة لإنشاء سجل AnalysisRun
    run_data = {
        "target_site": target_site,
        "start_url": start_url,
        "status": "pending",  # يتم تعيين الحالة الأولية كـ "معلّق"
        "created_at": datetime.utcnow()
    }

    # 2. استخدام دالة المساعدة (get_db و create_analysis_run) لإنشاء السجل
    with get_db() as db:
        new_run = create_analysis_run(db, run_data)
    
    if new_run:
        print(f"✅ تم بدء عملية تحليل جديدة للموقع: {target_site} بالمعرّف (ID): {new_run.id}")
    else:
        print(f"❌ فشل في بدء عملية التحليل للموقع: {target_site}")

    return new_run

# ----------------------------------------------------
# مثال على التنفيذ (للتجربة في بيئة تطوير Python)
# ----------------------------------------------------
if __name__ == "__main__":
    
    # *ملاحظة:* يجب التأكد من أن ملف database.py يعمل ونماذج الجداول تم إنشاؤها
    print("--- اختبار وظيفة بدء تحليل جديد ---")
    
    # بيانات عملية التحليل
    site_name = "منصة بيع المنتجات X"
    starting_link = "https://example.com/product/reviews"
    
    # استدعاء الدالة
    run = start_new_analysis_run(site_name, starting_link)
    
    if run:
        print(f"تفاصيل التشغيل:")
        print(f"   الموقع: {run.target_site}")
        print(f"   الحالة: {run.status}")
        print(f"   تاريخ الإنشاء: {run.created_at}")

        # الآن يمكنك تخيل أن عملية الاستخلاص تبدأ هنا...
        # ... ثم يتم تحديث الحالة لاحقًا باستخدام دالة update_analysis_run_status