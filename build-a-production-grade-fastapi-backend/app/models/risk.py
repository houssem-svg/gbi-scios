import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class RiskLedger(Base):
    __tablename__ = "risk_ledgers"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), index=True)
    compliance_flag_id = Column(String, nullable=True)
    risk_type = Column(String)
    severity_level = Column(String)
    financial_exposure = Column(Float, default=0.0)
    probability_score = Column(Float, default=0.0)
    operational_impact = Column(String)
    recommendation = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExposureSimulation(Base):
    __tablename__ = "exposure_simulations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), index=True)
    scenario_name = Column(String)
    simulated_loss = Column(Float, default=0.0)
    win_probability = Column(Float, default=0.0)
    lc_score_impact = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class RiskScenario(Base):
    __tablename__ = "risk_scenarios"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), index=True)
    title = Column(String)
    description = Column(String)
    mitigation_strategy = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)