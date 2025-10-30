# dashboard.py - واجهة المستخدم الرئيسية باستخدام Streamlit

import streamlit as st
import pandas as pd
import plotly.express as px # مكتبة احترافية للرسوم البيانية
from db_helpers import (
    get_db, 
    get_latest_analysis_run, 
    get_review_stats, 
    get_reviews_as_dataframe, 
    get_sales_opportunities_as_dataframe, # دالة استرداد فرص المبيعات
    create_analysis_run
)
# استيراد من ملف analyzer.py (يجب التأكد من وجوده)
# from analyzer import start_new_analysis_run, process_analysis_run 

# ----------------------------------------------------
# 1. إعداد الصفحة (Configuration)
# ----------------------------------------------------
st.set_page_config(
    page_title="لوحة تحكم تحليل المشاعر",
    layout="wide",
    initial_sidebar_state="expanded"
)

def format_percentage(value: float) -> str:
    """تحويل القيمة العشرية إلى نسبة مئوية مع تقريب."""
    # تأكد من أن القيمة ليست None قبل التنسيق
    if value is None:
        return "N/A"
    return f"{value:.2f}%"

# ----------------------------------------------------
# 2. وظيفة عرض البيانات الرئيسية
# ----------------------------------------------------

def load_data_from_db():
    """تحميل جميع البيانات من قاعدة البيانات مرة واحدة وحفظها في حالة الجلسة."""
    st.session_state['db_data'] = {}
    with get_db() as db:
        st.session_state['db_data']['latest_run'] = get_latest_analysis_run(db)
        st.session_state['db_data']['review_stats'] = get_review_stats(db)
        st.session_state['db_data']['reviews_df'] = get_reviews_as_dataframe(db)
        st.session_state['db_data']['opportunities_df'] = get_sales_opportunities_as_dataframe(db)

# استخدام @st.cache_data لضمان عدم إعادة تحميل البيانات عند التفاعل غير الضروري
@st.cache_data(ttl=600)
def get_cached_data():
    """وظيفة للحصول على البيانات من قاعدة البيانات وتخزينها مؤقتاً."""
    with get_db() as db:
        return {
            'latest_run': get_latest_analysis_run(db),
            'review_stats': get_review_stats(db),
            'reviews_df': get_reviews_as_dataframe(db),
            'opportunities_df': get_sales_opportunities_as_dataframe(db)
        }

