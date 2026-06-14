[app]
title = Samurai Arena Fight
package.name = samuraiarenafight
package.domain = com.crisvarela98
source.dir = .
source.include_exts = py,png,jpg,jpeg,json,wav,mp3,ttf
source.include_patterns = assets/*,assets/**/*,data/*,data/**/*,config/*,src/*,src/**/*,p4a-recipes/**/*
source.exclude_dirs = tmp,.pytest_cache,__pycache__,.venv
version = 0.1.0
requirements = python3,pygame-ce,requests,python-socketio,websocket-client
orientation = landscape
fullscreen = 1
android.permissions = INTERNET,WAKE_LOCK,VIBRATE
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a
android.wakelock = True
android.enable_androidx = True
android.copy_libs = 1
android.logcat_filters = *:S python:D SDL:D
p4a.bootstrap = sdl2
p4a.local_recipes = ./p4a-recipes

[buildozer]
log_level = 2
warn_on_root = 1
