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
CANCEL_BUTTON = "إلغاء"
LOG_PANEL_TITLE = "📋 سجل العمليات"

# Errors and status (user-facing, must stay Arabic per §2.4)
NO_FILES_SELECTED_ERROR = "الرجاء اختيار الملفين المطلوبين أولاً"
GENERIC_PROCESSING_ERROR = "حدث خطأ غير متوقع أثناء المعالجة. راجع سجل العمليات لمزيد من التفاصيل."
CANCELLED_MESSAGE = "تم إلغاء العملية"
MERGE_SUCCESS_MESSAGE = "تم دمج {count} حيازة"
FILE_SAVED_MESSAGE = "تم حفظ الملف: {path}"

# Success dialog
SUCCESS_DIALOG_TITLE = "تمت المعالجة بنجاح"
SUCCESS_DIALOG_MESSAGE = "تم إنشاء الملف بنجاح."
OPEN_FOLDER_BUTTON = "فتح المجلد"
OPEN_FILE_BUTTON = "فتح الملف"
CLOSE_BUTTON = "إغلاق"

# Advanced settings panel
ADVANCED_SETTINGS_TITLE = "⚙ إعدادات متقدمة"
CHOOSE_MAPPING_BUTTON = "اختيار"
DEFAULT_MAPPING_LABEL = "الإعداد الافتراضي"
INCLUDE_LAGHI_LABEL = "تضمين الصفوف الملغاة (لاغى)"
ENABLE_SPATIAL_SORT_LABEL = "تفعيل الترتيب المكاني"
SAVE_PRESET_BUTTON = "حفظ الإعدادات"
LOAD_PRESET_BUTTON = "تحميل الإعدادات"

# Log panel toggle (Iteration 2 §4)
SHOW_LOG_TOGGLE = "📋 عرض سجل العمليات ▾"
HIDE_LOG_TOGGLE = "📋 إخفاء سجل العمليات ▴"

# Statistics panel (Iteration 2 §4)
STATS_PANEL_TITLE = "📊 ملخص النتائج"
STAT_TOTAL_MERGED = "إجمالي الحيازات المدمجة"
STAT_COMPLETE_ROWS = "بيانات كاملة"
STAT_INCOMPLETE_ROWS = "بيانات ناقصة"
STAT_BASE_ONLY = "فقط من ملف المنظومة"
STAT_SECONDARY_ONLY = "فقط من الملف الخارجي"
STAT_WITH_NATIONAL_ID = "مع رقم قومي"
STAT_WITHOUT_NATIONAL_ID = "بدون رقم قومي"
STAT_EXCLUDED_LAGHI = 'صفوف "لاغى" مستبعدة'
STAT_TOTAL_FEDDAN = "إجمالي المساحة (فدان)"
STAT_TOTAL_SQM = "إجمالي المساحة (م²)"
STAT_DISTINCT_BASINS = "عدد الأحواض"
STAT_TOP_BASINS = "أكبر 3 أحواض"
STAT_UNPLACED = "قطع لم يُحدَّد ترتيبها المكاني"
STAT_ELAPSED_TIME = "زمن المعالجة"
STAT_ELAPSED_TIME_UNIT = "{seconds} ث"
COPY_VALUE_TOOLTIP = "نسخ القيمة"
INCOMPLETE_ROWS_POPOVER_TITLE = "الحيازات ذات البيانات الناقصة"
