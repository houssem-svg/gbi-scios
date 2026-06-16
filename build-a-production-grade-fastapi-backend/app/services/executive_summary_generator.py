import json
from sqlalchemy.orm import Session
from app.models.ai import AIInsight, ExecutiveRecommendation
from app.services.prompt_builder import build_executive_summary_prompt
from app.services.ai_service import ai_client

async def generate_and_save_insights(db: Session, project_id: str) -> dict:
    # 1. جمع البيانات (سيتم ربطها لاحقاً بـ Risk و Compliance)
    mock_risk = {"exposure": 500000, "level": "MEDIUM"}
    mock_compliance = {"flags": 2, "severity": "MODERATE"}
    
    # 2. بناء الـ Prompt وطلب الذكاء الاصطناعي
    prompt = build_executive_summary_prompt(project_id, mock_risk, mock_compliance)
    ai_response = await ai_client.generate_text(prompt)
    parsed_response = json.loads(ai_response)
    
    # 3. الحفظ في قاعدة البيانات
    insight = AIInsight(
        project_id=str(project_id),
        executive_summary=parsed_response["summary"],
        optimization_actions=parsed_response["actions"]
    )
    db.add(insight)
    db.flush() # للحصول على الـ insight.id
    
    # 4. حفظ التوصيات المرافقة
    rec = ExecutiveRecommendation(
        project_id=str(project_id),
        insight_id=insight.id,
        action_type="MITIGATION",
        description="Immediate restructuring of local procurement process.",
        impact_score="HIGH"
    )
    db.add(rec)
    db.commit()
    
    return {"status": "success", "insight_id": insight.id}