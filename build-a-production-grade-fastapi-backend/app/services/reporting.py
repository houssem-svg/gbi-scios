# app/services/reporting.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
import uuid
import os
from pathlib import Path
from typing import Dict, Any, List

# استيراد أدوات المساعدة لمعالجة النصوص والتراجع التلقائي عن الخطوط
from app.utils.pdf_helpers import register_arabic_font, format_arabic_text

# استيراد أدوات ReportLab لبناء وتنسيق الـ PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.reporting import Report, ReportStatus, ReportType
from app.schemas.reporting import ReportGenerateRequest
from app.models.project import Project 
from app.models.boq_item import BoQItem
from app.models.compliance import ComplianceFlag

class ReportingService:

    @staticmethod
    def generate_report(db: Session, request: ReportGenerateRequest, user_id: str) -> Report:
        """
        محرك التجميع الرئيسي: يتحقق من المشروع، يجمع المؤشرات المالية والامتثالية،
        ويولد سجل التقرير النهائي للجهة السيادية مع طباعة ملف PDF حقيقي.
        """
        try:
            project_uuid = uuid.UUID(request.project_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format for project_id")

        project = db.query(Project).filter(Project.id == project_uuid).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # 1. إنشاء السجل الأولي للتقرير بحالة (PENDING)
        report = Report(
            project_id=project_uuid,
            generated_by=uuid.UUID(str(user_id)) if user_id else None,
            report_type=request.report_type,
            status=ReportStatus.PENDING
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        try:
            # 2. تحديث الحالة إلى PROCESSING لبدء حقن البيانات الذكية
            report.status = ReportStatus.PROCESSING
            db.commit()

            compliance_summary = ReportingService._build_compliance_summary(db, project_uuid)
            exposure_metrics = ReportingService._build_exposure_metrics(db, project_uuid, project)
            risk_profile = ReportingService._build_risk_profile(db, project_uuid, compliance_summary, exposure_metrics)

            aggregated_payload = {
                "metadata": {
                    "project_id": str(project_uuid),
                    "project_name": getattr(project, 'project_name', 'Unknown Project'),
                    "report_id": report.id,
                    "generated_at": report.created_at.isoformat(),
                },
                "compliance_summary": compliance_summary,
                "exposure_metrics": exposure_metrics,
                "risk_profile": risk_profile
            }

            report.json_payload = aggregated_payload
            
            # 3. صياغة وتوليد مسار ملف الـ PDF الحقيقي
            filename = f"exec_{str(project_uuid)}_{uuid.uuid4().hex[:8]}.pdf"
            storage_dir = Path(__file__).resolve().parents[2] / "storage" / "reports"
            
            # التأكد من وجود مجلد التخزين محلياً لمنع الأخطاء
            storage_dir.mkdir(parents=True, exist_ok=True)
            full_pdf_path = str(storage_dir / filename)

            # 4. تشغيل محرك الطباعة لتحويل الـ JSON المجمع إلى وثيقة PDF باللغة العربية
            ReportingService._render_pdf_file(full_pdf_path, aggregated_payload)

            # حفظ المسار النسبي في قاعدة البيانات للتحميل لاحقاً
            report.file_path = f"/storage/reports/{filename}"
            report.status = ReportStatus.COMPLETED
            db.commit()
            db.refresh(report)

        except Exception as e:
            report.status = ReportStatus.FAILED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Report generation failed during PDF rendering: {str(e)}"
            )

        return report

    @staticmethod
    def get_reports_by_project(db: Session, project_id: str) -> List[Report]:
        try:
            project_uuid = uuid.UUID(project_id)
        except ValueError:
            return []
        return db.query(Report).filter(Report.project_id == project_uuid).order_by(Report.created_at.desc()).all()

    @staticmethod
    def download_report(db: Session, report_id: int, user_id: str) -> str:
        """
        التحقق من الصلاحيات وجلب المسار الآمن لملف التقرير من القرص الصلب.
        """
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

        project = db.query(Project).filter(Project.id == report.project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked project not found.")
        
        if str(project.owner_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Access denied. You do not have permission to download reports for this project."
            )

        if not report.file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="PDF file was not generated for this report."
            )

        base_dir = (Path(__file__).resolve().parents[2] / "storage" / "reports").resolve()
        clean_filename = Path(report.file_path).name 
        secure_target_path = (base_dir / clean_filename).resolve()

        if not str(secure_target_path).startswith(str(base_dir)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path sequence.")

        if not secure_target_path.exists() or not secure_target_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="The physical report file is missing from the storage disk."
            )

        return str(secure_target_path)

    # --- محرك توليد ورسم ملفات الـ PDF الحقيقية ثنائي اللغة (Bilingual PDF Sub-Engine) ---

    @staticmethod
    def _render_pdf_file(output_path: str, payload: Dict[str, Any]) -> None:
        """
        رسم وتنسيق ملف الـ PDF التنفيذي وحفظه ميكانيكياً مع دعم كامل ومحكم للنصوص العربية (RTL).
        """
        # تسجيل الخط العربي الآمن (إما Arial المحقون أو التراجع لـ Helvetica)
        active_font = register_arabic_font()
        is_fallback = (active_font == "Helvetica")

        doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        
        styles = getSampleStyleSheet()
        
        # 1. الأنماط القياسية للفقرات الإنجليزية (Left-to-Right)
        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName="Helvetica-Bold", fontSize=22, textColor=colors.HexColor("#1A365D"), spaceAfter=10)
        body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#2D3748"))
        
        # 2. الأنماط الاحترافية للفقرات العربية (Right-to-Left)
        arabic_section_style = ParagraphStyle(
            'ArabicSection', 
            fontName=active_font if not is_fallback else "Helvetica-Bold", 
            fontSize=13, 
            leading=18,
            textColor=colors.HexColor("#2B6CB0"), 
            alignment=2,  # محاذاة لليمين (Right Alignment)
            spaceBefore=14, 
            spaceAfter=6
        )
        
        arabic_body_style = ParagraphStyle(
            'ArabicBody', 
            fontName=active_font, 
            fontSize=10.5, 
            leading=16, 
            textColor=colors.HexColor("#2D3748"), 
            alignment=2  # محاذاة لليمين (Right Alignment)
        )
        
        arabic_alert_style = ParagraphStyle(
            'ArabicAlert', 
            fontName=active_font if not is_fallback else "Helvetica-Bold", 
            fontSize=11, 
            leading=16, 
            textColor=colors.HexColor("#C53030"), 
            alignment=2
        )

        # --- الجزء الأول: الترويسة والمعلومات الفنية المباشرة (English Metadata) ---
        story.append(Paragraph("Executive Compliance & Risk Report", title_style))
        story.append(Paragraph(f"Project ID: {payload['metadata']['project_id']}", body_style))
        story.append(Paragraph(f"Project Name: {payload['metadata']['project_name']}", body_style))
        story.append(Paragraph(f"Generated At: {payload['metadata']['generated_at']}", body_style))
        story.append(Spacer(1, 15))

        # --- الجزء الثاني: الخلاصة التنفيذية للمخاطر (Arabic Executive Summary) ---
        story.append(Paragraph(format_arabic_text("1. الخلاصة التنفيذية والتحليل الأمني للمشروع"), arabic_section_style))
        
        risk_lvl = payload['risk_profile']['risk_level']
        risk_text_raw = f"مستوى الخطورة العام للمشروع: {risk_lvl}"
        story.append(Paragraph(format_arabic_text(risk_text_raw), arabic_alert_style if risk_lvl in ["HIGH", "CRITICAL"] else arabic_body_style))
        
        # سحب النص العربي ومعالجته بدقة ضد مشاكل الانفصال والاتجاه
        summary_raw = payload['risk_profile']['executive_risk_summary']
        story.append(Paragraph(format_arabic_text(summary_raw), arabic_body_style))
        story.append(Spacer(1, 15))

        # --- الجزء الثالث: جدول المقاييس المالية والتعرض (Bilingual Structured Table) ---
        story.append(Paragraph(format_arabic_text("2. مقاييس الامتثال والتعرض المالي والجزاءات"), arabic_section_style))
        story.append(Spacer(1, 4))
        
        # عكس ترتيب الأعمدة برمجياً ليتدفق الجدول من اليمين لليسار (RTL Table Conversion)
        # العمود الأول سيكون الوصف العربي المعالج، العمود الثاني القيمة المالية
        exp_data = [
            [format_arabic_text("مكون ومقياس الامتثال الحرج"), format_arabic_text("القيمة المالية / الأثر المستهدف")],
            [format_arabic_text("إجمالي القيمة المالية غير الممتثلة بالبند"), f"{payload['compliance_summary']['total_non_compliant_value']:,.2f} SAR"],
            [format_arabic_text("التعرض المالي المباشر والنشط (Active Exposure)"), f"{payload['exposure_metrics']['total_financial_exposure']:,.2f} SAR"],
            [format_arabic_text("الغرامات الإلزامية للمحتوى المحلي (حسب نسبة الجزاء المخزّنة 30%)"), f"{payload['exposure_metrics']['mandatory_list_penalties']:,.2f} SAR"],
            [format_arabic_text("تسرّب الرواتب وفق معامل الاعتراف LCP (46.6%)"), f"{payload['exposure_metrics']['estimated_payroll_leakage']:,.2f} SAR"],
            [format_arabic_text("نسبة التعرض المالي الكلي من ميزانية المشروع"), f"% {payload['exposure_metrics']['exposure_percentage_vs_project_budget'] if not is_fallback else payload['exposure_metrics']['exposure_percentage_vs_project_budget']}"]
        ]
        
        # رسم وتصميم الجدول مع محاذاة كافة الحقول جهة اليمين لتناسق المظهر العربي
        t_exposure = Table(exp_data, colWidths=[320, 180])
        t_exposure.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'), # توجيه النصوص لليمين
            ('FONTNAME', (0,0), (-1,-1), active_font),
            ('FONTSIZE', (0,0), (-1,0), 10.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t_exposure)
        story.append(Spacer(1, 15))

        # --- الجزء الرابع: تفصيل البنود الأكثر خطورة إن وجدت (Top Risk Items) ---
        if payload['risk_profile']['top_risk_items']:
            story.append(Paragraph(format_arabic_text("3. تفصيل البنود الأكثر خطورة وحجماً من المخالفات"), arabic_section_style))
            story.append(Spacer(1, 4))
            
            risk_items_data = [[format_arabic_text("كود البند"), format_arabic_text("الوصف الفني للمادة المخالفة"), format_arabic_text("الأثر المالي المباشر")]]
            
            for item in payload['risk_profile']['top_risk_items']:
                risk_items_data.append([
                    format_arabic_text(item['item_code']),
                    format_arabic_text(item['description']),
                    f"{item['financial_impact']:,.2f} SAR"
                ])
                
            t_risk_items = Table(risk_items_data, colWidths=[70, 270, 160])
            t_risk_items.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4A5568")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,-1), active_font),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ]))
            story.append(t_risk_items)

        # طباعة وحفظ المستند التنفيذي على القرص الصلب
        doc.build(story)

    # --- المحركات المساعدة لطبقة تجميع البيانات (Data Aggregation Sub-Engines) ---

    @staticmethod
    def _build_compliance_summary(db: Session, project_id: uuid.UUID) -> Dict[str, Any]:
        flags = db.query(ComplianceFlag).filter(ComplianceFlag.project_id == project_id).all()
        total_violations = len(flags)
        resolved_violations = sum(1 for f in flags if f.status in ["resolved", "waived"])
        unresolved_violations = total_violations - resolved_violations

        total_non_compliant_val = db.query(
            func.sum(BoQItem.total_price)
        ).join(
            ComplianceFlag, ComplianceFlag.boq_item_id == BoQItem.id
        ).filter(
            ComplianceFlag.project_id == project_id
        ).scalar() or 0.0

        # Top violation CATEGORIES (not item codes). Join through the mandatory item
        # to its real category field, replacing the previous incorrect grouping by item_code.
        from app.models.mandatory_list import MandatoryListItem
        top_categories_query = db.query(
            MandatoryListItem.category, func.count(ComplianceFlag.id).label('v_count')
        ).join(
            ComplianceFlag, ComplianceFlag.mandatory_item_id == MandatoryListItem.id
        ).filter(
            ComplianceFlag.project_id == project_id
        ).group_by(MandatoryListItem.category).order_by(func.count(ComplianceFlag.id).desc()).limit(3).all()

        top_categories = [
            {"category": (cat or "Uncategorized"), "count": count}
            for cat, count in top_categories_query
        ]

        return {
            "total_violations": total_violations,
            "resolved_violations": resolved_violations,
            "unresolved_violations": unresolved_violations,
            "total_non_compliant_value": float(total_non_compliant_val),
            "top_violation_categories": top_categories
        }

    @staticmethod
    def _build_exposure_metrics(db: Session, project_id: uuid.UUID, project: Any) -> Dict[str, Any]:
        # Sum exposure of OPEN flags (waived/resolved excluded) and the actual
        # penalty_percentage stored on each flag (0.30 by default). This replaces
        # the previous hardcoded 0.20 factor that contradicted the stored 0.30.
        open_flags = db.query(ComplianceFlag).filter(
            ComplianceFlag.project_id == project_id,
            ComplianceFlag.status == "open"
        ).all()

        total_exposure = sum(float(f.exposure_amount or 0) for f in open_flags)
        # mandatory_list_penalties = sum over flags of (boq_total_price × penalty_percentage).
        # exposure_amount already == boq_total_price × penalty_percentage, so:
        mandatory_penalties = total_exposure

        # LCP payroll leakage = (1 - saudi_payroll_recognition_factor) × saudi_payroll.
        # Until a PayrollRecord feed exists, leakage is 0.0 — NOT a fabricated 7% of exposure.
        # The previous 0.07 factor had no basis in the LCP methodology and is removed.
        payroll_leakage = 0.0
        payroll_recognition_factor = 0.534  # 53.4% of Saudi payroll counts as local content

        project_budget = getattr(project, 'budget', 0.0)
        if project_budget <= 0.0:
            project_budget = db.query(func.sum(BoQItem.total_price)).filter(BoQItem.project_id == project_id).scalar() or 1.0

        exposure_percentage = (float(total_exposure) / float(project_budget)) * 100

        return {
            "total_financial_exposure": float(total_exposure),
            "mandatory_list_penalties": float(mandatory_penalties),
            "estimated_payroll_leakage": float(payroll_leakage),
            "payroll_recognition_factor": payroll_recognition_factor,
            "exposure_percentage_vs_project_budget": round(float(exposure_percentage), 2)
        }

    @staticmethod
    def _build_risk_profile(db: Session, project_id: uuid.UUID, compliance: Dict[str, Any], exposure: Dict[str, Any]) -> Dict[str, Any]:
        unresolved = compliance["unresolved_violations"]
        exposure_pct = exposure["exposure_percentage_vs_project_budget"]

        if unresolved == 0:
            risk_level = "LOW"
            summary = "المشروع ممتثل بالكامل للمتطلبات التنظيمية والمحتوى المحلي السيادي."
        elif exposure_pct > 25 or unresolved > 15:
            risk_level = "CRITICAL"
            summary = "تحذير عالي الخطورة: المشروع يتجاوز حدود التعرض المالي المسموح بها، يتطلب تدخل فوري وسريع للتصحيح."
        elif exposure_pct > 10 or unresolved > 5:
            risk_level = "HIGH"
            summary = "المشروع يواجه ثغرات امتثال واضحة قد تؤدي إلى تسييل غرامات مالية من الجهات التنظيمية."
        else:
            risk_level = "MODERATE"
            summary = "مستوى الخطورة معتدل، توجد ملاحظات امتثال محدودة يمكن معالجتها عبر خطط التصحيح."

        critical_items_query = db.query(
            BoQItem.item_code, BoQItem.description, BoQItem.total_price
        ).join(
            ComplianceFlag, ComplianceFlag.boq_item_id == BoQItem.id
        ).filter(
            ComplianceFlag.project_id == project_id,
            ComplianceFlag.status == "open"
        ).order_by(BoQItem.total_price.desc()).limit(2).all()

        top_risk_items = [
            {"item_code": item[0], "description": item[1], "financial_impact": float(item[2])}
            for item in critical_items_query
        ]

        return {
            "risk_level": risk_level,
            "critical_flags_count": unresolved,
            "top_risk_items": top_risk_items,
            "executive_risk_summary": summary
        }
