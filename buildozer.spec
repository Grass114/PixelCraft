[app]
title = PixelCraft
package.name = pixelcraft
package.domain = com.grass114

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_exts = spec,pyc,pyo
source.exclude_dirs = tests, bin, __pycache__, .git

version = 1.0

requirements = python3==3.9.0,kivy==2.1.0,pillow==8.4.0

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 30
android.minapi = 21
android.sdk = 30
android.ndk = 23b
android.accept_sdk_license = True
android.arch = arm64-v8a
android.enable_androidx = True