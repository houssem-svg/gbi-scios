# app/models/reporting.py

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Uuid

from app.core.database import Base  # تم تعديل المسار ليناسب مشروعك

class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ReportType(str, enum.Enum):
    EXECUTIVE = "EXECUTIVE"
    COMPREHENSIVE = "COMPREHENSIVE"

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    generated_by = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    report_type = Column(Enum(ReportType), default=ReportType.EXECUTIVE, nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    
    # تفاصيل البيانات المجمعة لعرضها في لوحة التحكم مستقبلاً
    json_payload = Column(JSON, nullable=True)
    
    # مسار ملف الـ PDF القابل للتحميل
    file_path = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # العلاقات مع الجداول الأخرى
    # project = relationship("Project", back_populates="reports")
