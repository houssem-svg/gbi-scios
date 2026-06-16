# app/utils/pdf_helpers.py

import os
import logging
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

logger = logging.getLogger(__name__)

# الطريقة الحديثة والآمنة لتهيئة مشكل الحروف للإصدارات الجديدة 
# دون الحاجة لاستدعاء sub-module 'config'
arabic_processor = arabic_reshaper.ArabicReshaper()

def register_arabic_font() -> str:
    """تسجيل خط TrueType يدعم العربية ديناميكياً"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_font_path = os.path.join(base_dir, "static", "fonts", "Arial.ttf")
    project_font_path_lower = os.path.join(base_dir, "static", "fonts", "arial.ttf")
    
    possible_paths = [
        project_font_path,
        project_font_path_lower,
        "C:\\Windows\\Fonts\\Arial.ttf",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                font_name = "Arabic-Arial"
                pdfmetrics.registerFont(TTFont(font_name, path))
                logger.info(f"✅ Successfully registered font: {font_name} from {path}")
                return font_name
            except Exception as e:
                logger.warning(f"Font found at {path} but failed to register: {str(e)}")
                continue
                
    logger.critical("🚨 No Arabic font found! Falling back to Helvetica.")
    return "Helvetica"

def format_arabic_text(text) -> str:
    """إعادة تشكيل الحروف وتطبيق خوارزمية الاتجاه RTL"""
    if text is None:
        return ""
    text_str = str(text).strip()
    if not text_str:
        return ""
    try:
        reshaped_text = arabic_processor.reshape(text_str)
        return get_display(reshaped_text)
    except Exception as e:
        logger.error(f"Error processing Arabic text: {str(e)}")
        return text_str
