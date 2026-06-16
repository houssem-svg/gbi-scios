# seed_boq.py

import uuid
from app.core.database import SessionLocal
from app.models.boq_item import BoQItem, SourcingType

def seed_test_boq_items():
    db = SessionLocal()
    try:
        # معرف المشروع ومعرف الملف الذي رفعته للتو
        project_uuid = uuid.UUID("2b2ae39f-f627-4825-ac61-eb61af52ccda")
        file_uuid = uuid.UUID("bb5639c6-7a40-49a8-b69e-27d3f67e0136")

        # تجهيز البنود الأربعة التي كانت في ملف الـ CSV
        items = [
            BoQItem(
                project_id=project_uuid, uploaded_file_id=file_uuid, 
                item_code="C001", description="أسمنت وطني مقاوم للأملاح", 
                quantity=1000, unit_price=25.00, total_price=25000.00, 
                sourcing_type=SourcingType.LOCAL
            ),
            BoQItem(
                project_id=project_uuid, uploaded_file_id=file_uuid, 
                item_code="S001", description="حديد تسليح مستورد عالي الشد", 
                quantity=500, unit_price=3000.00, total_price=1500000.00, 
                sourcing_type=SourcingType.IMPORTED
            ),
            BoQItem(
                project_id=project_uuid, uploaded_file_id=file_uuid, 
                item_code="M001", description="رخام أرضيات إيطالي", 
                quantity=200, unit_price=450.00, total_price=90000.00, 
                sourcing_type=SourcingType.IMPORTED
            ),
            BoQItem(
                project_id=project_uuid, uploaded_file_id=file_uuid, 
                item_code="W001", description="أبواب خشبية محلية الصنع", 
                quantity=50, unit_price=1200.00, total_price=60000.00, 
                sourcing_type=SourcingType.LOCAL
            )
        ]
        
        db.add_all(items)
        db.commit()
        print("✅ تم حقن بنود الـ BOQ الأربعة في قاعدة البيانات بنجاح!")
        
    except Exception as e:
        print(f"❌ حدث خطأ: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_boq_items()