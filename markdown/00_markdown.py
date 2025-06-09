#!/usr/bin/env -S uv run --preview --python 3.11
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "trame[app]>=3.0.0b2",
#   "trame-vuetify>=3.0.0b1",
#   "trame-markdown>=3.0.0b0",
# ]
# ///

"""
Markdown Viewer Application

This application demonstrates how to display markdown content dynamically 
using Trame 3 and Vue 3.

It allows selecting different markdown files from a dropdown and renders them.

# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('00_markdown.py' to 'markdown_viewer.py')
#   is in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from markdown_viewer import MarkdownViewerApp
#   app = MarkdownViewerApp()
#   app.server.show()
"""

import os
from pathlib import Path

from trame.app import TrameApp, get_server
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, markdown

# -----------------------------------------------------------------------------
# Application Class
# -----------------------------------------------------------------------------

class MarkdownViewerApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(
            server if server else get_server(client_type="vue3"),
            name="MarkdownViewer"
        )
        self._initialize_state()
        self._build_ui()
        self.update_markdown_content() # Initial content load

    def _initialize_state(self):
        self.state.file_name = "demo.md"
        self.state.file_options = ["demo.md", "sample.md", "module.md"]
        self.state.md_content = "" # Initialize with empty string or placeholder
        self.state.trame__title = "Markdown Viewer (Trame 3)"

    @change("file_name")
    def update_markdown_content(self, file_name=None, **kwargs):
        if file_name is None:
            file_name = self.state.file_name
        
        current_script_path = Path(__file__).parent.resolve()
        md_file_path = current_script_path / file_name

        if md_file_path.exists() and md_file_path.is_file():
            with open(md_file_path, encoding="utf-8") as f:
                self.ctrl.md_update(f.read())
        else:
            self.ctrl.md_update(f"# Error\nCould not find or read '{file_name}' at '{md_file_path}'.")

    def _build_ui(self):
        with SinglePageLayout(self.server) as layout:
            layout.title.set_text("Markdown Viewer")

            with layout.toolbar:
                vuetify3.VSpacer()
                vuetify3.VSelect(
                    v_model=("file_name", self.state.file_name),
                    items=("file_options", self.state.file_options), 
                    hide_details=True,
                    density="compact",
                    style="max-width: 200px;",
                )

            with layout.content:
                md = markdown.Markdown(classes="pa-4 mx-2")
                self.ctrl.md_update = md.update


# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main():
    app = MarkdownViewerApp()
    app.server.start()

if __name__ == "__main__":
    main()
