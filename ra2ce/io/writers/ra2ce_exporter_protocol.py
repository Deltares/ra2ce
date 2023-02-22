from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Ra2ceExporterProtocol(Protocol):
    def export(self, export_path: Path, export_data: Any) -> None:  # pragma: no cover
        """
        Exports the given data to the given path.

        Args:
            export_path (Path): File path where to save the `export_data`.
            export_data (Any): Data to be exported.
        """
        pass
