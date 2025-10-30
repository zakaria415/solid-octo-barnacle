# social_publisher.py

import requests
import logging
import os # إضافة استيراد os
# import json # لا حاجة له ما دمنا لا نقرأ من config.json

LOG_FILENAME = "app_scraper.log" 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILENAME, filemode='a')

def publish_to_social_media(message, platforms): # تم إزالة api_tokens من المعلمات
    """
    ينشر نفس المحتوى على منصات متعددة بضغطة زر.
    (رموز الوصول يتم قراءتها الآن من متغيرات البيئة لضمان الأمان)
    """
    
    results = {}
    
    # 1. النشر على فيسبوك (Facebook Page)
    if 'facebook' in platforms:
        try:
            # القراءة الآمنة مباشرة من متغيرات البيئة
            page_access_token = os.getenv('FACEBOOK_TOKEN') 
            page_id = os.getenv('FACEBOOK_PAGE_ID')
            
            if page_access_token and page_id:
                url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
                payload = {'message': message, 'access_token': page_access_token}
                response = requests.post(url, data=payload)
                
                if response.status_code == 200:
                    results['facebook'] = "✅ تم النشر بنجاح على فيسبوك!"
                    logging.info(f"Published to Facebook: {message[:50]}...")
                else:
                    results['facebook'] = f"❌ فشل فيسبوك: {response.json().get('error', 'غير معروف')}"
            else:
                 results['facebook'] = "⚠️ رموز الوصول لفيسبوك غير متوفرة (تحتاج لتعيين FACEBOOK_TOKEN و FACEBOOK_PAGE_ID في متغيرات البيئة)."
                 
        except Exception as e:
            results['facebook'] = f"❌ خطأ الاتصال بفيسبوك: {e}"

    # 2. النشر على تويتر (X) - (محاكاة)
    if 'twitter' in platforms:
        twitter_token = os.getenv('TWITTER_BEARER_TOKEN')
        if twitter_token:
             results['twitter'] = "⚠️ التويتر/X يحتاج إلى تطبيق منطق النشر الفعلي. (الرمز موجود)"
        else:
             results['twitter'] = "⚠️ رمز الوصول لتويتر غير متوفر (TWITTER_BEARER_TOKEN غير مُعيّن)."
        
    return results