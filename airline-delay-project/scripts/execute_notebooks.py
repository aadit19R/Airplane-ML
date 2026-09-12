"""Execute each notebook in a fresh kernel using this Python environment."""
import os
from pathlib import Path
import sys
import tempfile

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "airline-matplotlib"))
os.environ.setdefault("IPYTHONDIR", str(Path(tempfile.gettempdir()) / "airline-ipython"))
os.environ.setdefault("JUPYTER_RUNTIME_DIR", str(Path(tempfile.gettempdir()) / "airline-jupyter"))


def main():
    names = sys.argv[1:] or ["01_beginner_eda.ipynb", "02_feature_engineering.ipynb"]
    for name in names:
        path = PROJECT_ROOT / "notebooks" / name
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        manager = KernelManager(kernel_name="python3")
        manager.kernel_spec.argv[0] = sys.executable
        client = NotebookClient(notebook, km=manager, timeout=300,
                                resources={"metadata": {"path": str(PROJECT_ROOT)}})
        # An explicitly supplied manager must be shut down by its caller.
        try:
            client.execute()
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
        nbformat.write(notebook, path)
        code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
        assert all(cell.execution_count is not None for cell in code_cells)
        print(f"Executed {name}: {len(code_cells)} code cells, no errors", flush=True)


if __name__ == "__main__":
    main()
