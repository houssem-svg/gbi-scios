"""Central model registry — imports every model so SQLAlchemy's
``Base.metadata`` (and therefore Alembic autogenerate) sees the full set.
"""

from app.models.ai import AIInsight, ExecutiveRecommendation, WaiverStrategy
from app.models.bid import Bid, EvaluationFormula
from app.models.boq_item import BoQItem, SourcingType
from app.models.compliance import ComplianceFlag, ComplianceFlagStatus, ViolationType
from app.models.evaluation import EvaluationCriteria, EvaluationResult
from app.models.mandatory_list import MandatoryListItem, MandatoryStatus
from app.models.project import Project, ProjectStatus
from app.models.reporting import Report, ReportStatus, ReportType
from app.models.risk import ExposureSimulation, RiskLedger, RiskScenario
from app.models.supplier import Supplier, SupplierSizeCategory
from app.models.uploaded_file import UploadedFile, UploadedFileType
from app.models.user import User, UserRole

__all__ = [
    "AIInsight",
    "Bid",
    "BoQItem",
    "ComplianceFlag",
    "ComplianceFlagStatus",
    "EvaluationCriteria",
    "EvaluationFormula",
    "EvaluationResult",
    "ExecutiveRecommendation",
    "ExposureSimulation",
    "MandatoryListItem",
    "MandatoryStatus",
    "Project",
    "ProjectStatus",
    "Report",
    "ReportStatus",
    "ReportType",
    "RiskLedger",
    "RiskScenario",
    "SourcingType",
    "Supplier",
    "SupplierSizeCategory",
    "UploadedFile",
    "UploadedFileType",
    "User",
    "UserRole",
    "ViolationType",
    "WaiverStrategy",
]
