# Assignment 6 - Banner Grabbing Tool
**Student:** Eng. Dhafer Alyaari  
**Language:** Python

## English
A simple command-line tool that connects to a TCP port and reads the service banner.
It can read immediate banners (such as SSH and FTP). For HTTP services, it sends a `HEAD` request and reads the response headers.

**How to run**
```bash
python banner_grabber.py 127.0.0.1 21,22,80
```
For a web service on another port:
```bash
python banner_grabber.py 127.0.0.1 8081 --mode http
```
Change the IP and ports to a system you own or are authorized to check.

**Output:** port status, the first banner line, and the HTTP `Server` header when available. The tool handles closed ports, connection errors, and timeouts.
A service name or version can only be identified if the server includes it in its response.

**Tests:** run `python -m unittest -v test_banner_grabber` or double-click `Run_Tests.bat` on Windows.  
**Local demo:** run `python demo_local.py` or `Run_Demo.bat`. This starts local example services; it does not scan external networks.

## العربية
برنامج بسيط بلغة **Python** لقراءة بصمة الخدمة (Banner) من منفذ TCP.

- يتصل بعنوان IP ورقم منفذ محدد.
- يقرأ البانر مباشرة من خدمات مثل **SSH** و**FTP**.
- يرسل طلب `HEAD / HTTP/1.1` لخدمات **HTTP** ويعرض أول سطر وترويسة `Server` إن وُجدت.
- يعرض حالة المنفذ ويعالج المهلة الزمنية وأخطاء الاتصال دون إيقاف البرنامج.

**طريقة التشغيل:**
```bash
python banner_grabber.py 127.0.0.1 21,22,80
```

**للتجربة دون شبكة خارجية:** شغّل `demo_local.py` وستظهر أمثلة SSH وFTP وHTTP من خوادم تجريبية محلية.  
**للاختبار:** شغّل `test_banner_grabber.py` بواسطة `python -m unittest -v test_banner_grabber`.

**ملاحظة:** لا يمكن تحديد نظام التشغيل أو إصدار الخدمة بدقة إذا لم يُعلنه الخادم ضمن البانر. استخدم البرنامج فقط على الأنظمة المسموح لك بفحصها.

## Project files / ملفات المشروع
- `banner_grabber.py` - Main program / البرنامج الأساسي
- `test_banner_grabber.py` - Local unit tests / الاختبارات
- `demo_local.py` - Local demo / تجربة محلية
- `Example_Output.txt` - Sample output / مثال النتيجة
- `Test_Report.txt` - Test summary / ملخص الاختبارات
- `Run_Demo.bat`, `Run_Tests.bat`, `Run_Banner_Grabber.bat` - Windows helpers
- `.github/workflows/build-windows.yml` - Builds and adds `Banner_Grabber.exe` automatically after a successful Windows run

## References / المراجع
- Python socket documentation: https://docs.python.org/3/library/socket.html
- GitHub Actions documentation: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
