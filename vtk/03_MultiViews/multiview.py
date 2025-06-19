#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame>=3.0.0b1",
#     "trame-vuetify>=3.0.0b1",
#     "trame-vtk>=3.0.0b1",
#     "vtk",
# ]
# ///

# # VTK Multi-View Application
#
# This application demonstrates how to display multiple synchronized views of the
# same VTK scene. Each view has a different background color, and all views
# share the same cone geometry. The resolution of the cone can be controlled
# globally.

# **Key Features:**
# - Multiple synchronized VTK views.
# - Shared VTK geometry (a cone).
# - Independent camera controls for each view by default.
# - Global control for cone resolution.
# - Distinct background color for each view.
# - UI built with Trame 3 and Vuetify 3.

# **Running if uv is available:**
# ```bash
# # Run directly
# uv run ./multiview.py
#
# # Or, if you've made the script executable
# ./multiview.py
# ```

# **Required Packages:**
# `uv` will automatically create a virtual environment and install the
# dependencies listed at the top of this script.
# If you don't have `uv`, you can install the packages manually:
# ```bash
# pip install trame trame-vuetify trame-vtk vtk
# ```

# **Run as a Desktop Application:**
# ```bash
# python ./multiview.py --app
# ```

# **Run in Jupyter Lab / Notebook:**
#   Rename and make sure this script ('multiview.py' to 'multi_view_app.py')
#   is in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from multi_view_app import MultiViewApp
#   app = MultiViewApp()
#   app.server.show()

# **Run as a Web Application (default):**
# ```bash
# python ./multiview.py --server
# ```
# ---

import vtkmodules.vtkRenderingOpenGL2  # noqa
from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3 as vuetify, vtk as vtk_widgets

DEFAULT_RESOLUTION = 6
NB_COLS = 4
PALETTE = [
    (0.5, 0, 0), (0, 0.5, 0), (0, 0, 0.5),
    (0.5, 0, 0.5), (0.5, 0.5, 0), (0, 0.5, 0.5),
]

class MultiViewApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server, client_type="vue3")
        self._initialize_vtk()
        self._initialize_state()
        self._build_ui()
        self._on_resolution_change() # Set initial resolution and update views

    def _initialize_vtk(self):
        self.cone_source = vtkConeSource()
        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.cone_source.GetOutputPort())

        self.colors = PALETTE + PALETTE  # 12 views
        self.render_windows = []
        self._html_views = [] # Store view widgets if needed for later reference

        # Build VTK render windows and associated components
        for color in self.colors:
            actor = vtkActor()
            actor.SetMapper(self.mapper)

            renderer = vtkRenderer()
            renderer.SetBackground(*color)
            render_window = vtkRenderWindow()
            render_window.AddRenderer(renderer)
            render_window.SetOffScreenRendering(1)

            # Setup interactor
            render_window_interactor = vtkRenderWindowInteractor()
            render_window_interactor.SetRenderWindow(render_window)
            # The following line ensures that the interactor style is a vtkInteractorStyleSwitch
            # which then allows setting specific styles like TrackballCamera.
            render_window_interactor.Initialize() # Initialize is important
            if render_window_interactor.GetInteractorStyle():
                 render_window_interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

            renderer.AddActor(actor)
            renderer.ResetCamera()
            # render_window.Render() # Initial render can be deferred or handled by view updates

            self.render_windows.append(render_window)

    def _initialize_state(self):
        self.state.trame__title = "VTK Multi-View Application"
        self.state.resolution = DEFAULT_RESOLUTION

    @change("resolution")
    def _on_resolution_change(self, resolution=None, **kwargs):
        if resolution is None:
            resolution = self.state.resolution
        self.cone_source.SetResolution(int(resolution))
        self.ctrl.update_views()

    def _reset_resolution(self):
        self.state.resolution = DEFAULT_RESOLUTION
        # The @change decorator on resolution will trigger _on_resolution_change

    def _build_ui(self):
        with SinglePageLayout(self.server, full_height=True) as layout:
            layout.title.set_text("Multi-View Cone")
            layout.icon.click = self.ctrl.reset_camera # Reset all views' cameras

            with layout.toolbar:
                vuetify.VSpacer()
                vuetify.VSlider(
                    v_model=("resolution", self.state.resolution),
                    min=3,
                    max=60,
                    step=1,
                    hide_details=True,
                    density="compact", # Vuetify 3 uses density
                    style="max-width: 300px",
                    thumb_label=True,
                )
                vuetify.VDivider(vertical=True, classes="mx-2")
                with vuetify.VBtn(icon=True, click=self._reset_resolution):
                    vuetify.VIcon("mdi-undo-variant")

            with layout.content:
                with vuetify.VContainer(fluid=True, classes="pa-0 bg-surface-variant fill-height"):
                    num_render_windows = len(self.render_windows)
                    if num_render_windows == 0:
                        return # Or display a message

                    num_rows = int(num_render_windows / NB_COLS)
                    row_height_percent = 90.0 / num_rows if num_rows > 0 else 90.0

                    for row_idx in range(num_rows):
                        with vuetify.VRow(
                            classes="pa-1 ma-1",
                            style=f"height: {row_height_percent}%; width:100%;", # flex-shrink:0 is important
                        ):
                            for col_idx in range(NB_COLS):
                                view_idx = row_idx * NB_COLS + col_idx
                                if view_idx < num_render_windows:
                                    render_window = self.render_windows[view_idx]
                                    with vuetify.VCol(
                                        classes="pa-1 ma-1",
                                    ):
                                        view = vtk_widgets.VtkRemoteView(
                                            render_window,
                                            ref=f"view{view_idx}",
                                        )
                                        self.ctrl.update_views.add(view.update)
                                        self.ctrl.reset_camera.add(view.reset_camera)
                                        self._html_views.append(view)



def main():
    app = MultiViewApp()
    app.server.start()

if __name__ == "__main__":
    main()