from pathlib import Path
from typing import Any, Protocol


class Ra2ceExporterProtocol(Protocol):
    def export(self, export_path: Path, export_data: Any) -> None:
        pass
