[app]
title = G-R Service
package.name = grservice
package.domain = org.grservice
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,html,js,css,json,txt
version = 1.0.0
requirements = python3,kivy,flask,requests,urllib3,chardet,idna,certifi,pyjnius,android
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,VIBRATE
android.api = 30
android.minapi = 21
android.ndk = 23b
android.archs = arm64-v8a, armeabi-v7a
android.presplash_color = #f4f7fc
android.build_tools = 30.0.3
