[app]

title = GaokaoQuery
package.name = gaokaoquery
package.domain = org.gaokao

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db

version = 0.1
requirements = python3==3.11.10,kivy==2.3.0,pymysql

android.permissions = INTERNET
android.api = 30
android.minapi = 21
android.accept_sdk_license = True

# 只用这一行指定 NDK 路径
android.ndk_path = /home/zyf/.buildozer/android/platform/android-ndk-r23c

log_level = 2

[buildozer]

log_level = 2

warn_on_root = 1