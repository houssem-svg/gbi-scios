from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ExecutiveRecommendationRead(BaseModel):
    id: str
    action_type: str
    description: str
    impact_score: str
    model_config = ConfigDict(from_attributes=True)

class AIInsightRead(BaseModel):
    id: str
    project_id: str
    executive_summary: str
    optimization_actions: List[str]
    recommendations: Optional[List[ExecutiveRecommendationRead]] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WaiverStrategyRead(BaseModel):
    id: str
    project_id: str
    compliance_flag_id: Optional[str]
    justification: str
    compensating_control: str
    approval_probability: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)