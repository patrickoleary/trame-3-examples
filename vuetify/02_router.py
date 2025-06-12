#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame[app]",
#     "trame-vuetify",
#     "trame-router",
# ]
# ///
# -----------------------------------------------------------------------------
# Trame Router Demo (Trame 3 / Vue 3)
#
# This example demonstrates multi-page navigation using trame-router
# with Vuetify 3 components in a Trame 3 application. It features a navigation
# drawer and dynamically generated routes.
#
# Running if uv is available:
#   uv run ./02_router.py
#   or ./02_router.py
#
# Required Packages:
#   (Handled by the script block above if using uv run)
#   pip install "trame[app]" trame-vuetify trame-router
#
# To run as a Desktop Application:
#   python 02_router.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('02_router.py' to 'router_app.py') is renamed and in the same
#   directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from router_app import RouterApp
#   app = RouterApp()
#   app.server.show()
#
# To run as a Web Application (default):
#   python 02_router.py --server
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

from trame.app import TrameApp
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame_router.ui.router import RouterViewLayout
from trame.widgets import router, vuetify3

# -----------------------------------------------------------------------------
# Trame Application
# -----------------------------------------------------------------------------

class RouterApp(TrameApp):
    def __init__(self, server_name=None, **kwargs):
        super().__init__(server_name, client_type="vue3", **kwargs)
        self._ui = None
        self._initialize_state()
        self._build_ui()

    def _initialize_state(self):
        self.state.selected_route = "/"  # For VList v-model
        self.state.open_drawer_groups = ["bars_group"]  # Keep "Bars" group open
        # Data for client-side v-for loop for Bar items
        self.state.bar_route_params = [{"id_val": 1}, {"id_val": 2}, {"id_val": 3}]

    # --- Route UI builders ---


    def add_route(self, path, ui):
        with RouterViewLayout(self.server, path):
            ui()

    def _ui_home(self):
        with vuetify3.VCard() as card:
            vuetify3.VCardTitle("This is home (Vue 3)")
        return card

    def _ui_foo(self):
        with vuetify3.VCard() as card:
            vuetify3.VCardTitle("This is foo (Vue 3)")
            with vuetify3.VCardText():
                vuetify3.VBtn("Take me back", click="$router.back()")
        return card

    def _ui_bar_id(self):
        # $route.params.id is automatically available in Vue templates
        with vuetify3.VCard() as card:
            vuetify3.VCardTitle("This is bar with ID '{{ $route.params.id }}' (Vue 3)")
        return card

    # --- Main UI construction ---

    def _build_ui(self):
        self.add_route("/", self._ui_home)
        self.add_route("/foo", self._ui_foo)
        self.add_route("/bar/:id", self._ui_bar_id)

        with SinglePageWithDrawerLayout(self.server, full_height=True) as self._ui:
            self._ui.title.set_text("Multi-Page demo (Vue 3)")

            # Main content area where router views will be displayed
            with self._ui.content:
                with vuetify3.VContainer(): # Removed fluid=True to match original appearance
                    router.RouterView()

            # Navigation drawer
            with self._ui.drawer:
                with vuetify3.VList(
                    nav=True,
                    dense=True,
                    v_model="selected_route",
                    opened=("open_drawer_groups",), # Bind to state for open groups
                ):
                    vuetify3.VListSubheader("Routes")

                    vuetify3.VListItem(
                        to="/",
                        value="/", # For v-model
                        title="Home",
                        prepend_icon="mdi-home",
                    )

                    vuetify3.VListItem(
                        to="/foo",
                        value="/foo",
                        title="Foo",
                        prepend_icon="mdi-food",
                    )

                    # Group for "Bar" routes
                    with vuetify3.VListGroup(value="bars_group"): # `value` identifies the group
                        with vuetify3.Template(v_slot_activator="{ props }"):
                            # This VListItem activates the group
                            vuetify3.VListItem(
                                v_bind="props", # Spread props from slot
                                title="Bars",
                                prepend_icon="mdi-label-multiple-outline", # Icon for the group
                            )
                        
                        # Dynamically create list items for each bar_id using v-for
                        vuetify3.VListItem(
                           v_for="item_spec in bar_route_params",
                           key=("item_spec.id_val",), # Unique key for each item
                           # Use JS template literals for dynamic `to` and `value`
                           to=("`/bar/${item_spec.id_val}`",),
                           value=("`/bar/${item_spec.id_val}`",),
                           title="Bar", # Static part of the title
                           # Dynamic subtitle using JS template literal
                           subtitle=("`ID '${item_spec.id_val}'`",),
                           prepend_icon="mdi-peanut-outline",
                        )
        return self._ui

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main(**kwargs):
    app = RouterApp(**kwargs)
    app.server.start()

if __name__ == "__main__":
    main()
