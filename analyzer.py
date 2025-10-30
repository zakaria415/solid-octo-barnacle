[  ] # analyzer.py - منطق عمل التطبيق: إدارة التحليل والاستخلاص والحفظ
[  ] 
[  ] # استيرادات الأساسية
[  ] from datetime import datetime
[  ] from db_helpers import (
[  ]     get_db, 
[  ]     create_analysis_run,
[  ]     update_analysis_run_status, 
[  ]     create_review, 
[  ]     create_sales_opportunity,
[  ]     get_review_stats
[  ] )
[  ] from models import AnalysisRun # نستورد النماذج للعرض
[  ] # استيرادات منطق العمل (يجب تثبيتها: pip install requests beautifulsoup4 textblob)
[  ] import requests
[  ] from bs4 import BeautifulSoup
[  ] from textblob import TextBlob
[  ] import re 
[  ] import time
[  ] # استيراد خدمة الإشعارات (يفترض أن ملف notifier.py موجود)
[  ] from notifier import send_analysis_notification 
[  ] 
[  ] # ----------------- 1. دوال الاستخلاص والتحليل الفعلية -----------------
[  ] 
[  ] def scrape_reviews(url: str, review_selector: str) -> list[dict]:
[  ]     """
[  ]     استخلاص نصوص المراجعات والتقييمات الفعلية من صفحة واحدة.
[  ]     *** ملاحظة: هذه الدالة تحتاج للتخصيص الكامل حسب هيكل HTML للموقع المستهدف. ***
[  ]     """
[  ]     reviews_list = []
[  ]     
[  ]     try:
[  ]         response = requests.get(url, timeout=15)
[  ]         response.raise_for_status() # إطلاق استثناء لأخطاء HTTP
[  ]         
[  ]         soup = BeautifulSoup(response.content, 'html.parser')
[  ]         
[  ]         review_elements = soup.select(review_selector) 
[  ]         
[  ]         for element in review_elements:
[  ]             # يجب تعديل هذه المُحدّدات (.review-title, .review-body, إلخ) لتطابق الموقع
[  ]             title = element.select_one('.review-title')?.text.strip()
[  ]             text = element.select_one('.review-body')?.text.strip()
[  ]             rating_str = element.select_one('.review-rating')?.text.strip() 
[  ]             
[  ]             if text:
[  ]                 # استخراج القيمة الرقمية للتقييم
[  ]                 rating = re.search(r'\d+', rating_str).group(0) if rating_str and re.search(r'\d+', rating_str) else None
[  ] 
[  ]                 reviews_list.append({
[  ]                     'title': title,
[  ]                     'review_text': text,
[  ]                     'rating': rating,
[  ]                     # حقول التحليل سيتم ملؤها لاحقاً
[  ]                 })
[  ] 
[  ]     except requests.exceptions.RequestException as e:
[  ]         print(f"خطأ في الاستخلاص من {url}: {e}")
[  ]     
[  ]     return reviews_list
[  ] 
[  ] def analyze_sentiment(text: str) -> tuple[str, float, float, str]:
[  ]     """
[  ]     تحليل نص المراجعة للحصول على المشاعر والذاتية واللغة.
[  ]     *** ملاحظة: TextBlob لا يدعم العربية بشكل كامل ويجب استبداله بمكتبة عربية متخصصة. ***
[  ]     """
[  ]     try:
[  ]         # استخدام TextBlob (يجب استبداله بنموذج عربي في الإنتاج)
[  ]         analysis = TextBlob(text)
[  ]         
[  ]         sentiment_score = analysis.sentiment.polarity # من -1 (سلبي) إلى +1 (إيجابي)
[  ]         subjectivity_score = analysis.sentiment.subjectivity
[  ]         language = 'ar' 
[  ]         
[  ]         if sentiment_score > 0.3:
[  ]             label = 'إيجابي'
[  ]         elif sentiment_score < -0.1:
[  ]             label = 'سلبي'
[  ]         else:
[  ]             label = 'محايد'
[  ]             
[  ]         return label, sentiment_score, subjectivity_score, language
[  ] 
[  ]     except Exception as e:
[  ]         print(f"خطأ في تحليل المشاعر: {e}")
[  ]         return 'محايد', 0.0, 0.5, 'unknown'
[  ] 
[  ] def find_sales_intent(text: str) -> tuple[bool, str | None]:
[  ]     """
[  ]     تحديد ما إذا كان النص يشير إلى فرصة مبيعات أو تحسين (فرصة).
[  ]     """
[  ]     keywords = ["أتمنى لو", "يحتاج إلى", "يجب أن", "لو كان هناك", "نقص في"]
[  ]     
[  ]     if any(k in text.lower() for k in keywords):
[  ]         product_title = f"طلب ميزة/تحسين: {text[:30].replace(text[:30].split()[0], '')}..."
[  ]         return True, product_title
[  ]         
[  ]     return False, None
[  ] 
[  ] # ----------------- 2. وظائف إدارة عملية التحليل -----------------
[  ] 
[  ] def start_new_analysis_run(target_site: str, start_url: str) -> AnalysisRun | None:
[  ]     """
[  ]     تبدأ عملية تحليل جديدة عن طريق إنشاء سجل AnalysisRun في قاعدة البيانات بحالة 'pending'.
[  ]     """
[  ]     run_data = {
[  ]         "target_site": target_site,
[  ]         "start_url": start_url,
[  ]         "status": "pending",  
[  ]         "created_at": datetime.utcnow()
[  ]     }
[  ] 
[  ]     with get_db() as db:
[  ]         new_run = create_analysis_run(db, run_data)
[  ]     
[  ]     if new_run:
[  ]         print(f"✅ تم بدء عملية تحليل جديدة للموقع: {target_site} بالمعرّف (ID): {new_run.id}")
[  ]     else:
[  ]         print(f"❌ فشل في بدء عملية التحليل للموقع: {target_site}")
[  ] 
[  ]     return new_run
[  ] 
[  ] 
[  ] def process_analysis_run(run_to_process: AnalysisRun):
[  ]     """
[  ]     إدارة عملية التحليل بالكامل: التحديث، الاستخلاص، التحليل، الحفظ، والإشعار.
[  ]     """
[  ]     run_id = run_to_process.id
[  ]     start_url = run_to_process.start_url
[  ]     
[  ]     print(f"\n--- بدء تحليل ID: {run_id} للموقع: {run_to_process.target_site} ---")
[  ]     
[  ]     # 1. تحديث الحالة إلى "running" (قيد التشغيل)
[  ]     with get_db() as db:
[  ]         updated_run = update_analysis_run_status(db, run_id, "running")
[  ]         if not updated_run:
[  ]             print(f"❌ فشل تحديث حالة التشغيل ID: {run_id} إلى 'running'.")
[  ]             return
[  ] 
[  ]     print(f"🔄 تم تحديث الحالة إلى: {updated_run.status}")
[  ] 
[  ]     try:
[  ]         # 2. الاستخلاص الفعلي
[  ]         review_selector = 'div.review-card' # يجب تخصيصه
[  ]         raw_reviews = scrape_reviews(start_url, review_selector)
[  ]         
[  ]         # 3. تحليل وحفظ البيانات
[  ]         reviews_to_save = []
[  ]         opportunities_to_save = []
[  ]         
[  ]         for r_data in raw_reviews:
[  ]             # التحليل
[  ]             label, score, subjectivity, lang = analyze_sentiment(r_data['review_text'])
[  ]             is_opportunity, op_title = find_sales_intent(r_data['review_text'])
[  ]             
[  ]             review_final_data = {
[  ]                 'analysis_run_id': run_id,
[  ]                 'title': r_data.get('title'),
[  ]                 'review_text': r_data['review_text'],
[  ]                 'rating': r_data.get('rating'),
[  ]                 'sentiment_label': label,
[  ]                 'compound_score': score,
[  ]                 'subjectivity': subjectivity,
[  ]                 'language': lang,
[  ]                 'has_sales_intent': is_opportunity,
[  ]                 'scraped_at': datetime.utcnow()
[  ]             }
[  ]             reviews_to_save.append(review_final_data)
[  ] 
[  ]             if is_opportunity:
[  ]                 opportunities_to_save.append({
[  ]                     'analysis_run_id': run_id,
[  ]                     'product_title': op_title,
[  ]                     'review_text': r_data['review_text'],
[  ]                     'compound_score': score,
[  ]                     'estimated_value': 50.0, # قيمة افتراضية
[  ]                     'status': 'pending',
[  ]                     'created_at': datetime.utcnow(),
[  ]                 })
[  ]             
[  ]         # 4. حفظ البيانات وحساب الإحصائيات النهائية
[  ]         total_reviews = len(reviews_to_save)
[  ]         positive_count = sum(1 for r in reviews_to_save if r['sentiment_label'] == 'إيجابي')
[  ]         negative_count = sum(1 for r in reviews_to_save if r['sentiment_label'] == 'سلبي')
[  ]         neutral_count = total_reviews - (positive_count + negative_count)
[  ]         avg_compound_score = sum(r['compound_score'] for r in reviews_to_save) / total_reviews if total_reviews else 0
[  ]         positive_perc = (positive_count / total_reviews) * 100 if total_reviews else 0
[  ] 
[  ]         with get_db() as db:
[  ]             # حفظ المراجعات وفرص المبيعات
[  ]             for r_data in reviews_to_save:
[  ]                 create_review(db, r_data)
[  ]             for o_data in opportunities_to_save:
[  ]                 create_sales_opportunity(db, o_data)
[  ]             
[  ]             # 5. تحديث سجل التحليل بـ "completed" والنتائج
[  ]             final_data = {
[  ]                 "total_reviews": total_reviews,
[  ]                 "positive_count": positive_count,
[  ]                 "negative_count": negative_count,
[  ]                 "neutral_count": neutral_count,
[  ]                 "positive_percentage": positive_perc,
[  ]                 "avg_compound_score": avg_compound_score,
[  ]                 "completed_at": datetime.utcnow(),
[  ]                 "status": "completed"
[  ]             }
[  ]             
[  ]             db.query(AnalysisRun).filter(AnalysisRun.id == run_id).update(final_data)
[  ]             db.commit()
[  ]             
[  ]             print(f"✅ اكتمل التحليل ID: {run_id}. المراجعات الكلية: {total_reviews}")
[  ]             
[  ]             # 6. إرسال إشعار النجاح
[  ]             send_analysis_notification(run_to_process, is_success=True)
[  ] 
[  ]     except Exception as e:
[  ]         error_msg = str(e)
[  ]         print(f"❌ حدث خطأ غير متوقع أثناء التحليل ID {run_id}: {error_msg}")
[  ]         
[  ]         # 7. تحديث الحالة إلى "failed" وإرسال إشعار الفشل
[  ]         with get_db() as db:
[  ]             run_to_process.status = "failed"
[  ]             db.add(run_to_process)
[  ]             db.commit()
[  ]             
[  ]             send_analysis_notification(run_to_process, is_success=False, error_message=error_msg)
[  ]             
[  ] # ----------------------------------------------------
[  ] # مثال على التنفيذ (يجب ربطه بـ Streamlit)
[  ] # ----------------------------------------------------
[  ] if __name__ == "__main__":
[  ]     
[  ]     # 1. بدء عملية جديدة
[  ]     run_obj = start_new_analysis_run("منصة تجريبية X", "http://test.com/reviews")
[  ]     
[  ]     if run_obj:
[  ]         # 2. معالجة العملية الجديدة (وهي عملية طويلة المدى)
[  ]         # ملاحظة: في تطبيق Streamlit، يجب تشغيل هذه الدالة في مؤشر ترابط (Thread) أو عملية منفصلة
[  ]         # لتجنب حظر واجهة المستخدم.
[  ]         process_analysis_run(run_obj)
[  ]         
[  ]         # 3. التحقق من النتيجة النهائية
[  ]         with get_db() as db:
[  ]             final_run = db.query(AnalysisRun).filter(AnalysisRun.id == run_obj.id).first()
[  ]             if final_run:
[  ]                 print(f"\n*** تقرير نهائي (ID: {final_run.id}) ***")
[  ]                 print(f"الحالة النهائية: {final_run.status}")
[  ]                 print(f"إجمالي المراجعات: {final_run.total_reviews}")
[  ]