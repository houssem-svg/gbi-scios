# seed_mandatory.py

from app.core.database import SessionLocal
from app.models.mandatory_list import MandatoryListItem

def seed_test_mandatory_items():
    db = SessionLocal()
    try:
        # مسح البيانات السابقة لتجنب التكرار
        db.query(MandatoryListItem).delete()
        
        # حقن المواد مع توفير كافة الحقول الإجبارية (Category و Local Manufacturer)
        items = [
            MandatoryListItem(
                item_code="S001", 
                product_name="حديد تسليح", 
                category="مواد بناء",
                local_manufacturer="المصنع الوطني للحديد"  # الحقل الجديد المطلوب
            ),
            MandatoryListItem(
                item_code="M001", 
                product_name="رخام أرضيات", 
                category="تشطيبات",
                local_manufacturer="شركة الرخام السعودي"  # الحقل الجديد المطلوب
            )
        ]
        
        db.add_all(items)
        db.commit()
        print("✅ تم حقن القائمة الإلزامية بنجاح! المحرك الآن يعرف الممنوعات.")
        
    except Exception as e:
        print(f"❌ حدث خطأ: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_mandatory_items()