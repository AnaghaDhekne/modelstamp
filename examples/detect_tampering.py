"""Demonstrate rejection of a modified artifact before deserialization."""

from pathlib import Path
from tempfile import TemporaryDirectory

import modelstamp as ms


def main() -> None:
    with TemporaryDirectory() as directory:
        path = Path(directory) / "model.pkl"
        ms.save({"coefficient": 1.25}, path, backend="pickle")

        with path.open("ab") as stream:
            stream.write(b"modified")

        try:
            ms.verify(path)
        except ms.ArtifactIntegrityError as exc:
            print(f"Artifact rejected before loading: {exc}")
        else:  # pragma: no cover - the example should never reach this branch.
            raise RuntimeError("modified artifact unexpectedly passed verification")


if __name__ == "__main__":
    main()
