#!/usr/bin/env -S uv run --script
# -----------------------------------------------------------------------------
# Trame Vuetify Menu Demo (Trame 3 / Vue 3)
#
# This example demonstrates a simple Vuetify 3 VMenu in a Trame 3 application.
# It shows how to create a menu with items that trigger a Python callback
# when clicked, all refactored into a modern class-based structure.
#
# Running if uv is available:
#   uv run ./01_menu.py
#   or ./01_menu.py
#
# Required Packages:
#   (Handled by the /// script block below if using uv run)
#   pip install "trame[app]" trame-vuetify
#
# To run as a Desktop Application:
#   python 01_menu.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('menu.py') is renamed and is in the same
#   directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from menu_app import MenuApp
#   app = MenuApp()
#   app.server.show()
#
# To run as a Web Application (default):
#   python 01_menu.py --server
# -----------------------------------------------------------------------------
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "trame-vuetify",
#     "trame[app]",
# ]
# ///

from trame.app import TrameApp
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3

# -----------------------------------------------------------------------------
# Trame Application
# -----------------------------------------------------------------------------

class MenuApp(TrameApp):
    def __init__(self, server_name=None, **kwargs):
        super().__init__(server_name, client_type="vue3", **kwargs)
        self._ui = None
        self._initialize_state()
        self._build_ui()

    def _initialize_state(self):
        self.state.menu_items = ["one", "two", "three"]
        self.state.trame__title = "Menu example"

    def print_item(self, item):
        print("Clicked on", item)

    def _build_ui(self):
        with SinglePageLayout(self.server, full_height=True) as self._ui:
            with self._ui.toolbar:
                vuetify3.VSpacer()
                with vuetify3.VMenu():
                    with vuetify3.Template(v_slot_activator="{ props }"):
                        with vuetify3.VBtn(icon=True, v_bind="props"):
                            vuetify3.VIcon("mdi-dots-vertical")
                    with vuetify3.VList():
                        with vuetify3.VListItem(
                            v_for="(item, i) in menu_items",
                            key="i",
                            value=["item"], # value should be bound to item for selection if needed
                            # For simple click, direct binding in VBtn is fine
                        ):
                            vuetify3.VBtn(
                                "{{ item }}",
                                click=(self.print_item, "[item]"),
                                block=True, # Makes the button take full width of VListItem
                                flat=True, # Removes button's own elevation/background for better list item appearance
                                # text=True, # Alternative to flat for a text-like button
                            )

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main(**kwargs):
    app = MenuApp()
    app.server.start(**kwargs)

if __name__ == "__main__":
    main()
