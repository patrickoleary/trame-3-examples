#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
# ]
# ///

# # VTK Contour with Remote/Local Rendering
#
# This application demonstrates how to use the `VtkRemoteLocalView` component
# to seamlessly switch between remote and local rendering of a VTK pipeline.
# The user can adjust a contour value with a slider and choose the rendering mode.
#
# **Key Features:**
# - **VTK Integration**: Visualizes a contour from a `vtkXMLImageDataReader`.
# - **Remote/Local Rendering**: Uses `VtkRemoteLocalView` to allow the user to
#   switch between server-side (remote) and client-side (local) rendering.
# - **Reactive UI**: A slider controls the `contour_value` which updates the
#   VTK pipeline and the view in real-time.

# ## Running if uv is available:
#
# ```
# uv run ./RemoteLocalViewRendering.py
# ./RemoteLocalViewRendering.py
# ```
#
# ## Required Packages:
#
# `uv` will automatically create a virtual environment and install the packages
# listed in the script header. To install manually, use:
# `pip install trame trame-vuetify trame-vtk`
#
# ## Run as a Desktop Application:
#
# ```
# python ./RemoteLocalViewRendering.py --app
# ```
#
# ## Run in Jupyter Lab / Notebook:
#
#   Rename and make sure this script ('RemoteLocalViewRendering.py' to 'remotelocalviewrendering.py') is renamed and in the same
#   directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from remotelocalviewrendering import ContourApp
#   app = ContourApp()
#   app.server.show()
#
# ## Run as a Web Application (default):
#
# ```
# python ./RemoteLocalViewRendering.py --server
# ```
#
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

from pathlib import Path

import vtkmodules.vtkRenderingOpenGL2  # noqa
from vtkmodules.vtkFiltersCore import vtkContourFilter
from vtkmodules.vtkIOXML import vtkXMLImageDataReader
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from trame.app import get_server
from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vtk as vtk_widgets
from trame.widgets import vuetify3

# -----------------------------------------------------------------------------
# Application
# -----------------------------------------------------------------------------


class ContourApp(TrameApp):
    def __init__(self, server=None, **kwargs):
        super().__init__(server=get_server(server, client_type="vue3"), **kwargs)

        # Initialize VTK, State, and UI
        self._initialize_vtk()
        self._initialize_state()
        self._build_ui()

        # Initial contour update
        self.update_contour()

    def _initialize_vtk(self):
        # VTK pipeline
        data_directory = Path(__file__).parent.parent.with_name("data")
        head_vti = data_directory / "head.vti"

        self.reader = vtkXMLImageDataReader()
        self.reader.SetFileName(head_vti)
        self.reader.Update()

        self.contour = vtkContourFilter()
        self.contour.SetInputConnection(self.reader.GetOutputPort())
        self.contour.SetComputeNormals(1)
        self.contour.SetComputeScalars(0)

        # Rendering setup
        self.renderer = vtkRenderer()
        self.render_window = vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)

        # Setup interactor
        self.render_window_interactor = vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)
        self.render_window_interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        mapper = vtkPolyDataMapper()
        actor = vtkActor()
        mapper.SetInputConnection(self.contour.GetOutputPort())
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()

    def _initialize_state(self):
        data_range = self.reader.GetOutput().GetPointData().GetScalars().GetRange()
        contour_value = 0.5 * (data_range[0] + data_range[1])

        self.state.trame__title = "VTK Remote/Local Contour"
        self.state.data_range = data_range
        self.state.contour_value = contour_value
        self.state.view_mode = "local"  # local and remote
        self.state.theme_mode = "light"

    @change("contour_value")
    def update_contour(self, **kwargs):
        self.contour.SetValue(0, self.state.contour_value)
        self.ctrl.view_update_image()  # For remote rendering

    def _build_ui(self):
        with SinglePageLayout(self.server, full_height=True, theme=("theme_mode", self.state.theme_mode)) as layout:
            layout.title.set_text("Contour")
            layout.icon.click = self.ctrl.view_reset_camera

            with layout.toolbar:
                vuetify3.VSpacer()

                with vuetify3.VBtnToggle(
                    v_model=("view_mode", self.state.view_mode),
                    density="compact",
                    mandatory=True,
                    rounded=0,
                ) as toggle:
                    vuetify3.VBtn(value="local", icon="mdi-laptop")
                    vuetify3.VBtn(value="remote", icon="mdi-remote")
                vuetify3.VSpacer()
                vuetify3.VSlider(
                    v_model="contour_value",
                    min=self.state.data_range[0],
                    max=self.state.data_range[1],
                    hide_details=True,
                    density="compact",
                    style="max-width: 300px",
                    thumb_label=True,
                    __events__=["end"],
                    end=self.ctrl.view_update,
                )
                with vuetify3.VBtn(
                    icon=True,
                    click="theme_mode = theme_mode == 'light' ? 'dark' : 'light'",
                ):
                    vuetify3.VIcon("mdi-theme-light-dark")

                with vuetify3.VBtn(icon=True, click=self.ctrl.view_reset_camera):
                    vuetify3.VIcon("mdi-crop-free")

                vuetify3.VProgressLinear(
                    indeterminate=True,
                    absolute=True,
                    bottom=True,
                    active=("trame__busy",),
                )

            with layout.content:
                with vuetify3.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                ):
                    view = vtk_widgets.VtkRemoteLocalView(
                        self.render_window,
                        namespace="view",
                        mode=("view_mode",self.state.view_mode),
                    )
                    self.ctrl.view_reset_camera = view.reset_camera
                    self.ctrl.view_update = view.update
                    self.ctrl.view_update_image = view.update_image
                    view.push_remote_camera_on_end_interaction()

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    app = ContourApp()
    app.server.start()


if __name__ == "__main__":
    main()
