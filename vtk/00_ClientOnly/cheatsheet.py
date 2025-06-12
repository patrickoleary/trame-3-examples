#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
# ]
# ///

# # Trame VTK Client-Only Rendering Cheatsheet
#
# This application demonstrates client-only rendering with VTK.js in Trame.
# It features a cone whose resolution can be dynamically updated using a slider.
#
# **Key Features:**
# - Client-side rendering using `vtk.VtkView`, `VtkGeometryRepresentation`, and `VtkAlgorithm`.
# - Reactive state variable `resolution` controlling the cone's detail.
# - `VSlider` for user interaction to change the resolution.
# - `@change` decorator to react to state changes (`resolution`).
# - Standard Trame app structure with `TrameApp` subclass.
#
# Running if uv is available:
#   uv run ./cheatsheet.py
#   or ./cheatsheet.py
#
# Required Packages:
#   (Handled by the /// pyproject block above if using uv run)
#   pip install "trame[app]" trame-vuetify trame-vtk
#
# Run as a Desktop Application:
#   python cheatsheet.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('cheatsheet.py' to 'vtk_cone_app.py' or similar)
#   is in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from vtk_cone_app import ConeApp
#   app = ConeApp()
#   app.server.show()
#
# Run as a Web Application (default):
#   python cheatsheet.py --server
# ---

from trame.app import TrameApp
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3 as v3, vtk
from trame.decorators import change


class ConeApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server, client_type="vue3")
        self._initialize_state()
        self._build_ui()

    def _initialize_state(self):
        """Initialize reactive state variables."""
        self.state.resolution = 6

    @change("resolution")
    def _on_resolution_change(self, resolution, **kwargs):
        """Called when the 'resolution' state variable changes."""
        # For client-only rendering, the change to `state.resolution`
        # is automatically picked up by the VtkAlgorithm's `state` binding.

    def reset_resolution(self):
        """Resets the resolution to its default value."""
        self.state.resolution = 6

    def _build_ui(self):
        """Build the user interface."""
        with SinglePageLayout(self.server, full_height=True) as self.ui:
            self.ui.title.set_text("VTK Client-Only Cone")

            with self.ui.toolbar:
                self.ui.toolbar.density = "compact"
                v3.VSpacer()
                v3.VSlider(
                    v_model=("resolution", self.state.resolution), # Bind to state, use initial value
                    min=3,
                    max=60,
                    step=1,
                    density="compact",
                    hide_details=True,
                    style="max-width: 300px;",
                    thumb_label=True,
                )
                v3.VBtn(icon="mdi-undo", click=self.reset_resolution)
                v3.VBtn(icon="mdi-crop-free", click=self.ctrl.reset_camera)

            with self.ui.content:
                with v3.VContainer(fluid=True, classes="fill-height pa-0 ma-0"):
                    with vtk.VtkView(ref="vtk_view") as view:
                        self.ctrl.reset_camera = view.reset_camera
                        with vtk.VtkGeometryRepresentation():
                            vtk.VtkAlgorithm(
                                vtk_class="vtkConeSource",
                                state=('{ resolution }',),  # Reactive binding to client-side state
                            )
        return self.ui


def main(server=None):
    """Instantiates and starts the Trame application."""
    app = ConeApp(server)
    app.server.start()
    return app


if __name__ == "__main__":
    main()
