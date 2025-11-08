# analyzer.py (إضافة الدالة الجديدة)
# ... (الدوال والـ imports القديمة) ...
from datetime import datetime
from db_helpers import get_db, create_analysis_run, update_analysis_run # تم تحديث الـ import
from models import AnalysisRun 
# ... (دالة start_new_analysis_run هنا) ...

def update_analysis_run_status(run_id: int, new_status: str, end_run: bool = False) -> AnalysisRun | None:
    """
    تحدّث حالة سجل تحليل موجود (AnalysisRun) في قاعدة البيانات.

    الوسائط:
        run_id (int): المعرّف الفريد لعملية التحليل المراد تحديثها.
        new_status (str): الحالة الجديدة (مثل: 'completed', 'failed', 'in_progress').
        end_run (bool): إذا كانت True، سيتم تعيين حقل finished_at إلى الوقت الحالي (نهاية التشغيل).

    الناتج:
        AnalysisRun | None: كائن AnalysisRun بعد التحديث، أو None في حالة الفشل.
    """
    
    # 1. إعداد البيانات المراد تحديثها
    updates = {
        "status": new_status,
        # يمكننا إضافة تاريخ الانتهاء
        "finished_at": datetime.utcnow() if end_run else None 
    }
    
    # 2. استخدام دالة المساعدة لتحديث السجل
    with get_db() as db:
        updated_run = update_analysis_run(db, run_id, updates)

    if updated_run:
        print(f"🔄 تم تحديث الحالة للمعرّف {run_id} إلى: {new_status}")
    else:
        print(f"❌ فشل في تحديث الحالة للمعرّف {run_id}.")
        
    return updated_run

# ----------------------------------------------------
# مثال على التنفيذ (إكمال مثال الـ if __name__ == "__main__":)
# ----------------------------------------------------
if __name__ == "__main__":
    
    # ... (الجزء القديم لـ start_new_analysis_run) ...

    # ----------------------------------------------------------------------
    print("\n--- اختبار وظيفة تحديث الحالة ---")
    
    if run:
        # 1. محاكاة بدء العملية
        update_analysis_run_status(run.id, "in_progress")
        
        # 2. محاكاة إكمال العملية بنجاح
        finished_run = update_analysis_run_status(run.id, "completed", end_run=True)

        if finished_run:
            print(f"تفاصيل التشغيل النهائية:")
            print(f"   الحالة الجديدة: {finished_run.status}")
            print(f"   تاريخ الانتهاء: {finished_run.finished_at}")
