"""
Inspired by: https://github.com/pdoc3/pdoc/issues/101#issuecomment-1645289507

Program to generate `Docs` using `pdoc3` with a central `index.html`
"""

import inspect
import os
from pathlib import Path

from pdoc import _render_template, import_module


def generate_docs_and_central_index(modules_to_process: list[str], doc_output_dir: Path) -> None:
    """Method to generate a doc folder with central `index.html`

    :param modules_to_process: List of modules to process
    :param doc_output_dir: Path to store the generated docs
    """

    modules = [import_module(module, reload=True) for module in modules_to_process]

    # Generate the docs for each module under docs folder
    command = f'pdoc --html --skip-errors --force --output-dir {doc_output_dir.name} {" ".join(modules_to_process)}'
    os.system(command=command)

    # Create a single base `index.html`
    with open(Path(doc_output_dir, "index.html"), "w", encoding="utf-8") as index:
        index.write(_render_template("/html.mako",
                                     modules=sorted((module.__name__, inspect.getdoc(module)) for module in modules)))


if __name__ == "__main__":
    module_list = ["core"]
    doc_path = Path("docs")
    generate_docs_and_central_index(module_list, doc_path)
