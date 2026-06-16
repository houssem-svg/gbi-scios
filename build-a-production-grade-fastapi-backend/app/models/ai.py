import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from app.core.database import Base

class AIInsight(Base):
    __tablename__ = "ai_insights"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, index=True, nullable=False)
    executive_summary = Column(Text, nullable=False)
    optimization_actions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExecutiveRecommendation(Base):
    __tablename__ = "executive_recommendations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, index=True, nullable=False)
    insight_id = Column(String, ForeignKey("ai_insights.id"), nullable=False)
    action_type = Column(String, nullable=False) # e.g., "MITIGATION", "STRATEGIC"
    description = Column(Text, nullable=False)
    impact_score = Column(String, nullable=False) # e.g., "HIGH", "MEDIUM"

class WaiverStrategy(Base):
    __tablename__ = "waiver_strategies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, index=True, nullable=False)
    compliance_flag_id = Column(String, nullable=True) # المرتبط بالمخالفة إن وجد
    justification = Column(Text, nullable=False)
    compensating_control = Column(Text, nullable=False)
    approval_probability = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)