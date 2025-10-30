# nltk_setup.py
import nltk
import logging
logging.getLogger('nltk').setLevel(logging.WARNING)
print("--- جاري التحقق من موارد NLTK المطلوبة... ---")

# تحميل الموارد الضرورية لتحليل المشاعر
nltk.download('vader_lexicon', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)

print("NLTK: اكتمل تحميل موارد NLTK بنجاح.")
