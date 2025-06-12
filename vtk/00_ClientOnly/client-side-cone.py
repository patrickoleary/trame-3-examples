#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
# ]
# ///
# -----------------------------------------------------------------------------
# # VTK Client-Side Rendering
#
# This example demonstrates a client-only rendering scenario using `trame`.
# The application displays a VTK cone source, and its resolution can be
# interactively adjusted by the user. All rendering and interaction logic
# runs directly in the web browser.
#
# **Key Features:**
# - Pure client-side rendering with `trame-vtk`.
# - Interactive control of a VTK object property (cone resolution) via a slider.
# - Class-based application structure using `trame.app.TrameApp`.
# - Modern Trame 3 / Vuetify 3 UI.
#
# ---
#
# For a better understanding of the concepts used in this example, please refer to:
#
# - **Trame Tutorial**: https://kitware.github.io/trame/docs/tutorial.html
# - **VTK Integration**: https://kitware.github.io/trame/docs/programming/vtk.html
#
# ---
#
# **Running if uv is available:**
# `uv run ./vtk/00_ClientOnly/client-side-cone.py`
# or
# `./vtk/00_ClientOnly/client-side-cone.py`
#
# **Required Packages:**
# `uv` will handle the dependencies specified in the script header.
# Alternatively, you can install them manually:
# `pip install trame trame-vuetify trame-vtk`
#
# **Run as a Desktop Application:**
# `python ./vtk/00_ClientOnly/client-side-cone.py --app`
#
# **Run in Jupyter Lab / Notebook:**
#   Rename and make sure this script ('client-side-cone.py') is renamed to 'client_side_cone.py'
#   and is in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from client_side_cone import ClientConeApp
#   app = ClientConeApp()
#   app.server.show()
#
# **Run as a Web Application (default):**
# `python ./vtk/00_ClientOnly/client-side-cone.py --server`
#
# ---

from trame.app import TrameApp
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk as vtk_widgets
from trame.widgets import vuetify3 as v
from trame.decorators import change


class ClientConeApp(TrameApp):
    """
    A Trame application for client-side VTK cone rendering.
    """

    def __init__(self, server=None):
        super().__init__(server=server, client_type="vue3")
        self._initialize_state()
        self._build_ui()

    def _initialize_state(self):
        """Initialize the reactive state."""
        self.state.resolution = 6
        self.state.trame__title = "VTK Client-Side Rendering"
        self.state.theme_mode = "light"

    @change("resolution")
    def _on_resolution_change(self, resolution, **kwargs):
        """Called when the 'resolution' state variable changes."""
        # For client-only rendering, the change to `state.resolution`
        # is automatically picked up by the VtkAlgorithm's `state` binding.

    def _build_ui(self):
        """Build the user interface."""
        with SinglePageLayout(self.server, full_height=True, theme=("theme_mode", "light")) as self.ui:
            self.ui.title.set_text(self.state.trame__title)

            with self.ui.toolbar:
                v.VSpacer()
                v.VSlider(
                    v_model=("resolution", self.state.resolution),
                    min=3,
                    max=60,
                    step=1,
                    hide_details=True,
                    thumb_label=True,
                    style="max-width: 300px;",
                    classes="my-auto",
                )
                v.VBtn(icon="mdi-crop-free", click=self.ctrl.reset_camera)

                with v.VBtn(
                    icon=True,
                    click="theme_mode = theme_mode == 'light' ? 'dark' : 'light'",
                ):
                    v.VIcon("mdi-theme-light-dark")

            with self.ui.content:
                with v.VContainer(fluid=True, classes="pa-0 fill-height"):
                    with vtk_widgets.VtkView(ref="view") as view:
                        self.ctrl.reset_camera = view.reset_camera
                        with vtk_widgets.VtkGeometryRepresentation():
                            vtk_widgets.VtkAlgorithm(
                                vtk_class="vtkConeSource",
                                state=('{ resolution }',),  # Reactive binding to client-side state
                            )


if __name__ == "__main__":
    app = ClientConeApp()
    app.server.start()
