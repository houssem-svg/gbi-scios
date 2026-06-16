import uuid
from sqlalchemy.orm import Session
from app.models.risk import RiskLedger
from app.models.compliance import ComplianceFlag
from app.services.executive_summary_service import generate_summary_and_actions

def calculate_severity(exposure: float) -> str:
    if exposure < 100000: return "LOW"
    elif exposure < 1000000: return "MODERATE"
    elif exposure < 10000000: return "HIGH"
    return "CRITICAL"

def calculate_project_risk(db: Session, project_id: str):
    # 1. تحويل المعرف النصي إلى كائن UUID للبحث
    if isinstance(project_id, str):
        valid_project_id = uuid.UUID(project_id)
    else:
        valid_project_id = project_id

    # 2. جلب المخالفات من قاعدة البيانات بأمان
    flags = db.query(ComplianceFlag).filter(ComplianceFlag.project_id == valid_project_id).all()
    
    # 3. حساب المخاطر المالية بأمان
    total_exposure = 0.0
    for flag in flags:
        if flag.exposure_amount:
            try:
                total_exposure += float(flag.exposure_amount)
            except ValueError:
                pass
    
    payroll_leakage = 0.0 
    total_sovereign_exposure = total_exposure + payroll_leakage
    
    severity = calculate_severity(total_sovereign_exposure)
    summary, actions = generate_summary_and_actions(severity, total_sovereign_exposure)
    
    # 4. تسجيل الخطر (تحويل الـ UUID إلى نص هنا لكي تقبله SQLite بدون مشاكل)
    ledger = RiskLedger(
        project_id=str(valid_project_id),  # <--- هذا هو التعديل السحري لحل المشكلة!
        risk_type="COMPLIANCE_AND_LEAKAGE",
        severity_level=severity,
        financial_exposure=total_sovereign_exposure,
        recommendation=actions[0] if actions else "Review operations"
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)
    
    return {
        "total_exposure": total_sovereign_exposure,
        "risk_breakdown": [ledger],
        "executive_summary": summary,
        "mitigation_actions": actions,
        "win_probability": 30.0 if severity == "CRITICAL" else 85.0
    }