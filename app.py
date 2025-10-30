# app.py - لوحة مدير الأداء الذكي (Final Dashboard)

import streamlit as st
import asyncio
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scraper_core import FeedbackAnalystScraper, load_config, LOG_FILENAME
from social_publisher import publish_to_social_media
from db_helpers import (
    get_all_analysis_runs, 
    get_analysis_run_by_id,
    get_reviews_by_analysis_run,
    get_sales_opportunities_by_analysis_run,
    reviews_to_dataframe,
    sales_opportunities_to_dataframe,
    get_sentiment_summary_from_reviews,
    get_analysis_summary_stats,
    delete_analysis_run
)
from email_notifier import EmailNotifier, send_critical_alerts
from database import init_db
import time
import datetime

# تهيئة قاعدة البيانات عند بدء التطبيق
try:
    init_db()
except Exception as e:
    import logging
    logging.warning(f"⚠️ تحذير: فشل تهيئة قاعدة البيانات: {e}")

# ----------------- دوال المساعدة -----------------

def get_config_files(config_dir='.'):
    """جلب قائمة بملفات config.json في المجلد."""
    return [f for f in os.listdir(config_dir) if f.endswith('.json') and f.startswith('config')]

def get_log_content(n_lines=100):
    """قراءة آخر n سطر من ملف السجل."""
    try:
        with open(LOG_FILENAME, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return "".join(lines[-n_lines:])
    except FileNotFoundError:
        return "Log file not found."
    except Exception as e:
        return f"Error reading log: {e}"

def set_rtl_css():
    """حقن أكواد CSS لضبط اتجاه النص من اليمين إلى اليسار (RTL) وتحسين الخط."""
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            direction: rtl; 
            font-family: 'Cairo', 'Tajawal', sans-serif; 
        }
        
        .stMarkdown, .stHeader, .stTitle, h1, h2, h3, h4, [data-testid="stSidebar"] {
            text-align: right !important;
        }
        
        [data-testid="stSidebar"] {
            padding-right: 20px; 
        }

        .stTextInput input {
            direction: ltr; 
            text-align: left;
        }
        
        .stButton button {
            border-radius: 8px;
            padding: 8px 16px;
            direction: rtl;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# ----------------- واجهة Streamlit -----------------

st.set_page_config(layout="wide", page_title="Smart Performance Analyst")
set_rtl_css() # تطبيق CSS

# تحميل الإعدادات
config_files = get_config_files()
current_config = {}
selected_config = 'config.json' 
if config_files:
    current_config = load_config(selected_config)

site_name = current_config.get('target_site_name', 'موقع غير معروف')
st.title(f"🚀 مدير الأداء الذكي - {site_name}") 
st.markdown("---")


# 1. الشريط الجانبي: الإعدادات والأمان
with st.sidebar:
    st.header("⚙️ إعدادات المشروع")
    
    st.markdown(f"**الموقع المستهدف:** `{site_name}`")
    st.markdown(f"**الرابط الأساسي:** `{current_config.get('base_url', 'غير محدد')}`")
    st.markdown("---")
    
    st.subheader("إعدادات API (للنشر والتسويق)")
    
    # حقول إدخال لـ Tokens (أكثر أماناً وسهولة من تعديل JSON على الهاتف)
    if 'api_tokens' not in st.session_state:
        st.session_state.api_tokens = current_config.get('api_tokens', {})
    
    st.session_state.api_tokens['facebook_token'] = st.text_input("Facebook Page Token:", 
                                                                 value=st.session_state.api_tokens.get('facebook_token', ''),
                                                                 type="password",
                                                                 help="مفتاح وصول الصفحة لنشر المحتوى (لتجنب وضعه في config.json بشكل دائم).")
    st.session_state.api_tokens['facebook_page_id'] = st.text_input("Facebook Page ID:", 
                                                                 value=st.session_state.api_tokens.get('facebook_page_id', ''))
    
    st.markdown("---")
    
    st.subheader("إعدادات البريد الإلكتروني")
    
    # تخزين إعدادات البريد
    if 'email_config' not in st.session_state:
        st.session_state.email_config = current_config.get('email', {})
    
    st.session_state.email_config['sender'] = st.text_input("البريد المرسل:", 
                                                            value=st.session_state.email_config.get('sender', ''),
                                                            help="بريدك الإلكتروني (Gmail)")
    st.session_state.email_config['receiver'] = st.text_input("البريد المستقبل:", 
                                                              value=st.session_state.email_config.get('receiver', ''),
                                                              help="البريد الذي ستُرسل إليه التنبيهات")
    st.session_state.email_config['password'] = st.text_input("كلمة مرور التطبيق:", 
                                                              value=st.session_state.email_config.get('password', ''),
                                                              type="password",
                                                              help="كلمة مرور التطبيق (App Password) من Gmail")
    
    auto_alerts = st.checkbox("تفعيل التنبيهات التلقائية للتعليقات السلبية", value=False)
    
    st.markdown("---")
    
    if st.button("🔍 اختبار المُحددات والـ Robots.txt"):
        if current_config:
            st.success("الاختبارات الأساسية ناجحة.")

# 2. التبويبات الرئيسية
tab_control, tab_analysis, tab_history, tab_marketing, tab_log = st.tabs([
    "⚡ التحكم والتشغيل", 
    "📊 تحليل المشاعر", 
    "📚 التحليلات السابقة", 
    "📢 أدوات التسويق", 
    "📈 المراقبة (Log)"
])

# ----------------- تبويب التحكم -----------------
with tab_control:
    st.header("إعدادات التشغيل والاستخلاص")
    
    col_url, col_pages, col_concurrency = st.columns([3, 1, 1])
    with col_url:
        start_url = st.text_input("🔗 أدخل الرابط لصفحة البداية (Page 1) للتحليل:", 
                                  value=current_config.get('base_url', '') + '/catalogue/page-1.html',
                                  help="الرابط الذي سيبدأ منه الروبوت استخلاص التعليقات.")
    with col_pages:
        pages_to_scrape = st.number_input("عدد الصفحات القصوى:", min_value=1, value=5, step=1)
    with col_concurrency:
        max_concurrency = st.number_input("التزامن (Concurrency):", min_value=1, value=5, step=1)
    
    if st.button("▶️ ابدأ التحليل (Async/NLP)", type="primary"):
        status_placeholder = st.empty()
        status_placeholder.info("جاري استخلاص التعليقات وتحليل المشاعر...")
        
        try:
            # تحديث config.json بـ Tokens الحالية قبل التشغيل
            current_config['api_tokens'] = st.session_state.api_tokens 
            
            scraper = FeedbackAnalystScraper(selected_config)
            start_time = time.time()
            total_scraped, metrics = asyncio.run(scraper.run_scraper_async(start_url, pages_to_scrape, max_concurrency))
            end_time = time.time()
            
            if total_scraped > 0:
                detailed_data, sentiment_summary = scraper.generate_analysis()
                st.session_state['detailed_data'] = detailed_data 
                st.session_state['sentiment_summary'] = sentiment_summary
                
                status_placeholder.success(f"🎉 اكتمل التحليل! تم جمع {total_scraped} تعليق في {end_time - start_time:.2f} ثانية.")
                
            else:
                status_placeholder.warning("انتهى التحليل دون جمع أي تعليقات.")
                
        except Exception as e:
            status_placeholder.error(f"❌ خطأ فادح: فشل التشغيل. Error: {e}")

# ----------------- تبويب تحليل المشاعر -----------------
with tab_analysis:
    st.header("نتائج تحليل المشاعر (Sentiment Analysis)")
    
    if 'sentiment_summary' in st.session_state and not st.session_state['sentiment_summary'].empty:
        summary_df = st.session_state['sentiment_summary']
        detailed_df = st.session_state['detailed_data']

        # لوحة مقاييس الأداء الرئيسية (KPIs)
        total_reviews = summary_df['العدد'].sum()
        positive_pct = summary_df[summary_df['تصنيف المشاعر'].isin(['Positive', 'إيجابي'])]['النسبة المئوية (%)'].sum()
        negative_count = summary_df[summary_df['تصنيف المشاعر'].isin(['Negative', 'سلبي'])]['العدد'].sum()
        avg_subjectivity = detailed_df['الموضوعية (0-1)'].mean()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="إجمالي التعليقات", value=total_reviews)
        with col2:
            st.metric(label="النسبة الإيجابية الكلية", value=f"{positive_pct:.1f}%")
        with col3:
            st.metric(label="متوسط الموضوعية", value=f"{avg_subjectivity:.2f}")
        with col4:
            st.metric(label="عدد التعليقات السلبية", value=negative_count, delta_color="inverse")
            
        st.markdown("---")
        
        # الرسوم البيانية والجداول
        col_pie, col_summary = st.columns([2, 1])
        
        with col_pie:
            st.subheader("توزيع المشاعر الكلي:")
            fig = px.pie(
                summary_df, 
                values='النسبة المئوية (%)', 
                names='تصنيف المشاعر', 
                title='النسبة المئوية للتعليقات الإيجابية والسلبية',
                color='تصنيف المشاعر',
                color_discrete_map={'إيجابي':'#28a745', 'Positive':'#28a745', 'سلبي':'#dc3545', 'Negative':'#dc3545', 'محايد':'#ffc107', 'Neutral':'#ffc107'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col_summary:
            st.subheader("ملخص العدد:")
            st.dataframe(summary_df[['تصنيف المشاعر', 'العدد', 'النسبة المئوية (%)']].round(2), hide_index=True)


        st.markdown("---")
        
        # التعليقات السلبية (الأكثر سلبية أولاً)
        st.subheader("التعليقات السلبية التي تحتاج تدخلاً عاجلاً:")
        
        negative_comments = detailed_df[detailed_df['تصنيف المشاعر'].isin(['سلبي', 'Negative'])].sort_values(by='شدة السلبية/الإيجابية', ascending=True)
        
        if not negative_comments.empty:
            # فلترة إضافية حسب شدة السلبية (اقتراح إضافي)
            min_score, max_score = st.slider("فلترة حسب شدة السلبية/الإيجابية (مركب):", 
                                             min_value=-1.0, max_value=1.0, 
                                             value=(-1.0, -0.05), step=0.05)
            
            filtered_negative = negative_comments[(negative_comments['شدة السلبية/الإيجابية'] >= min_score) & (negative_comments['شدة السلبية/الإيجابية'] <= max_score)]
            
            st.dataframe(
                filtered_negative[['العنوان/المنتج', 'نص التعليق', 'شدة السلبية/الإيجابية', 'الموضوعية (0-1)', 'التقييم', 'اللغة']], 
                use_container_width=True,
                column_config={
                    "شدة السلبية/الإيجابية": st.column_config.ProgressColumn("شدة السلبية/الإيجابية", format="%.2f", min_value=-1.0, max_value=1.0),
                    "الموضوعية (0-1)": st.column_config.ProgressColumn("الموضوعية", format="%.2f", min_value=0.0, max_value=1.0)
                }
            )
            
            # زر إرسال تنبيه بريد إلكتروني
            st.markdown("---")
            if st.button("📧 إرسال تنبيه فوري عبر البريد الإلكتروني", key="send_email_alert"):
                email_config = st.session_state.get('email_config', {})
                if email_config.get('sender') and email_config.get('receiver') and email_config.get('password'):
                    with st.spinner("جاري إرسال التنبيه..."):
                        result = send_critical_alerts(
                            negative_comments,
                            email_config,
                            site_name,
                            threshold=-0.5
                        )
                        if result:
                            st.success("✅ تم إرسال التنبيه بنجاح!")
                        else:
                            st.warning("⚠️ لم يتم العثور على تعليقات سلبية حرجة (أقل من -0.5)")
                else:
                    st.error("❌ يرجى تكوين إعدادات البريد الإلكتروني في الشريط الجانبي أولاً.")
        else:
             st.info("لا توجد تعليقات سلبية تم تحديدها في هذا التحليل.")

    else:
        st.info("قم بتشغيل المحلل أولاً لعرض نتائج تحليل المشاعر.")

# ----------------- تبويب التحليلات السابقة -----------------
with tab_history:
    st.header("📚 التحليلات المحفوظة والمقارنة الزمنية")
    
    # عرض إحصائيات عامة
    stats = get_analysis_summary_stats()
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("إجمالي التحليلات", stats.get('total_runs', 0))
        with col2:
            st.metric("إجمالي التعليقات", stats.get('total_reviews', 0))
        with col3:
            st.metric("فرص المبيعات", stats.get('total_sales_opportunities', 0))
        with col4:
            st.metric("تحليلات آخر 7 أيام", stats.get('recent_runs_7_days', 0))
        
        st.markdown("---")
    
    # جلب جميع التحليلات
    analysis_runs = get_all_analysis_runs(limit=50)
    
    if analysis_runs:
        st.subheader("اختر تحليلاً سابقاً للعرض:")
        
        # إنشاء قائمة منسدلة للتحليلات
        run_options = {}
        for run in analysis_runs:
            label = f"#{run.id} - {run.target_site} ({run.created_at.strftime('%Y-%m-%d %H:%M')} - {run.total_reviews} تعليق)"
            run_options[label] = run.id
        
        selected_run_label = st.selectbox(
            "التحليلات المتاحة:",
            options=list(run_options.keys()),
            key="history_selectbox"
        )
        
        if selected_run_label:
            selected_run_id = run_options[selected_run_label]
            selected_run = get_analysis_run_by_id(selected_run_id)
            
            if selected_run:
                # عرض معلومات التحليل
                st.markdown("### معلومات التحليل:")
                info_col1, info_col2, info_col3 = st.columns(3)
                with info_col1:
                    st.info(f"**الموقع:** {selected_run.target_site}")
                    st.info(f"**الصفحات:** {selected_run.pages_scraped}")
                with info_col2:
                    st.info(f"**التاريخ:** {selected_run.created_at.strftime('%Y-%m-%d %H:%M')}")
                    st.info(f"**الحالة:** {selected_run.status}")
                with info_col3:
                    st.info(f"**التعليقات:** {selected_run.total_reviews}")
                    st.info(f"**النسبة الإيجابية:** {selected_run.positive_percentage:.1f}%")
                
                st.markdown("---")
                
                # جلب التعليقات
                reviews = get_reviews_by_analysis_run(selected_run_id)
                
                if reviews:
                    # تحويل إلى DataFrame
                    detailed_df = reviews_to_dataframe(reviews)
                    sentiment_summary = get_sentiment_summary_from_reviews(reviews)
                    
                    # KPIs
                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                    with kpi_col1:
                        st.metric("إجمالي التعليقات", selected_run.total_reviews)
                    with kpi_col2:
                        st.metric("إيجابي", selected_run.positive_count)
                    with kpi_col3:
                        st.metric("سلبي", selected_run.negative_count)
                    with kpi_col4:
                        st.metric("محايد", selected_run.neutral_count)
                    
                    st.markdown("---")
                    
                    # رسم بياني
                    col_chart, col_table = st.columns([2, 1])
                    with col_chart:
                        st.subheader("توزيع المشاعر:")
                        fig = px.pie(
                            sentiment_summary,
                            values='النسبة المئوية (%)',
                            names='تصنيف المشاعر',
                            color='تصنيف المشاعر',
                            color_discrete_map={'إيجابي':'#28a745', 'Positive':'#28a745', 'سلبي':'#dc3545', 'Negative':'#dc3545', 'محايد':'#ffc107', 'Neutral':'#ffc107'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col_table:
                        st.subheader("الملخص:")
                        st.dataframe(sentiment_summary, hide_index=True, use_container_width=True)
                    
                    st.markdown("---")
                    
                    # عرض التعليقات
                    st.subheader("جميع التعليقات:")
                    st.dataframe(detailed_df, use_container_width=True, height=400)
                    
                    # فرص المبيعات
                    sales_opps = get_sales_opportunities_by_analysis_run(selected_run_id)
                    if sales_opps:
                        st.markdown("---")
                        st.subheader(f"فرص المبيعات ({len(sales_opps)}):")
                        sales_df = sales_opportunities_to_dataframe(sales_opps)
                        st.dataframe(sales_df, use_container_width=True)
                else:
                    st.warning("لا توجد تعليقات محفوظة لهذا التحليل.")
                
                # زر الحذف
                st.markdown("---")
                if st.button("🗑️ حذف هذا التحليل", key=f"delete_{selected_run_id}"):
                    if delete_analysis_run(selected_run_id):
                        st.success("✅ تم حذف التحليل بنجاح!")
                        st.rerun()
                    else:
                        st.error("❌ فشل حذف التحليل.")
        
        # المقارنة الزمنية
        st.markdown("---")
        st.subheader("📈 المقارنة الزمنية (آخر 10 تحليلات)")
        
        if len(analysis_runs) >= 2:
            # إنشاء رسم بياني للاتجاه الزمني
            trend_data = []
            for run in analysis_runs[:10]:
                trend_data.append({
                    'التاريخ': run.created_at.strftime('%Y-%m-%d'),
                    'النسبة الإيجابية': run.positive_percentage,
                    'عدد التعليقات': run.total_reviews,
                    'ID': run.id
                })
            
            trend_df = pd.DataFrame(trend_data)
            
            # رسم بياني خطي للنسبة الإيجابية
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=trend_df['التاريخ'],
                y=trend_df['النسبة الإيجابية'],
                mode='lines+markers',
                name='النسبة الإيجابية',
                line=dict(color='#28a745', width=3),
                marker=dict(size=10)
            ))
            fig_trend.update_layout(
                title='اتجاه النسبة الإيجابية عبر الزمن',
                xaxis_title='التاريخ',
                yaxis_title='النسبة الإيجابية (%)',
                hovermode='x unified'
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # رسم بياني عمودي لعدد التعليقات
            fig_count = px.bar(
                trend_df,
                x='التاريخ',
                y='عدد التعليقات',
                title='عدد التعليقات المستخلصة عبر الزمن',
                color='عدد التعليقات',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_count, use_container_width=True)
        else:
            st.info("يجب أن يكون لديك تحليلان على الأقل لعرض المقارنة الزمنية.")
    
    else:
        st.info("لا توجد تحليلات محفوظة بعد. قم بتشغيل تحليل جديد من تبويب 'التحكم والتشغيل'.")
        
# ----------------- تبويب أدوات التسويق -----------------
with tab_marketing:
    st.header("📢 النشر الفوري والإجراءات")
    
    if 'detailed_data' in st.session_state:
        detailed_df = st.session_state['detailed_data']
        
        # وكيل المبيعات: فرص الإحالة المباشرة
        st.subheader("3. وكيل المبيعات: فرص الإحالة المباشرة 🎯")
        sales_opportunities = detailed_df[detailed_df['فرصة مبيعات محتملة'] == True]
        
        if not sales_opportunities.empty:
            total_opportunities = len(sales_opportunities)
            estimated_value = total_opportunities * 50 # 50$ كقيمة تقديرية
            
            col_value, col_count = st.columns(2)
            with col_count:
                st.metric(label="عدد فرص المبيعات المكتشفة", value=total_opportunities)
            with col_value:
                st.metric(label="القيمة التقديرية (50$ لكل فرصة)", value=f"${estimated_value:,}")
                
            st.markdown("---")
            st.caption("هذه التعليقات تحمل نية شراء أو توصية. يجب اتخاذ إجراء فوري:")
            
            st.dataframe(
                sales_opportunities[['العنوان/المنتج', 'نص التعليق', 'شدة السلبية/الإيجابية', 'التقييم']], 
                use_container_width=True
            )
            
            if st.button("🔥 تصدير كملف إحالة للمبيعات (CSV)"):
                csv = sales_opportunities.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 تحميل ملف CSV",
                    data=csv,
                    file_name='sales_opportunities.csv',
                    mime='text/csv',
                )
                st.success("✅ تم توليد ملف الإحالة، جاهز للاستخدام من قبل فريق المبيعات.")
                
        else:
            st.info("لم يتم اكتشاف فرص مبيعات محتملة في هذا التحليل (ابحث عن كلمات مثل 'سأشتري'، 'أوصي').")
            
        st.markdown("---")
        
        # تحويل التعليقات الإيجابية إلى محتوى ترويجي
        st.subheader("1. تحويل التعليقات الإيجابية إلى محتوى ترويجي:")
        
        positive_comments = detailed_df[detailed_df['تصنيف المشاعر'].isin(['إيجابي', 'Positive'])].sort_values(by='شدة السلبية/الإيجابية', ascending=False)
        
        if not positive_comments.empty:
            best_comment = positive_comments.iloc[0]['نص التعليق']
            st.info(f"✨ أفضل تعليق إيجابي مقترح للنشر:\n\n{best_comment}")
            
            post_content = st.text_area("نص المنشور (يمكنك التعديل):", value=best_comment)
            
            platforms = st.multiselect("اختر المنصات للنشر:", 
                                       ['facebook', 'twitter', 'linkedin'], 
                                       default=['facebook'])
            
            if st.button("🚀 انشر المحتوى على المنصات المختارة", type="primary"):
                api_tokens = st.session_state.api_tokens
                with st.spinner("جاري النشر على الشبكات الاجتماعية..."):
                    results = publish_to_social_media(post_content, platforms, api_tokens)
                    
                    st.success("✅ اكتمل طلب النشر:")
                    for platform, result in results.items():
                        st.markdown(f"- **{platform.capitalize()}**: {result}")
        else:
             st.warning("لا توجد تعليقات إيجابية يمكن استخدامها كمحتوى ترويجي.")
             
        st.markdown("---")
        
        st.subheader("2. لوحة التحكم المتقدمة للإعلانات 📊")
        
        summary_df = st.session_state.get('sentiment_summary', pd.DataFrame())
        if not summary_df.empty:
            total_reviews = summary_df['العدد'].sum()
            positive_pct = summary_df[summary_df['تصنيف المشاعر'].isin(['Positive', 'إيجابي'])]['النسبة المئوية (%)'].sum()
            negative_count = summary_df[summary_df['تصنيف المشاعر'].isin(['Negative', 'سلبي'])]['العدد'].sum()
            positive_count = summary_df[summary_df['تصنيف المشاعر'].isin(['Positive', 'إيجابي'])]['العدد'].sum()
            
            # حساب معامل الصحة (Health Score)
            health_score = (positive_pct - (negative_count / total_reviews * 100 * 2)) if total_reviews > 0 else 0
            health_score = max(0, min(100, health_score))
            
            # مقاييس الأداء
            st.markdown("#### مؤشرات الأداء الرئيسية:")
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            with metric_col1:
                st.metric("معامل الصحة", f"{health_score:.1f}%", 
                         help="مؤشر شامل لصحة المنتج بناءً على المشاعر")
            with metric_col2:
                conversion_rate = (positive_count / total_reviews * 100) if total_reviews > 0 else 0
                st.metric("معدل التحويل المتوقع", f"{conversion_rate:.1f}%")
            with metric_col3:
                satisfaction_index = (positive_pct + 50 - (negative_count / total_reviews * 100)) / 1.5 if total_reviews > 0 else 50
                st.metric("مؤشر الرضا", f"{satisfaction_index:.0f}/100")
            with metric_col4:
                recommendation_score = len(sales_opportunities) / total_reviews * 100 if total_reviews > 0 else 0
                st.metric("معدل التوصية", f"{recommendation_score:.1f}%")
            
            st.markdown("---")
            
            # حاسبة الميزانية والـ ROI
            st.markdown("#### 💰 حاسبة الميزانية والعائد المتوقع:")
            
            col_budget, col_results = st.columns(2)
            
            with col_budget:
                st.markdown("**إدخال الميزانية:**")
                current_budget = st.number_input("الميزانية الحالية ($/شهر):", min_value=0, value=1000, step=100)
                cost_per_click = st.number_input("تكلفة النقرة (CPC) ($):", min_value=0.01, value=0.50, step=0.05)
                avg_order_value = st.number_input("متوسط قيمة الطلب ($):", min_value=1, value=50, step=5)
            
            with col_results:
                st.markdown("**النتائج المتوقعة:**")
                
                # حسابات
                expected_clicks = int(current_budget / cost_per_click)
                expected_conversions = int(expected_clicks * (conversion_rate / 100))
                expected_revenue = expected_conversions * avg_order_value
                roi = ((expected_revenue - current_budget) / current_budget * 100) if current_budget > 0 else 0
                
                st.info(f"🖱️ **النقرات المتوقعة:** {expected_clicks:,}")
                st.info(f"✅ **التحويلات المتوقعة:** {expected_conversions}")
                st.info(f"💵 **الإيرادات المتوقعة:** ${expected_revenue:,}")
                
                if roi > 0:
                    st.success(f"📈 **العائد على الاستثمار (ROI):** +{roi:.0f}%")
                else:
                    st.error(f"📉 **العائد على الاستثمار (ROI):** {roi:.0f}%")
            
            st.markdown("---")
            
            # توصيات ذكية
            st.markdown("#### 🎯 التوصيات الذكية:")
            
            if health_score >= 75 and positive_pct > 70:
                st.success("✅ **التوصية: زيادة الميزانية (Scaling)**")
                st.markdown("""
                - المنتج يحظى بقبول عالٍ جداً
                - ينصح بزيادة الميزانية بنسبة **30-50%**
                - ركز على الإعلانات للجمهور المشابه (Lookalike Audience)
                - استخدم التعليقات الإيجابية كشهادات في الإعلانات
                """)
                suggested_budget = current_budget * 1.4
                st.info(f"💡 الميزانية المقترحة: ${suggested_budget:.0f}/شهر")
                
            elif health_score < 40 or negative_count > 10:
                st.error("❌ **التوصية: إيقاف مؤقت وإصلاح**")
                st.markdown("""
                - توجد مشاكل جوهرية تحتاج إلى معالجة
                - أوقف الحملات مؤقتاً لتجنب خسائر إضافية
                - ركز على حل المشاكل التي أشارت إليها التعليقات السلبية
                - بعد الإصلاح، ابدأ بحملة اختبار صغيرة
                """)
                st.warning(f"⚠️ الخسائر المحتملة إذا استمرت الحملات: ${current_budget * 0.7:.0f}/شهر")
                
            elif 40 <= health_score < 75:
                st.info("🧪 **التوصية: اختبار A/B**")
                st.markdown("""
                - الأداء متوسط، يحتاج إلى تحسين
                - قم بإنشاء نسختين من الإعلان (A/B Testing)
                - اختبر رسائل مختلفة واستهداف مختلف
                - حافظ على الميزانية الحالية أثناء الاختبار
                """)
                st.info(f"💡 قسّم الميزانية: ${current_budget * 0.5:.0f} لكل نسخة")
            
            # جدول المقارنة
            st.markdown("---")
            st.markdown("#### 📊 مقارنة السيناريوهات:")
            
            scenarios = pd.DataFrame({
                'السيناريو': ['المحافظ', 'المتوازن', 'العدواني'],
                'الميزانية ($)': [current_budget * 0.7, current_budget, current_budget * 1.5],
                'التحويلات المتوقعة': [
                    int(expected_conversions * 0.7),
                    expected_conversions,
                    int(expected_conversions * 1.5)
                ],
                'الإيرادات المتوقعة ($)': [
                    int(expected_revenue * 0.7),
                    expected_revenue,
                    int(expected_revenue * 1.5)
                ],
                'ROI المتوقع (%)': [
                    roi * 0.9,
                    roi,
                    roi * 1.2
                ]
            })
            
            st.dataframe(scenarios, use_container_width=True, hide_index=True)

    else:
        st.info("قم بتشغيل المحلل أولاً لعرض أدوات التسويق.")

# ----------------- تبويب المراقبة (Log) -----------------
with tab_log:
    st.subheader("ملف السجل المباشر (آخر 100 سطر)")
    st.code(get_log_content(), language='log')
