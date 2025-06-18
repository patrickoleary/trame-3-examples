#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
# ]
# ///

# # VTK Contour Geometry with Local/Remote Rendering
#
# This application demonstrates how to use both `VtkRemoteView` (server-side rendering)
# and `VtkLocalView` (client-side rendering) within the same Trame application,
# allowing the user to switch between them at runtime.
#
# **Key Features:**
# - **Dual Rendering Modes:** Toggle between server-side and client-side rendering.
# - **VTK Integration:** Uses a standard VTK pipeline (reader, contour filter).
# - **Interactive Controls:** 
#   - A slider adjusts the contour value.
#   - A checkbox toggles between interactive (live) updates and on-release updates.
#   - A "Reset View" button resets the contour value and camera.
# - **State-driven UI:** The UI reactively switches between views based on application state.
# - **Busy Indicator:** A progress bar shows when the server is busy.
#
# ---
#
# For a deeper understanding of the concepts demonstrated in this example, please refer to the
# [Trame tutorial](https://trame.readthedocs.io/en/latest/trame_tutorial.html).
#
# ---
#
# **Running if `uv` is available:**
# ```bash
# # Run the script directly:
# ./vtk/02_ContourGeometry/LocalViewRemoteViewRendering.py
#
# # Or with uv run:
# uv run ./vtk/02_ContourGeometry/LocalViewRemoteViewRendering.py
# ```
#
# **Required Packages:**
# `uv` will handle the dependencies specified in the script's header. If you don't have `uv`,
# you can install the required packages manually:
# ```bash
# pip install trame trame-vuetify trame-vtk
# ```
#
# **Run as a Desktop Application:**
# ```bash
# python ./vtk/02_ContourGeometry/LocalViewRemoteViewRendering.py --app
# ```
#
# **Run in Jupyter Lab / Notebook:**
#   Rename and make sure this script ('LocalViewRemoteViewRendering.py' to 'contour_app.py')
#   is in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from contour_app import ContourViewApp
#   app = ContourViewApp()
#   app.server.show()
#
# **Run as a Web Application (default):**
# ```bash
# python ./vtk/02_ContourGeometry/LocalViewRemoteViewRendering.py --server
# ```
#
# ---

# ---
#
# For a deeper understanding of the concepts demonstrated in this example, please refer to the
# [Trame tutorial](https://trame.readthedocs.io/en/latest/trame_tutorial.html).
#
# ---
#
# **Running if `uv` is available:**
# ```bash
# # Run the script directly:
# ./vtk/02_ContourGeometry/LocalViewRemoteViewRendering.py
#
# # Or with uv run:
# uv run ./vtk/02_ContourGeometry/LocalViewRemoteViewRendering.py
# ```
#
# **Required Packages:**
# `uv` will handle the dependencies specified in the script's header. If you don't have `uv`,
# you can install the required packages manually:
# ```bash
# pip install trame trame-vuetify trame-vtk
# ```
#
# **Run as a Desktop Application:**
# ```bash
# python ./vtk/02_ContourGeometry/LocalViewRemoteViewRendering.py --app
# ```
#
# **Run in Jupyter Lab / Notebook:**
# Rename this script to `contour_app.py` and place it in the same directory as your notebook.
# Then, in a cell, execute:
# ```python
# from contour_app import ContourViewApp
#
# app = ContourViewApp()
# app.server.show()
# ```
#
# **Run as a Web Application (default):**
# ```bash
# python ./vtk/02_ContourGeometry/LocalViewRemoteViewRendering.py --server
# ```
#
# ---

from pathlib import Path

import vtkmodules.vtkRenderingOpenGL2  # noqa
from vtkmodules.vtkFiltersCore import vtkContourFilter
from vtkmodules.vtkIOXML import vtkXMLImageDataReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch

from trame.app import TrameApp, get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, vtk
from trame.decorators import change

# -----------------------------------------------------------------------------
# Main Application Class
# -----------------------------------------------------------------------------

