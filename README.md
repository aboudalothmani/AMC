# Eye Mouse Control

مشروع سطح مكتب لنظام Windows يتيح التحكم بالمؤشر باستخدام حركة العين والرأس عبر كاميرا الويب. يعتمد التطبيق على تتبع الوجه والعينين محلياً على الجهاز، مع واجهة رسومية للمعايرة، حفظ الإعدادات، وعرض مؤشرات الأداء أثناء التشغيل.

## ما الذي يقدمه المشروع؟

- التحكم بالمؤشر اعتماداً على اتجاه النظر وحركة الرأس.
- معايرة ذكية من 9 نقاط لتحسين دقة التوجيه على الشاشة.
- أوضاع نقر متعددة:
  - `Blink` للنقر بالرمش.
  - `Dwell` للنقر بعد تثبيت المؤشر.
  - `Off` لإيقاف النقر التلقائي.
- دعم الشاشات المتعددة مع اختيار الشاشة المستهدفة من الواجهة.
- عرض مباشر للكamera مع معلومات تشخيصية مثل FPS، جودة التتبع، ووضع الرأس.
- حفظ الإعدادات في ملفات المشروع والعمل محلياً بدون خدمات سحابية.

## التقنيات المستخدمة

- Python 3.10
- OpenCV
- MediaPipe
- OpenVINO
- PyQt6 / PySide6
- NumPy / SciPy

## بنية المستودع

- `EyeMouseControl/`: مجلد التطبيق الرئيسي.
- `EyeMouseControl/src/`: كود التطبيق.
- `EyeMouseControl/config/`: ملفات الإعدادات والمعايرة.
- `EyeMouseControl/models/`: ملفات النماذج المطلوبة للتتبع.
- `EyeMouseControl/tests/`: اختبارات الوحدة.
- `EyeMouseControl/docs/`: وثائق إضافية.

## المتطلبات

- Windows 10 أو Windows 11
- Python 3.10
- كاميرا ويب تعمل بشكل جيد ويفضل 720p أو أعلى

## التشغيل الكامل

### 1. استنساخ المستودع

```powershell
git clone https://github.com/aboudalothmani/AMC.git
cd AMC
cd EyeMouseControl
```

### 2. إنشاء بيئة افتراضية

```powershell
python -m venv .venv
```

### 3. تفعيل البيئة الافتراضية

على PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

على Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

### 4. تثبيت الاعتمادات

```powershell
pip install -r requirements.txt
```

### 5. التأكد من وجود النماذج

غالباً يحتوي المستودع على النماذج داخل `models/`. إذا كانت غير موجودة أو ناقصة، شغّل:

```powershell
python download_models.py
```

### 6. تشغيل التطبيق

```powershell
python src/main.py
```

## خطوات الاستخدام لأول مرة

1. شغّل التطبيق بالأمر `python src/main.py`.
2. اختر الشاشة المستهدفة من قسم `Target Monitor`.
3. اضغط `Start Smart Calibration`.
4. اتبع نقاط المعايرة التسع مع تثبيت الرأس والنظر مباشرة إلى الهدف.
5. اختر وضع النقر المناسب من `Click Mode`.
6. عدّل الحساسية من `Cursor Sensitivity`.
7. اضغط `Save Settings` لحفظ الإعدادات.

## الاختصارات

- `Ctrl + Alt + E`: تفعيل أو إيقاف وضع الراحة
- `Ctrl + Alt + M`: التبديل بين أوضاع النقر
- `Ctrl + Alt + C`: بدء المعايرة

## ملفات الإعداد المهمة

- `config/default_config.json`: الإعدادات الأساسية مثل الكاميرا، الحساسية، النقر، والاختصارات.
- `config/calibration.json`: بيانات المعايرة المحفوظة.

## التشغيل أثناء التطوير

إذا أردت تشغيل الاختبارات:

```powershell
$env:PYTHONPATH='src'
pytest -q
```

## ملاحظات مهمة

- التطبيق مصمم أساساً للعمل على Windows.
- المعايرة مرتبطة بالشاشة المختارة، لذلك من الأفضل إعادة المعايرة بعد تغيير الشاشة.
- السجلات تكتب في:
  - `logs/eyemouse.log`
- عكس المعاينة `Mirror Preview` يؤثر على العرض فقط، وليس على منطق التتبع.

## استكشاف الأعطال

إذا لم يعمل التطبيق بشكل صحيح، راجع النقاط التالية:

- تأكد من استخدام Python 3.10.
- تأكد من أن الكاميرا غير مشغولة من تطبيق آخر.
- تأكد من تثبيت الحزم بنجاح من `requirements.txt`.
- إذا كانت ملفات النماذج ناقصة، شغّل `python download_models.py`.
- راجع ملف السجل `logs/eyemouse.log` لمعرفة سبب الخطأ.

## ملخص سريع

بعد الاستنساخ، التسلسل المعتاد للتشغيل هو:

```powershell
cd AMC\EyeMouseControl
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/main.py
```
