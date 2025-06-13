#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
#     "vtk",
# ]
# ///
# -----------------------------------------------------------------------------
# Trame VTK Server-Side Rendering Cone
#
# This application demonstrates server-side VTK rendering with Trame.
# A cone's resolution is controlled by a slider, with the VTK pipeline
# running on the server and the resulting geometry pushed to the client.
#
# **Key Features:**
# - Server-side VTK pipeline (`vtkConeSource`).
# - Geometry representation (`vtk.VtkPolyData`) pushed to client.
# - Reactive state variable `resolution` controlling the cone's detail.
# - `VSlider` for user interaction to change the resolution.
# - `@change` decorator to react to state changes (`resolution`).
# - Standard Trame app structure with `TrameApp` subclass.
#
# Running if uv is available:
#   uv run ./01_SimpleCone/ClientView.py
#   or ./01_SimpleCone/ClientView.py
#
# Required Packages:
#   (Handled by the /// pyproject block above if using uv run)
#   pip install "trame[app]" trame-vuetify trame-vtk vtk
#
# Run as a Desktop Application:
#   python ./01_SimpleCone/ClientView.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('01_SimpleCone/ClientView.py' to 'client_view_app.py' or similar)
#   is in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from client_view_app import ClientViewApp
#   app = ClientViewApp()
#   app.server.show()
#
# Run as a Web Application (default):
#   python ./01_SimpleCone/ClientView.py --server
# ---

from vtkmodules.vtkFiltersSources import vtkConeSource

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk
from trame.widgets import vuetify3 as v3

DEFAULT_RESOLUTION = 6

# -----------------------------------------------------------------------------
# Application
# -----------------------------------------------------------------------------

class ClientViewApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server, client_type="vue3")
        self.cone_source = vtkConeSource()
        self._initialize_state()
        self._build_ui()
        self._on_resolution_change(resolution=self.state.resolution) # Initial cone update

    def _initialize_state(self):
        """Initialize reactive state variables."""
        self.state.trame__title = "VTK Server-Side Cone"
        self.state.resolution = DEFAULT_RESOLUTION

    @change("resolution")
    def _on_resolution_change(self, resolution, **kwargs):
        """Called when the 'resolution' state variable changes."""
        self.cone_source.SetResolution(int(resolution))
        if hasattr(self.ctrl, "mesh_update"):
            self.ctrl.mesh_update()

    def reset_resolution(self):
        """Resets the resolution to its default value."""
        self.state.resolution = DEFAULT_RESOLUTION

    def _build_ui(self):
        """Build the user interface."""
        with SinglePageLayout(self.server, full_height=True) as self.ui:
            self.ui.title.set_text("Cone Application (Server VTK)")

            with self.ui.toolbar:
                self.ui.toolbar.density = "compact"
                v3.VSpacer()
                v3.VSlider(
                    v_model=("resolution", self.state.resolution),
                    min=3,
                    max=60,
                    step=1,
                    density="compact",
                    hide_details=True,
                    style="max-width: 300px;",
                    thumb_label=True,
                )
                v3.VDivider(vertical=True, classes="mx-2")
                v3.VBtn(icon="mdi-undo", click=self.reset_resolution)
                v3.VBtn(icon="mdi-camera", click=self.ctrl.view_reset_camera) # Using mdi-camera for consistency

            with self.ui.content:
                with v3.VContainer(fluid=True, classes="fill-height pa-0 ma-0"):
                    with vtk.VtkView(ref="vtk_view") as view:
                        self.ctrl.view_reset_camera = view.reset_camera
                        with vtk.VtkGeometryRepresentation():
                            vtk_polydata = vtk.VtkPolyData(
                                "cone", dataset=self.cone_source
                            )
                            self.ctrl.mesh_update = vtk_polydata.update
            return self.ui

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main(server=None):
    """Instantiates and starts the Trame application."""
    app = ClientViewApp(server)
    app.server.start()
    return app

if __name__ == "__main__":
    main()