from pathlib import Path
import PyInstaller.__main__
from ra2ce import main as cli_module
from ra2ce import __version__

workpath = Path(__file__).parent.joinpath("build")


def build_cli():
    PyInstaller.__main__.run(
        [
            cli_module.__file__,
            "--name=ra2ce_cli",
            f"--workpath={str(workpath)}",
            f"--specpath={str(workpath)}",
            # f"--icon={str(convert_icon)}",
            "--noconfirm",
            "--onefile",
            "--clean",
        ]
    )
