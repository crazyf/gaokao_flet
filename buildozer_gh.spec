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

# ★★★ 关键：直接指向 GitHub Actions 预装的 NDK ★★★
android.ndk = 25b
android.ndk_path = /usr/local/lib/android/sdk/ndk/25.2.9519653

log_level = 2

[buildozer]

log_level = 2