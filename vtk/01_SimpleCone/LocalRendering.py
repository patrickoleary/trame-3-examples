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
# Trame VTK Client-Side Rendering Cone (Local Rendering)
#
# This application demonstrates client-side VTK rendering with Trame,
# utilizing the VtkLocalView component. The entire VTK pipeline, including
# the render window, is managed in Python on the server, and the
# VtkLocalView component renders this scene directly in the browser.
#
# **Key Features:**
# - Client-side VTK rendering using `trame.widgets.vtk.VtkLocalView`.
# - Full VTK pipeline (`vtkConeSource`, `vtkRenderWindow`, etc.) managed in Python.
# - The `vtkRenderWindow` instance is passed to `VtkLocalView`.
# - Reactive state variable `resolution` controlling the cone's detail.
# - `VSlider` for user interaction to change the resolution.
# - `@change` decorator to react to state changes (`resolution`).
# - Standard Trame app structure with `TrameApp` subclass for Vue 3.
#
# Running if uv is available:
#   uv run ./vtk/01_SimpleCone/LocalRendering.py
#   or ./vtk/01_SimpleCone/LocalRendering.py
#
# Required Packages:
#   (Handled by the /// pyproject block above if using uv run)
#   pip install "trame[app]" trame-vuetify trame-vtk vtk
#
# Run as a Desktop Application:
#   python ./vtk/01_SimpleCone/LocalRendering.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('vtk/01_SimpleCone/LocalRendering.py' to 'local_rendering_app.py' or similar)
#   is in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from local_rendering_app import LocalRenderingApp
#   app = LocalRenderingApp()
#   app.server.show()
#
# Run as a Web Application (default):
#   python ./vtk/01_SimpleCone/LocalRendering.py --server
# ---

from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
)

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk as vtk_widgets
from trame.widgets import vuetify3 as v3

DEFAULT_RESOLUTION = 6

# -----------------------------------------------------------------------------
# Application
# -----------------------------------------------------------------------------

class LocalRenderingApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server, client_type="vue3")

        # VTK pipeline setup
        self.cone_source = vtkConeSource()
        self.mapper = vtkPolyDataMapper()
        self.actor = vtkActor()
        self.renderer = vtkRenderer()
        self.render_window = vtkRenderWindow()

        self.mapper.SetInputConnection(self.cone_source.GetOutputPort())
        self.actor.SetMapper(self.mapper)
        self.renderer.AddActor(self.actor)
        self.render_window.AddRenderer(self.renderer)

        # Set interactor style for the render window
        # VtkLocalView will use the interactor from this render_window
        style = vtkInteractorStyleSwitch()
        style.SetCurrentStyleToTrackballCamera()
        # VtkLocalView manages its own interactor, so we don't set one on the render_window directly.
        # However, we can configure the style it *would* use if it had one, or rely on VtkLocalView's defaults.
        # For this example, ensuring TrackballCamera is preferred.
        # self.render_window.GetInteractor().SetInteractorStyle(style) # This line might be optional or handled by VtkLocalView

        self.renderer.ResetCamera()
        self.render_window.Render()  # Initial render

        # Initialize Trame state and UI
        self._initialize_state()
        self._build_ui()
        # Set initial cone resolution and trigger view update
        self._on_resolution_change(resolution=self.state.resolution)

    def _initialize_state(self):
        """Initialize reactive state variables."""
        self.state.trame__title = "VTK Client-Side Cone (Local Rendering)"
        self.state.resolution = DEFAULT_RESOLUTION

    @change("resolution")
    def _on_resolution_change(self, resolution, **kwargs):
        """Called when the 'resolution' state variable changes."""
        self.cone_source.SetResolution(int(resolution))
        if hasattr(self.ctrl, "view_update"):
            self.ctrl.view_update() # This will call VtkLocalView.update()

    def reset_resolution(self):
        """Resets the resolution to its default value."""
        self.state.resolution = DEFAULT_RESOLUTION

    def _build_ui(self):
        """Build the user interface."""
        with SinglePageLayout(self.server, full_height=True) as self.ui:
            self.ui.title.set_text("Cone Application (Local VTK)")

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
                v3.VBtn(icon="mdi-camera", click=self.ctrl.view_reset_camera) # Bound to VtkLocalView.reset_camera

            with self.ui.content:
                with v3.VContainer(fluid=True, classes="fill-height pa-0 ma-0"):
                    # VtkLocalView takes the vtkRenderWindow instance
                    view = vtk_widgets.VtkLocalView(self.render_window, ref="view")
                    self.ctrl.view_update = view.update
                    self.ctrl.view_reset_camera = view.reset_camera
            return self.ui

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main(server=None):
    """Instantiates and starts the Trame application."""
    app = LocalRenderingApp(server)
    app.server.start()
    return app

if __name__ == "__main__":
    main()
