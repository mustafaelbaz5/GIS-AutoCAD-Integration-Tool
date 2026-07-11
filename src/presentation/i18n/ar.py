"""Centralized Arabic UI strings, per project brief §2.4.

All user-facing Arabic text is referenced via these constants — never
scattered as magic strings across the presentation layer. Log messages
stay in English (see `infrastructure/logging_setup.py`); this module is
for text the user sees.
"""

APP_TITLE = "أداة تجهيز بيانات نظم المعلومات الجغرافية وأوتوكاد"

# Drop zones
BASE_FILE_TITLE = "الملف الأساسي"
SECONDARY_FILE_TITLE = "الملف الخارجي"
DROP_PLACEHOLDER = "⬇ اسحب الملف هنا أو انقر للاختيار"
INVALID_FILE_TYPE = "الملف يجب أن يكون بصيغة xlsx"
FILE_READ_ERROR = "تعذر قراءة الملف"

# Output path selector
OUTPUT_LABEL = "📁 حفظ في:"
CHANGE_BUTTON = "تغيير"
CHOOSE_FOLDER_TITLE = "اختر مجلد الحفظ"

# Processing
START_BUTTON = "▶  بدء المعالجة"
LOG_PANEL_TITLE = "📋 سجل العمليات"
