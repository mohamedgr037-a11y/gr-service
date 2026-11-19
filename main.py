import threading
import time
import os
import sys

# تشغيل خادم Flask في الخلفية
def start_flask():
    from server import app
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

threading.Thread(target=start_flask, daemon=True).start()
time.sleep(3) # انتظار السيرفر ليبدأ

# إعداد واجهة أندرويد باستخدام Kivy و WebView
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock

# محاولة استيراد WebView (يعتمد على منصة أندرويد)
try:
    from jnius import autoclass
    from android.runnable import run_on_ui_thread
    WebView = autoclass('android.webkit.WebView')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
    LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
    LinearLayout = autoclass('android.widget.LinearLayout')

    class WebViewWrapper(BoxLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            Clock.schedule_once(self.load_webview, 1)

        @run_on_ui_thread
        def load_webview(self, dt):
            webview = WebView(activity)
            webview.getSettings().setJavaScriptEnabled(True)
            webview.getSettings().setDomStorageEnabled(True) # لحفظ الدردشة والأذكار
            webview.setWebViewClient(WebViewClient())
            webview.loadUrl("http://127.0.0.1:5000")
            
            # إضافة WebView إلى شاشة أندرويد
            view = activity.getWindow().getDecorView().findViewById(android.R.id.content)
            view.addView(webview, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))

    class GRServiceApp(App):
        def build(self):
            return WebViewWrapper()

    if __name__ == '__main__':
        GRServiceApp().run()

except ImportError:
    # إذا تم التشغيل على الكمبيوتر وليس أندرويد
    print("Not running on Android. Server is running on http://127.0.0.1:5000")
    while True:
        time.sleep(1)
