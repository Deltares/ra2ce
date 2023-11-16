from pathlib import Path
import PyInstaller.__main__
from ra2ce import main as cli_module
from ra2ce import __version__
from os import environ


def build_cli():

    _conda_env = Path(environ["CONDA_PREFIX"])
    _site_packages = _conda_env.joinpath("lib", "site-packages")
    _hidden_imports = []

    def add_hidden_imports(module_name: str, *extra_imports) -> list[str]:
        _hidden_imports.append(_site_packages.joinpath(module_name))

        for _extra_import in extra_imports:
            _hidden_imports.append(module_name + "." + _extra_import)

        for _rasterio_path in _site_packages.joinpath(module_name).glob("*.py"):
            _hidden_imports.append(module_name + "." + _rasterio_path.stem)

    add_hidden_imports("rasterio", "_shim")
    add_hidden_imports("pygeos", "_geos")
    add_hidden_imports("pyogrio", "_geometry")

    _workpath = Path(__file__).parent.joinpath("build")
    _ra2ce_dir = Path(cli_module.__file__).parent
    _root_dir = Path(__file__).parent.parent
    PyInstaller.__main__.run(
        [
            cli_module.__file__,
            "--name=ra2ce_cli",
            f"--paths=.",
            f"--paths={str(_conda_env)}",
            f"--paths={str(_ra2ce_dir)}",
            f"--paths={str(_root_dir)}",
            *list(f"--hidden-import={_hi}" for _hi in _hidden_imports),
            f"--workpath={str(_workpath)}",
            f"--specpath={str(_workpath)}",
            # "--add-data={}:README.md".format(str(_root_dir.joinpath("README.md"))),
            # f"--icon={str(convert_icon)}",
            "--noconfirm",
            "--onefile",
            "--clean",
        ]
    )


if __name__ == "__main__":
    build_cli()
