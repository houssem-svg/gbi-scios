import json
from sqlalchemy.orm import Session
from app.models.ai import WaiverStrategy
from app.services.prompt_builder import build_waiver_prompt
from app.services.ai_service import ai_client

async def generate_and_save_waiver(db: Session, project_id: str) -> dict:
    mock_flag = {"issue": "Local Content Quota unmet", "penalty": "5% deduction"}
    
    prompt = build_waiver_prompt(mock_flag)
    ai_response = await ai_client.generate_text(prompt)
    parsed_response = json.loads(ai_response)
    
    waiver = WaiverStrategy(
        project_id=str(project_id),
        justification=parsed_response["justification"],
        compensating_control=parsed_response["control"],
        approval_probability=parsed_response["probability"]
    )
    db.add(waiver)
    db.commit()
    
    return {"status": "success", "waiver_id": waiver.id}