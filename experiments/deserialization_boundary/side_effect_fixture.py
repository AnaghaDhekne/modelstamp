from pathlib import Path


class MarkerOnLoad:
    """Controlled fixture whose reconstruction creates a harmless marker file."""

    def __reduce__(self):
        marker = Path("/tmp/modelstamp_deserialization_marker")
        return (_write_marker, (str(marker),))


def _write_marker(path):
    Path(path).write_text("deserialized\n", encoding="utf-8")
    return {"marker": path}
