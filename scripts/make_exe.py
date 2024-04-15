from datetime import datetime
from os import environ
from pathlib import Path

import PyInstaller.__main__
from pyinstaller_versionfile import create_versionfile

from ra2ce import __main__ as cli_module
from ra2ce import __version__

_conda_env = Path(environ["CONDA_PREFIX"])
_root_dir = Path(__file__).parent.parent
_workpath = Path(__file__).parent.joinpath("build")

_cli_name = "ra2ce_cli"


def get_version_file() -> Path:
    """
    Generates a file representing the version attributes to add in the .exe.

    Returns:
        Path: Location of the generated version file.
    """
    _version_file = _workpath.joinpath("version.rc")
    if not _version_file.parent.exists():
        _version_file.parent.mkdir()
    _version_file.touch(exist_ok=True)

    create_versionfile(
        _version_file,
        version=__version__,
        company_name="Deltares",
        legal_copyright=f"Copyright (C) {datetime.now().year} Stichting Deltares",
        product_name="Ra2ce",
        original_filename=f"{_cli_name}.exe",
    )
    return _version_file


def get_hidden_imports() -> list[str]:
    """
    Finds in the conda environment all the packages which could not be directly found
    with `pyinstaller`.

    Returns:
        list[str]: List of `--hidden-import` arguments for the `pyinstaller` call.
    """
    _hidden_imports = []
    _site_packages = _conda_env.joinpath("lib", "site-packages")

    def add_hidden_imports(module_name: str, *extra_imports) -> list[str]:
        _hidden_imports.append(_site_packages.joinpath(module_name))

        for _extra_import in extra_imports:
            _hidden_imports.append(module_name + "." + _extra_import)

        for _rasterio_path in _site_packages.joinpath(module_name).glob("*.py"):
            _hidden_imports.append(module_name + "." + _rasterio_path.stem)

    add_hidden_imports("rasterio", "_shim")
    add_hidden_imports("pygeos", "_geos")
    add_hidden_imports("pyogrio", "_geometry")
    return list(f"--hidden-import={_hi}" for _hi in _hidden_imports)


def build_cli():
    """
    Generates an `.exe` file (with a related binaries directory) using `PyInstaller`.
    """
    _ra2ce_dir = Path(cli_module.__file__).parent
    _logo = _root_dir.joinpath("docs", "_resources", "ra2ce_logo.ico")

    if not _logo.exists():
        from PIL import Image

        img = Image.open(_logo.with_suffix(".png"))
        img.save(_logo)

    PyInstaller.__main__.run(
        [
            cli_module.__file__,
            f"--name={_cli_name}",
            f"--paths=.",
            f"--paths={str(_conda_env)}",
            f"--paths={str(_ra2ce_dir)}",
            f"--paths={str(_root_dir)}",
            *get_hidden_imports(),
            f"--workpath={str(_workpath)}",
            f"--specpath={str(_workpath)}",
            "--icon={}".format(str(_logo)),
            "--copy-metadata=ra2ce",
            f"--version-file={str(get_version_file())}",
            "--noconfirm",
            "--clean",
        ]
    )


if __name__ == "__main__":
    build_cli()