def display_dashboard():
    """عرض لوحة التحكم الرئيسية."""
    st.title("لوحة تحكم تحليل مراجعات الموقع 📈")
    
    # تحميل البيانات (استخدام التخزين المؤقت لتحسين الأداء)
    try:
        data = get_cached_data()
    except Exception as e:
        st.error(f"فشل الاتصال أو قراءة البيانات من قاعدة البيانات. تأكد من أن ملف database.py يعمل. الخطأ: {e}")
        return

    latest_run = data['latest_run']
    stats = data['review_stats']
    reviews_df = data['reviews_df']
    opportunities_df = data['opportunities_df']

    if latest_run is None:
        st.info("لا توجد عمليات تحليل سابقة. ابدأ عملية تحليل جديدة من الشريط الجانبي.")
        return

    # 3. عرض مقاييس الأداء الرئيسية (KPIs)
    st.subheader(f"نتائج آخر تحليل (ID: {latest_run.id})")
    st.caption(f"تاريخ الانتهاء: {latest_run.completed_at.strftime('%Y-%m-%d %H:%M:%S') if latest_run.completed_at else 'قيد التشغيل/معلّق'} | الموقع: {latest_run.target_site}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="إجمالي المراجعات 🔢", value=stats['count'])
    
    with col2:
        st.metric(label="متوسط التقييم ⭐", value=f"{stats['avg_rating']:.2f}")

    with col3:
        # يمكن أن تكون قيمة latest_run.positive_percentage هي None إذا كانت العملية قيد التشغيل
        positive_perc = latest_run.positive_percentage if latest_run.positive_percentage is not None else 0.0
        st.metric(label="النسبة الإيجابية 👍", value=format_percentage(positive_perc), 
                  delta=f"{latest_run.positive_count} مراجعة")

    with col4:
        avg_score = latest_run.avg_compound_score if latest_run.avg_compound_score is not None else 0.0
        st.metric(label="متوسط مركب المشاعر 🧠", value=f"{avg_score:.3f}")
        
    st.markdown("---")

    # 4. تصور البيانات (Charts & Visualizations)
    st.subheader("تحليل المشاعر وتوزيع البيانات")
    
    if not reviews_df.empty and 'sentiment_label' in reviews_df.columns:
        
        col_chart, col_df = st.columns([1, 2])
        
        # الرسم البياني لتوزيع المشاعر
        sentiment_counts = reviews_df['sentiment_label'].value_counts().reset_index()
        sentiment_counts.columns = ['المشاعر', 'العدد']
        
        fig = px.pie(sentiment_counts, 
                     values='العدد', 
                     names='المشاعر', 
                     title='توزيع المشاعر',
                     color='المشاعر',
                     color_discrete_map={'إيجابي':'green', 'سلبي':'red', 'محايد':'blue'},
                     hole=.3) # استخدام دائري احترافي
        
        with col_chart:
            st.plotly_chart(fig, use_container_width=True)

        # 5. عرض جدول المراجعات التفصيلي
        with col_df:
            st.markdown("##### جدول المراجعات الأخيرة")
            st.dataframe(
                reviews_df[['review_text', 'sentiment_label', 'rating', 'scraped_at']].head(10),
                use_container_width=True,
                column_config={
                    "review_text": st.column_config.TextColumn("النص", width="large"),
                    "sentiment_label": st.column_config.TextColumn("المشاعر"),
                    "rating": st.column_config.TextColumn("التقييم"),
                    "scraped_at": st.column_config.DatetimeColumn("تاريخ الاستخلاص", format="YYYY-MM-DD HH:mm")
                }
            )
            
    st.markdown("---")

    # 6. عرض فرص المبيعات المكتشفة
    st.subheader("فرص المبيعات المكتشفة 💰")
    
    # تصفية الفرص المرتبطة بآخر عملية تحليل فقط (للعرض الأولي)
    last_run_id = latest_run.id if latest_run else None
    
    if last_run_id is not None and not opportunities_df.empty:
        opportunities_df_filtered = opportunities_df[opportunities_df['analysis_run_id'] == last_run_id]
        
        if not opportunities_df_filtered.empty:
            st.info(f"تم اكتشاف {len(opportunities_df_filtered)} فرصة مبيعات في آخر عملية تحليل (ID: {last_run_id}).")

            # عرض احترافي لجدول فرص المبيعات
            st.dataframe(
                opportunities_df_filtered[['product_title', 'review_text', 'estimated_value', 'status', 'created_at']],
                use_container_width=True,
                column_config={
                    "product_title": st.column_config.TextColumn("العنوان", width="medium"),
                    "review_text": st.column_config.TextColumn("نص المراجعة (المرتبط)", width="large"),
                    "estimated_value": st.column_config.NumberColumn("القيمة التقديرية", format="$%.2f"),
                    "status": st.column_config.TextColumn("الحالة"),
                    "created_at": st.column_config.DatetimeColumn("تاريخ الاكتشاف", format="YYYY-MM-DD HH:mm")
                }
            )
        else:
            st.info("لم يتم اكتشاف فرص مبيعات في هذا التشغيل.")
    else:
        st.info("لا توجد بيانات لفرص المبيعات لعرضها.")

# ----------------------------------------------------
# 7. وظيفة الشريط الجانبي (Sidebar Functionality)
# ----------------------------------------------------

def sidebar_controls():
    """التحكم في بدء عملية تحليل جديدة وعرض حالة النظام."""
    
    st.sidebar.title("إدارة التحليل")
    
    # عرض حالة آخر تشغيل (نستخدم وظيفة القراءة المباشرة لتجنب مشكلات التخزين المؤقت هنا)
    with get_db() as db:
        latest_run = get_latest_analysis_run(db)
    
    if latest_run:
        status_map = {
            "pending": "🟡 معلّق",
            "running": "🟠 قيد التشغيل",
            "completed": "🟢 مكتمل",
            "failed": "🔴 فاشل"
        }
        st.sidebar.markdown(f"**آخر حالة تشغيل:** {status_map.get(latest_run.status, latest_run.status)}")
        
        if latest_run.status == 'running':
            st.sidebar.warning("يرجى الانتظار، عملية التحليل جارية...")

    st.sidebar.markdown("---")
    st.sidebar.header("بدء تحليل جديد")

    # نموذج بدء التحليل
    with st.sidebar.form("new_analysis_form"):
        target_site = st.text_input("اسم الموقع المستهدف", "موقع بيع المنتجات")
        start_url = st.text_input("رابط البداية (URL)", "https://example.com/product/reviews")
        submitted = st.form_submit_button("بدء التحليل الآن")
        
        if submitted:
            # افتراض أن الدالة start_new_analysis_run موجودة في analyzer.py
            # with get_db() as db:
            #    new_run = start_new_analysis_run(db, target_site, start_url) 
            
            # محاكاة لعملية الإرسال
            st.success(f"تم إرسال طلب تحليل جديد للموقع {target_site}.")
            get_cached_data.clear() # مسح البيانات المخزنة مؤقتاً
            st.experimental_rerun() 

# ----------------------------------------------------
# 8. نقطة الدخول الرئيسية
# ----------------------------------------------------
if __name__ == "__main__":
    try:
        # عرض لوحة التحكم أولاً
        display_dashboard()
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحميل لوحة التحكم: {e}")

    # ثم عرض الشريط الجانبي
    sidebar_controls()
    
    # زر تحديث يدوي للوحة التحكم
    st.sidebar.markdown("---")
    if st.sidebar.button("تحديث البيانات"):
        get_cached_data.clear() # مسح البيانات المخزنة مؤقتاً
        st.experimental_rerun()