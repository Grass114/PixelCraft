[app]
title = PixelCraft
package.name = pixelcraft
package.domain = com.grass114

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_exts = spec,pyc,pyo
source.exclude_dirs = tests, bin, __pycache__, .git

version = 1.4.0

requirements = python3,kivy==2.3.0,pillow

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE

android.api = 30
android.minapi = 21
android.sdk = 30
android.ndk = 23b
android.accept_sdk_license = True
android.arch = arm64-v8a
android.enable_androidx = True