# app/services/dashboard.py

from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from typing import Dict, Any

from app.models.project import Project
from app.models.boq_item import BoQItem
from app.models.compliance import ComplianceFlag

class DashboardService:

    @staticmethod
    def get_user_dashboard_summary(db: Session, user_id: str) -> Dict[str, Any]:
        
        # 1. تحويل معرف المستخدم إلى UUID
        try:
            user_uuid = uuid.UUID(str(user_id))
        except ValueError:
            user_uuid = user_id

        # جلب المشاريع
        user_projects = db.query(Project).filter(Project.owner_id == user_uuid).all()
        total_projects = len(user_projects)
        
        if total_projects == 0:
            return {
                "total_projects": 0,
                "total_budget_managed": 0.0,
                "total_financial_exposure": 0.0,
                "overall_compliance_score": 100.0,
                "compliance_breakdown": {"open_flags": 0, "resolved_flags": 0, "waived_flags": 0, "total_flags": 0},
                "top_risk_projects": []
            }

        # 2. استخراج المعرفات ككائنات UUID حقيقية فقط (لمنع خطأ hex)
        project_uuids = [p.id for p in user_projects]

        # 3. حساب إجمالي الميزانية
        total_budget = db.query(func.sum(BoQItem.total_price)).filter(
            BoQItem.project_id.in_(project_uuids)
        ).scalar() or 0.0

        # 4. حساب إجمالي التعرض المالي
        user_boq_item_ids = db.query(BoQItem.id).filter(
            BoQItem.project_id.in_(project_uuids)
        ).subquery()

        total_exposure = db.query(func.sum(BoQItem.total_price)).join(
            ComplianceFlag, ComplianceFlag.boq_item_id == BoQItem.id
        ).filter(
            BoQItem.id.in_(user_boq_item_ids),
            ComplianceFlag.status == "open"
        ).scalar() or 0.0

        # 5. تفصيل حالات الامتثال
        flags_query = db.query(
            ComplianceFlag.status, 
            func.count(ComplianceFlag.id)
        ).filter(
            ComplianceFlag.project_id.in_(project_uuids)
        ).group_by(ComplianceFlag.status).all()

        flags_breakdown = {"open": 0, "resolved": 0, "waived": 0}
        for status_obj, count in flags_query:
            # استخراج الكلمة الصافية سواء كانت Enum أو نص
            status_str = str(getattr(status_obj, 'value', status_obj)).lower()
            if "open" in status_str: flags_breakdown["open"] += count
            elif "resolved" in status_str: flags_breakdown["resolved"] += count
            elif "waived" in status_str: flags_breakdown["waived"] += count

        total_flags = sum(flags_breakdown.values())

        # 6. حساب مؤشر الامتثال
        compliance_score = 100.0
        if total_budget > 0:
            compliance_score = ((float(total_budget) - float(total_exposure)) / float(total_budget)) * 100

        # 7. جلب أكثر المشاريع خطورة (مع حساب التعرض لكل مشروع بدقة)
        top_projects_query = db.query(
            ComplianceFlag.project_id, 
            func.count(ComplianceFlag.id).label('flag_count'),
            func.sum(BoQItem.total_price).label('project_exposure')
        ).join(
            BoQItem, ComplianceFlag.boq_item_id == BoQItem.id
        ).filter(
            ComplianceFlag.project_id.in_(project_uuids),
            ComplianceFlag.status == "open"
        ).group_by(ComplianceFlag.project_id).order_by(func.count(ComplianceFlag.id).desc()).limit(3).all()

        top_risk_projects = []
        project_map = {str(p.id): p.project_name for p in user_projects}

        for pid, flag_count, proj_exposure in top_projects_query:
            pid_str = str(pid)
            top_risk_projects.append({
                "project_id": pid_str,
                "project_name": project_map.get(pid_str, "Unknown Project"),
                "total_exposure": float(proj_exposure or 0.0),
                "unresolved_flags": flag_count
            })

        return {
            "total_projects": total_projects,
            "total_budget_managed": float(total_budget),
            "total_financial_exposure": float(total_exposure),
            "overall_compliance_score": round(compliance_score, 2),
            "compliance_breakdown": {
                "open_flags": flags_breakdown["open"],
                "resolved_flags": flags_breakdown["resolved"],
                "waived_flags": flags_breakdown["waived"],
                "total_flags": total_flags
            },
            "top_risk_projects": top_risk_projects
        }