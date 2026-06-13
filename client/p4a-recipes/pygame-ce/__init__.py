from os.path import join

from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.toolchain import current_directory


class PygameCeRecipe(CompiledComponentsPythonRecipe):
    version = "2.4.0"
    url = "https://github.com/pygame-community/pygame-ce/archive/{version}.tar.gz"
    site_packages_name = "pygame-ce"
    name = "pygame-ce"
    depends = ["sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf", "setuptools", "jpeg", "png"]
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            with open(join("buildconfig", "Setup.Android.SDL2.in"), encoding="utf-8") as template_file:
                setup_template = template_file.read()
            png = self.get_recipe("png", self.ctx)
            png_lib_dir = join(png.get_build_dir(arch.arch), ".libs")
            png_inc_dir = png.get_build_dir(arch.arch)
            jpeg = self.get_recipe("jpeg", self.ctx)
            jpeg_inc_dir = jpeg_lib_dir = jpeg.get_build_dir(arch.arch)
            mixer_includes = "".join(
                f"-I{include_dir} "
                for include_dir in self.get_recipe("sdl2_mixer", self.ctx).get_include_dirs(arch)
            )
            setup_file = setup_template.format(
                sdl_includes=(
                    " -I" + join(self.ctx.bootstrap.build_dir, "jni", "SDL", "include")
                    + " -L" + join(self.ctx.bootstrap.build_dir, "libs", str(arch))
                    + " -L" + png_lib_dir
                    + " -L" + jpeg_lib_dir
                    + " -L" + arch.ndk_lib_dir_versioned
                ),
                sdl_ttf_includes="-I" + join(self.ctx.bootstrap.build_dir, "jni", "SDL2_ttf"),
                sdl_image_includes="-I" + join(self.ctx.bootstrap.build_dir, "jni", "SDL2_image"),
                sdl_mixer_includes=mixer_includes,
                jpeg_includes="-I" + jpeg_inc_dir,
                png_includes="-I" + png_inc_dir,
                freetype_includes="",
            )
            with open("Setup", "w", encoding="utf-8") as setup_output:
                setup_output.write(setup_file)

    def get_recipe_env(self, arch):
        environment = super().get_recipe_env(arch)
        environment["USE_SDL2"] = "1"
        environment["PYGAME_CROSS_COMPILE"] = "TRUE"
        environment["PYGAME_ANDROID"] = "TRUE"
        environment["ANDROID_ROOT"] = join(self.ctx.ndk.sysroot, "usr")
        return environment


recipe = PygameCeRecipe()
