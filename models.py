# models.py - نماذج قاعدة البيانات

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class AnalysisRun(Base):
    """جدول لحفظ معلومات كل عملية تحليل."""
    __tablename__ = 'analysis_runs'
    
    id = Column(Integer, primary_key=True, index=True)
    target_site = Column(String(500), nullable=False)
    start_url = Column(String(1000), nullable=False)
    pages_scraped = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    positive_percentage = Column(Float, default=0.0)
    avg_compound_score = Column(Float, default=0.0)
    avg_subjectivity = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    
    # العلاقة مع التعليقات
    reviews = relationship("Review", back_populates="analysis_run", cascade="all, delete-orphan")
    sales_opportunities = relationship("SalesOpportunity", back_populates="analysis_run", cascade="all, delete-orphan")

class Review(Base):
    """جدول لحفظ كل مراجعة/تعليق تم استخلاصها."""
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_run_id = Column(Integer, ForeignKey('analysis_runs.id'), nullable=False)
    
    title = Column(String(1000), nullable=True)
    review_text = Column(Text, nullable=False)
    rating = Column(String(50), nullable=True) # يمكن أن يكون string مثل "4/5"
    sentiment_label = Column(String(50), nullable=True) # إيجابي، سلبي، محايد
    compound_score = Column(Float, nullable=True) # درجة المشاعر المركبة
    subjectivity = Column(Float, nullable=True)
    language = Column(String(10), default='unknown')
    has_sales_intent = Column(Boolean, default=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقة
    analysis_run = relationship("AnalysisRun", back_populates="reviews")

class SalesOpportunity(Base):
    """جدول لحفظ فرص المبيعات المكتشفة."""
    __tablename__ = 'sales_opportunities'
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_run_id = Column(Integer, ForeignKey('analysis_runs.id'), nullable=False)
    
    product_title = Column(String(1000), nullable=True)
    review_text = Column(Text, nullable=False)
    compound_score = Column(Float, nullable=False)
    estimated_value = Column(Float, default=50.0)  # القيمة التقديرية بالدولار
    status = Column(String(50), default='pending')  # pending, contacted, converted, lost
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقة
    analysis_run = relationship("AnalysisRun", back_populates="sales_opportunities")

class EmailNotification(Base):
    """جدول لحفظ سجل الإشعارات المرسلة."""
    __tablename__ = 'email_notifications'
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_run_id = Column(Integer, ForeignKey('analysis_runs.id'), nullable=True)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    sent_status = Column(String(50), default='Pending') # Sent, Failed, Pending
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقة
    analysis_run_id_fk = relationship("AnalysisRun")