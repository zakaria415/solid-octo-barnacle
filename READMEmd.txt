# 🤖 مشروع المحلل الذكي (Smart Analyzer Agent)

[![GitHub](https://img.shields.io/github/stars/YOUR-USERNAME/Smart-Analyzer-Project?style=social)](https://github.com/YOUR-USERNAME/Smart-Analyzer-Project)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/YOUR-USERNAME/Smart-Analyzer-Project/main/app.py)

---

## 🌟 نظرة عامة على المشروع

هذا المشروع هو عبارة عن **نظام تحليلي متكامل** (Smart Analyzer Agent) مبني على لغة Python وإطار عمل Streamlit. يهدف المشروع إلى أتمتة مهام التحليل، ومعالجة اللغات الطبيعية (باستخدام NLTK)، وإدارة قواعد البيانات، والنشر التلقائي للنتائج على منصات التواصل الاجتماعي.

الواجهة الرئيسية للمشروع يتم عرضها عبر Streamlit.

### المكونات الرئيسية:

* **`app.py`:** ملف التشغيل الرئيسي وواجهة المستخدم التفاعلية (Streamlit App).
* **`ai_assistant.py`:** وحدة الذكاء الاصطناعي المسؤولة عن التحليل.
* **`scraper_core.py`:** وحدة سحب البيانات (Web Scraping).
* **`database.py` / `db_helpers.py`:** وحدات إدارة وتخزين البيانات.
* **`social_publisher.py`:** وحدة النشر التلقائي على منصات التواصل الاجتماعي.

## 🛠️ متطلبات التشغيل والإعداد

المشروع يتطلب بيئة Python 3.

### 1. المتطلبات البرمجية

يجب تثبيت المكتبات التالية (المدرجة في ملف `requirements.txt`):

```bash
streamlit
nltk
pandas
requests
# قد تحتاج إلى مكتبات أخرى مثل pydantic