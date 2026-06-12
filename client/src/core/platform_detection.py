import importlib.util
import os
import sys


def detect_runtime_platform():
    platform_name = sys.platform.lower()
    android_markers = (
        "ANDROID_ARGUMENT",
        "ANDROID_APP_PATH",
        "ANDROID_PRIVATE",
        "P4A_BOOTSTRAP",
        "P4A_IS_WINDOWED",
    )

    if platform_name.startswith("android") or platform_name == "ios":
        return "android"
    if any(os.environ.get(marker) for marker in android_markers):
        return "android"
    if importlib.util.find_spec("android") is not None:
        return "android"
    return "pc"


def platform_display_name(platform_id):
    return "CELULAR / ANDROID" if platform_id == "android" else "PC / ESCRITORIO"


def platform_runtime_message(platform_id):
    if platform_id == "android":
        return "Botones tactiles activos automaticamente durante el combate."
    return "Teclado activo automaticamente. Los botones tactiles quedan ocultos."
