# email_notifier.py - نظام الإشعارات عبر البريد الإلكتروني

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from database import SessionLocal
from models import EmailNotification

logger = logging.getLogger(__name__)

class EmailNotifier:
    """فئة لإرسال الإشعارات عبر البريد الإلكتروني."""
    
    def __init__(self, email_config):
        self.sender = email_config.get('sender')
        self.password = email_config.get('password')
        self.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = email_config.get('smtp_port', 587)
    
    def send_email(self, recipient, subject, body, analysis_run_id=None, is_html=False):
        """
        إرسال بريد إلكتروني.
        
        Args:
            recipient: عنوان البريد الإلكتروني للمستلم
            subject: موضوع الرسالة
            body: محتوى الرسالة
            analysis_run_id: معرف التحليل (اختياري)
            is_html: هل المحتوى HTML؟
        
        Returns:
            True إذا تم الإرسال بنجاح، False خلاف ذلك
        """
        if not self.sender or not self.password:
            logger.warning("Email credentials not configured")
            self._save_notification_log(recipient, subject, body, analysis_run_id, 'failed', 'Email credentials not configured')
            return False
        
        try:
            # إنشاء الرسالة
            message = MIMEMultipart('alternative')
            message['From'] = self.sender
            message['To'] = recipient
            message['Subject'] = subject
            
            # إضافة المحتوى
            if is_html:
                message.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # الاتصال بالخادم وإرسال الرسالة
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(message)
            
            logger.info(f"✅ Email sent successfully to {recipient}")
            self._save_notification_log(recipient, subject, body, analysis_run_id, 'sent', None)
            return True
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self._save_notification_log(recipient, subject, body, analysis_run_id, 'failed', error_msg)
            return False
    
    def _save_notification_log(self, recipient, subject, body, analysis_run_id, status, error_message):
        """حفظ سجل الإشعار في قاعدة البيانات."""
        db = SessionLocal()
        try:
            notification = EmailNotification(
                analysis_run_id=analysis_run_id,
                recipient=recipient,
                subject=subject,
                body=body[:5000],  # حد أقصى 5000 حرف
                status=status,
                error_message=error_message
            )
            db.add(notification)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save email notification log: {e}")
            db.rollback()
        finally:
            db.close()
    
    def send_negative_review_alert(self, recipient, negative_reviews_df, site_name, analysis_run_id=None):
        """
        إرسال تنبيه عن التعليقات السلبية الحرجة.
        
        Args:
            recipient: عنوان البريد الإلكتروني
            negative_reviews_df: DataFrame يحتوي على التعليقات السلبية
            site_name: اسم الموقع
            analysis_run_id: معرف التحليل
        """
        if negative_reviews_df.empty:
            return False
        
        subject = f"⚠️ تنبيه: تعليقات سلبية حرجة - {site_name}"
        
        # إنشاء محتوى HTML
        html_body = f"""
        <html dir="rtl">
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; direction: rtl; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .review {{ 
                    background-color: #f8f9fa; 
                    padding: 15px; 
                    margin: 10px 0; 
                    border-right: 4px solid #dc3545;
                }}
                .score {{ font-weight: bold; color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ تنبيه: تعليقات سلبية تحتاج إلى تدخل فوري</h1>
            </div>
            <div class="content">
                <p><strong>الموقع:</strong> {site_name}</p>
                <p><strong>التاريخ:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>عدد التعليقات السلبية الحرجة:</strong> {len(negative_reviews_df)}</p>
                <hr>
                <h2>التعليقات السلبية الأكثر حرجة:</h2>
        """
        
        # إضافة أول 5 تعليقات سلبية
        for idx, row in negative_reviews_df.head(5).iterrows():
            title = row.get('العنوان/المنتج', 'N/A')
            review = row.get('نص التعليق', '')
            score = row.get('شدة السلبية/الإيجابية', 0)
            
            html_body += f"""
                <div class="review">
                    <p><strong>المنتج:</strong> {title}</p>
                    <p class="score">درجة السلبية: {score:.2f}</p>
                    <p><strong>التعليق:</strong> {review}</p>
                </div>
            """
        
        html_body += """
                <hr>
                <p><strong>يُنصح باتخاذ إجراء فوري للرد على هذه التعليقات.</strong></p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(recipient, subject, html_body, analysis_run_id, is_html=True)
    
    def send_analysis_summary(self, recipient, analysis_run, sentiment_summary, analysis_run_id=None):
        """
        إرسال ملخص التحليل.
        
        Args:
            recipient: عنوان البريد الإلكتروني
            analysis_run: كائن AnalysisRun
            sentiment_summary: DataFrame ملخص المشاعر
            analysis_run_id: معرف التحليل
        """
        subject = f"✅ اكتمل التحليل - {analysis_run.target_site}"
        
        html_body = f"""
        <html dir="rtl">
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; direction: rtl; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .metric {{ 
                    display: inline-block; 
                    background-color: #f8f9fa; 
                    padding: 15px; 
                    margin: 10px; 
                    border-radius: 5px;
                    min-width: 150px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ اكتمل التحليل</h1>
            </div>
            <div class="content">
                <p><strong>الموقع:</strong> {analysis_run.target_site}</p>
                <p><strong>التاريخ:</strong> {analysis_run.created_at.strftime('%Y-%m-%d %H:%M')}</p>
                <hr>
                <h2>الملخص:</h2>
                <div class="metric">
                    <h3>{analysis_run.total_reviews}</h3>
                    <p>إجمالي التعليقات</p>
                </div>
                <div class="metric">
                    <h3>{analysis_run.positive_percentage:.1f}%</h3>
                    <p>النسبة الإيجابية</p>
                </div>
                <div class="metric">
                    <h3>{analysis_run.positive_count}</h3>
                    <p>إيجابي</p>
                </div>
                <div class="metric">
                    <h3>{analysis_run.negative_count}</h3>
                    <p>سلبي</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(recipient, subject, html_body, analysis_run_id, is_html=True)


def send_critical_alerts(negative_reviews_df, email_config, site_name, threshold=-0.5, analysis_run_id=None):
    """
    إرسال تنبيهات للتعليقات السلبية الحرجة.
    
    Args:
        negative_reviews_df: DataFrame للتعليقات
        email_config: إعدادات البريد الإلكتروني
        site_name: اسم الموقع
        threshold: عتبة السلبية (افتراضي -0.5)
        analysis_run_id: معرف التحليل
    
    Returns:
        True إذا تم الإرسال بنجاح
    """
    # فلترة التعليقات الحرجة
    critical_reviews = negative_reviews_df[
        negative_reviews_df['شدة السلبية/الإيجابية'] <= threshold
    ]
    
    if critical_reviews.empty:
        logger.info("No critical negative reviews found")
        return False
    
    notifier = EmailNotifier(email_config)
    recipient = email_config.get('receiver')
    
    if not recipient:
        logger.warning("No email recipient configured")
        return False
    
    return notifier.send_negative_review_alert(recipient, critical_reviews, site_name, analysis_run_id)