class ContourViewApp(TrameApp):
    """
    A Trame application demonstrating switchable local/remote VTK rendering.
    """

    def __init__(self, server=None):
        super().__init__(server=server, client_type="vue3")

        # VTK pipeline setup
        self._setup_vtk_pipeline()

        # Initialize state and UI
        self._initialize_state()
        self.default_contour_value = 50.0
        self._build_ui()

        # Set initial contour value and update views
        self._update_contour_and_render()

    def _setup_vtk_pipeline(self):
        """Creates and configures the VTK pipeline."""
        data_path = Path(__file__).parent.parent.parent / "data" / "head.vti"
        self.reader = vtkXMLImageDataReader()
        self.reader.SetFileName(data_path)
        self.reader.Update()

        self.contour = vtkContourFilter()
        self.contour.SetInputConnection(self.reader.GetOutputPort())
        self.contour.SetComputeNormals(1)

        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.contour.GetOutputPort())
        self.mapper.SetScalarRange(self.reader.GetOutput().GetScalarRange())

        self.actor = vtkActor()
        self.actor.SetMapper(self.mapper)

        self.renderer = vtkRenderer()
        self.renderer.AddActor(self.actor)
        self.renderer.ResetCamera()

        self.render_window = vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.render_window.SetOffScreenRendering(1)  # Essential for VtkRemoteView
        self.render_window_interactor = vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)
        # Set current style to TrackballCamera, assuming default interactor style is vtkInteractorStyleSwitch
        self.render_window_interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        

    def _initialize_state(self):
        """Initializes the application's reactive state."""
        self.state.trame__title = "VTK Local/Remote Contour"
        self.state.contour_value = 50.0
        self.state.view_mode = "Remote"  # Start with Remote view
        self.state.interactive_update = True # Default to interactive updates

    def _toggle_view_mode(self):
        if self.state.view_mode == "Local":
            self.state.view_mode = "Remote"
        else:
            self.state.view_mode = "Local"

    @change("view_mode")
    def _sync_view_on_mode_change(self, view_mode, **kwargs):
        """Ensures the newly activated view is updated when the mode changes."""
        if view_mode == "Remote":
            if hasattr(self.ctrl, 'remote_view_update') and self.ctrl.remote_view_update:
                self.ctrl.remote_view_update()
        elif view_mode == "Local":
            if hasattr(self.ctrl, 'local_view_update') and self.ctrl.local_view_update:
                self.ctrl.local_view_update()


    def _update_contour_and_render(self, new_value=None):
        """Updates the contour filter with the new value and triggers a render."""
        if new_value is not None:
            self.state.contour_value = new_value

        self.contour.SetValue(0, float(self.state.contour_value))
        self.contour.Update()
        self.render_window.Render()

        if self.state.view_mode == "Remote":
            if hasattr(self.ctrl, 'remote_view_update') and self.ctrl.remote_view_update:
                self.ctrl.remote_view_update()
        elif self.state.view_mode == "Local":
            if hasattr(self.ctrl, 'local_view_update') and self.ctrl.local_view_update:
                self.ctrl.local_view_update()

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
        """Resets the contour value to default and resets the active view's camera."""
        # Reset contour value to default by calling _update_contour_and_render with the default
        self._update_contour_and_render(new_value=self.default_contour_value)

        # Reset camera of the active view
        if self.state.view_mode == "Remote":
            if hasattr(self.ctrl, 'remote_view_reset_camera') and self.ctrl.remote_view_reset_camera:
                self.ctrl.remote_view_reset_camera()
        elif self.state.view_mode == "Local":
            if hasattr(self.ctrl, 'local_view_reset_camera') and self.ctrl.local_view_reset_camera:
                self.ctrl.local_view_reset_camera()

    def _build_ui(self):
        """Builds the user interface."""
        with SinglePageLayout(self.server) as layout:
            layout.title.set_text(self.state.trame__title)

            with layout.toolbar:
                vuetify3.VProgressLinear(
                    indeterminate=True,
                    absolute=True,
                    bottom=True,
                    active=("trame__busy",),
                    color="primary",
                )
                vuetify3.VSpacer()
                vuetify3.VCheckbox(
                    v_model=("interactive_update", self.state.interactive_update),
                    label="Interactive",
                    density="compact",
                    hide_details=True,
                    classes="mt-0 pt-0 ml-2 mr-2",
                )
                vuetify3.VSlider(
                    v_model=("contour_value", 50.0),
                    min=50,
                    max=200,
                    density="compact",
                    hide_details=True,
                    __events=['end'],
                    end=(self.commit_changes, "[$event]"),
                    style="max-width: 300px;",
                )
                vuetify3.VBtn(
                    text=("view_mode === 'Local' ? 'Local  View' : 'Remote View'",),
                    click=self._toggle_view_mode,
                    min_width=150, # Prevent button resize
                    density="compact",
                    variant="tonal",
                    classes="mr-2",
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
                    # Remote View (Server-side rendering)
                    with vtk.VtkRemoteView(
                        view=self.render_window,
                        v_if="view_mode === 'Remote'",
                    ) as remote_view_instance:
                        self.ctrl.remote_view_update = remote_view_instance.update
                        self.ctrl.remote_view_reset_camera = remote_view_instance.reset_camera

                    # Local View (Client-side rendering)
                    with vtk.VtkLocalView(
                        view=self.render_window,
                        v_if="view_mode === 'Local'",
                    ) as local_view_instance:
                        self.ctrl.local_view_update = local_view_instance.update
                        self.ctrl.local_view_reset_camera = local_view_instance.reset_camera


            layout.footer.hide()

        return layout

def main(server=None):
    """Instantiates and runs the application."""
    if server is None:
        server = get_server()
    if isinstance(server, str):
        server = get_server(server_name=server)

    app = ContourViewApp(server=server)
    app.server.start()
    return app


if __name__ == "__main__":
    main()
