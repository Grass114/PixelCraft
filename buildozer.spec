[app]

# (str) Title of your application
title = PixelCraft

# (str) Package name
package.name = pixelcraft

# (str) Package domain (needed for android/ios packaging)
package.domain = com.grass114

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
# source.include_patterns = assets/*, images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec,pyc,pyo

# (list) List of directory names to not include at all
source.exclude_dirs = tests, bin, __pycache__, .git

# (list) List of exclusions using pattern matching
# source.exclude_patterns = license, images/*/*.jpg

# (str) Application versioning (method 1)
version = 1.4.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# 固定版本号，避免兼容性问题
requirements = python3==3.11.0,kivy==2.3.0,pillow==10.1.0

# (str) Custom source folders for requirements
# requirements.source.kivy = ../../kivy

# (list) Garden requirements
# garden_requirements =

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
# services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# OS X Specific
#

#
# author = © Copyright Info

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 2.3.0

#
# Android Specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain)
# Supported formats are: #RRGGBB #AARRGGBB or one of the following names:
# red, blue, green, black, white, gray, cyan, magenta, yellow, lightgray,
# darkgray, grey, lightgrey, darkgrey, aqua, fuchsia, lime, maroon, navy,
# olive, purple, silver, teal.
# android.presplash_color = #FFFFFF

# (string) Presplash animation using Lottie format.
# see https://lottiefiles.com/ for examples and https://airbnb.design/lottie/
# for general documentation.
# Lottie files can be created using various tools, like Adobe After Effect or SynfigStudio.
# android.presplash_lottie = "path/to/lottie/file.json"

# (str) Adaptive icon of the application (can be file or folder)
# adaptive-icon.filename = %(source.dir)s/data/icon.png

# (list) Permissions
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# ========== 重要：Android SDK/API 配置 ==========
# (int) Android API to use
android.api = 30

# (int) Minimum API required
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 30

# (str) Android NDK version to use
android.ndk = 23b

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (bool) Use --private data storage (True) or --dir internal storage (False)
# android.private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
# android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
# android.sdk_path =

# (str) ANT directory (if empty, it will be automatically downloaded.)
# android.ant_path =

# (bool) If True, then skip trying to update the Android sdk
# android.skip_update = False

# (str) Android entry point, default is ok for Kivy-based app
# android.entrypoint = org.kivy.android.PythonActivity

# (list) Android application build-keep-classes
# android.build_keep_class = java/lang/Object

# (list) List of Java .jar files to add to the classpath
# android.add_src =

# (list) List of Java AAR files to add
# android.add_aar =

# (list) Gradle dependencies to add
# android.gradle_dependencies =

# (list) Android whitelist
# android.whitelist =

# (bool) Enable Android Play Billing (In-app Purchases)
# android.enable_billing = False

# (str) The Android app theme to use
# android.manifest.theme = @android:style/Theme.NoTitleBar

# (str) The Android app launcher theme to use
# android.manifest.launcher_theme = @android:style/Theme.NoTitleBar

# (list) The Android add-on to use
# android.addon =

# (str) The android logcat filters to use
# android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libs folder
# android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# 改用 arm64-v8a（现代 Android 设备主流架构）
android.arch = arm64-v8a

#
# Python for android (p4a) specific
#

# (str) python-for-android branch to use, defaults to master
# p4a.branch = master

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
# p4a.source_dir =

# (str) The directory in which python-for-android should look for your own build recipes (if any)
# p4a.local_recipes =

# (str) Filename to the hook for p4a
# p4a.hook =

# (str) Bootstrap to use for android builds
# p4a.bootstrap = sdl2

# (bool) If True, will bypass all internet downloading and use time-stamped local binaries
# p4a.ignore_update = True

#
# iOS Specific
#

# (str) iOS bundle identifier
# ios.bundle_identifier = com.grass114.pixelcraft

# (str) iOS bundle name
# ios.bundle_name = PixelCraft

# (str) iOS bundle version
# ios.bundle_version = 1.4.0

# (str) iOS minimum version
# ios.minimum_ios_version = 10.0

# (str) iOS plist
# ios.plist = ios/Info.plist

# (str) iOS framework (Kivy or SDL2)
# ios.framework = kivy

# (str) iOS xcode version
# ios.xcode_version = 13.1

# (str) iOS keyboard (one of: default, dark, flint, theme)
# ios.keyboard = default

# (str) iOS font (if font name is not matching standard iOS font, add it in the fonts folder)
# ios.font = DroidSans.ttf

# (bool) If True, will use the iOS published mode (app store mode)
# ios.published_mode = False

#
# Docker specific
#

# (bool) If True, will use docker for building the app
# docker.enable = False

# (str) Docker image to use
# docker.image = kivy/buildozer

#
# Buildozer global config
#

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (bool) Should buildozer don't clean the builds
# build.no_clean = False