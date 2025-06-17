#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
#     "vtk",
#     "numpy", # Often useful with VTK data ranges
# ]
# ///

# # VTK Head Contour with Remote Rendering
#
# This application loads a VTI medical image (a human head scan), allows the user
# to define an isovalue using a slider, and then renders the resulting contour
# (isosurface) using server-side VTK rendering displayed via `VtkRemoteView`.
#
# **Key Features:**
#
# - **VTK Pipeline**: Loads `head.vti`, applies `vtkContourFilter`.
# - **Remote Rendering**: Uses `VtkRemoteView` for displaying the VTK scene.
# - **Interactive Isovalue**: `VSlider` controls the contour's isovalue.
# - **Data-driven Slider**: Slider range is determined by the scalar range of the input data.
# - **Modern Trame Structure**: Class-based application inheriting from `trame.app.TrameApp`.
# - **Custom Event Handling**: Demonstrates using the `__events` attribute to expose and handle non-default UI events (e.g., `end` on `VSlider`).

# --- Usage Instructions ---
#
# This script is designed to be run with `uv` or standard Python.
# The `head.vti` data file is expected to be in a `../data/` directory relative to this script.
#
# **Running if `uv` is available (recommended):**
#   `uv` will automatically create a virtual environment and install dependencies.
#   1. Make the script executable: `chmod +x ./RemoteViewRendering.py` (if not already)
#   2. Run directly: `./RemoteViewRendering.py`
#   Alternatively: `uv run ./RemoteViewRendering.py`
#
# **Required Packages (if not using `uv`):**
#   `uv` handles dependencies automatically. If not using `uv`, install packages from `dependencies`:
#   `pip install trame trame-vuetify trame-vtk vtk numpy`
#
# **Run as a Desktop Application:**
#   `python ./RemoteViewRendering.py --app`
#
# **Run in Jupyter Lab / Notebook:**
#   Rename this script (e.g., `02_ContourGeometry/RemoteViewRendering.py` to `contour_remote_app.py`)
#   and ensure it's in the same directory as your notebook or in Python's path.
#   Then, in a cell, execute:
#
#   from contour_remote_app import ContourRemoteApp
#   app = ContourRemoteApp()
#   app.server.show()
#
# **Run as a Web Application (default):**
#   `python ./RemoteViewRendering.py --server`
#   Then open your browser to `http://localhost:8080` (or the port shown in the console).
#
# --- End Usage Instructions ---

from pathlib import Path
import vtk
import numpy as np # For numerical operations if needed, e.g. data_range step

from trame.app import get_server, TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, vtk as vtk_widgets

# -----------------------------------------------------------------------------
# VTK pipeline setup
# -----------------------------------------------------------------------------

def create_vtk_pipeline():
    """Creates and configures the VTK pipeline for contouring head.vti."""
    data_directory = Path(__file__).resolve().parent.parent.parent / "data"
    head_vti_path = data_directory / "head.vti"

    if not head_vti_path.exists():
        raise FileNotFoundError(
            f"Expected data file not found: {head_vti_path}\n"
            f"Please ensure 'head.vti' is in a 'data' directory relative to the 'examples' directory."
        )

    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(str(head_vti_path))
    reader.Update()

    contour_filter = vtk.vtkContourFilter()
    contour_filter.SetInputConnection(reader.GetOutputPort())
    contour_filter.SetComputeNormals(1)
    contour_filter.SetComputeScalars(0) # We'll use the actor's color

    scalar_range = reader.GetOutput().GetPointData().GetScalars().GetRange()
    initial_contour_value = 0.5 * (scalar_range[0] + scalar_range[1])
    contour_filter.SetNumberOfContours(1) # Ensure this is set
    contour_filter.SetValue(0, initial_contour_value)
    contour_filter.Update()

    return {
        "reader": reader,
        "contour_filter": contour_filter,
        "scalar_range": scalar_range,
        "initial_contour_value": initial_contour_value,
    }

# -----------------------------------------------------------------------------
# Trame Application
# -----------------------------------------------------------------------------

class ContourRemoteApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server, client_type="vue3")

        # VTK Pipeline components
        vtk_parts = create_vtk_pipeline()
        self.reader = vtk_parts["reader"]
        self.contour_filter = vtk_parts["contour_filter"]
        self._scalar_range = vtk_parts["scalar_range"]
        self._initial_contour_value = vtk_parts["initial_contour_value"]

        # VTK Rendering components
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.render_window.SetOffScreenRendering(1)
        self.renderer.SetBackground(0.9, 0.9, 0.9) # Light gray background

        self.mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()
        self.mapper.SetInputConnection(self.contour_filter.GetOutputPort())
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetColor(0.2, 0.6, 0.9) # A pleasant blue
        self.renderer.AddActor(self.actor)
        self.renderer.ResetCamera()

        # Setup for VtkRemoteView
        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)
        self.render_window_interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        self.render_window_interactor.EnableRenderOff() # Crucial for remote rendering
        self.render_window_interactor.Initialize()

        # Initialize Trame state
        self._initialize_state()
        # Build UI
        self._build_ui()
        # Initial update of contour and view
        self._update_contour_and_render()

    def _initialize_state(self):
        """Initializes reactive state variables."""
        self.state.trame__title = "VTK Head Contour (Remote)"
        self.state.contour_value = self._initial_contour_value
        self.state.interactive_update = True
        self.state.slider_min = self._scalar_range[0]
        self.state.slider_max = self._scalar_range[1]
        # Calculate a reasonable step, e.g., 1/100th of the range
        self.state.slider_step = (self._scalar_range[1] - self._scalar_range[0]) / 100.0

    def _update_contour_and_render(self, new_value=None):
        """Updates the contour filter with the new value and triggers a render."""
        if new_value is None:
            new_value = self.state.contour_value
        else:
            self.state.contour_value = new_value # Ensure state reflects the value being set

        self.contour_filter.SetValue(0, float(new_value))
        self.contour_filter.Update()
        if hasattr(self.ctrl, 'view_update') and self.ctrl.view_update: # Check if view_update is bound by VtkRemoteView
            self.ctrl.view_update()

    @change("contour_value")
    def _on_contour_value_change_interactive(self, contour_value, **kwargs):
        """Called when 'contour_value' state changes, for interactive updates."""
        if self.state.interactive_update:
            self._update_contour_and_render(contour_value)

    def commit_changes(self, value):
        """
        Called on VSlider 'end' event. This is used for non-interactive updates
        to ensure the final value is applied when the user releases the slider.
        """
        if not self.state.interactive_update:
            self._update_contour_and_render(value)

    def reset_contour_and_camera(self):
        """Resets contour to initial value and resets camera."""
        self.state.contour_value = self._initial_contour_value # Reset state first
        self._update_contour_and_render() # Render with reset state value
        if hasattr(self.ctrl, 'view_reset_camera') and self.ctrl.view_reset_camera:
            self.ctrl.view_reset_camera()

    def _build_ui(self):
        """Builds the user interface for the application."""
        with SinglePageLayout(self.server, full_height=True) as layout:
            layout.title.set_text(self.state.trame__title)

            with layout.toolbar:
                vuetify3.VSpacer()
                vuetify3.VSlider(
                    v_model=("contour_value", self.state.contour_value),
                    min=("slider_min", self.state.slider_min),
                    max=("slider_max", self.state.slider_max),
                    step=("slider_step", self.state.slider_step),
                    label="Isovalue",
                    classes="mt-0 pt-0 ml-2 mr-2",
                    style="max-width: 350px; min-width: 200px;",
                    density="compact",
                    hide_details=True,
                    thumb_label=True,
                    # The 'end' event is not exposed by default in trame-vuetify's VSlider.
                    # We can dynamically expose it using the `__events` private attribute.
                    # This allows us to capture the slider's value when the user releases the mouse.
                    __events=["end"],
                    # When the 'end' event fires, call `commit_changes` with the event's payload ($event),
                    # which is the final slider value. This is used for non-interactive updates.
                    end=(self.commit_changes, "[$event]"),
                )
                vuetify3.VCheckbox(
                    v_model=("interactive_update", self.state.interactive_update),
                    label="Interactive",
                    density="compact",
                    hide_details=True,
                    classes="mt-0 pt-0 ml-2 mr-2",
                )
                vuetify3.VBtn(
                    "Reset View",
                    click=self.reset_contour_and_camera,
                    density="compact",
                    classes="ml-2",
                    variant="tonal",
                )

            with layout.content:
                with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
                    # view = vtk_widgets.VtkLocalView(
                    view = vtk_widgets.VtkRemoteView(
                        self.render_window,
                        ref="view",
                    )
                    self.ctrl.view_update = view.update
                    self.ctrl.view_reset_camera = view.reset_camera

            # Initial update calls after UI is built and server is ready
            self.ctrl.on_server_ready.add(self.ctrl.view_update)
            self.ctrl.on_server_ready.add(self.ctrl.view_reset_camera)

        return layout

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main(server=None):
    """Instantiates and starts the Trame application."""
    if server is None:
        server = get_server()
    if isinstance(server, str):
        server = get_server(server_name=server)

    app = ContourRemoteApp(server=server)
    app.server.start()
    return app

if __name__ == "__main__":
    main()
