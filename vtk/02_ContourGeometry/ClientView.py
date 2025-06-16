#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
#     "vtk",
# ]
# ///

# # VTK Contour Geometry
#
# This application demonstrates how to visualize the output of a VTK contour filter.
# It allows the user to dynamically change the contour value and see the resulting
# geometry update in real-time. The rendering is performed on the client side.
#
# **Key Features:**
# - Server-side VTK pipeline with a `vtkContourFilter`.
# - Client-side rendering using `VtkLocalView`.
# - Interactive contour value adjustment with a slider.
# - Dynamic updates of the geometry.

# ---
#
# Running if uv is available:
# `uv run ./vtk/02_ContourGeometry/ClientView.py`
#
# Or with Python:
# `python ./vtk/02_ContourGeometry/ClientView.py`
#
# Required packages:
# `pip install trame trame-vuetify trame-vtk vtk`
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('ClientView.py' to 'contour_app.py') is renamed and in the same
#   directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from contour_app import ContourApp
#   app = ContourApp()
#   app.server.show()
#
# ---

import vtk
from pathlib import Path

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3 as vuetify, vtk as vtk_widgets

# -----------------------------------------------------------------------------
# VTK pipeline
# -----------------------------------------------------------------------------

def create_pipeline():
    """Create and return a VTK pipeline."""
    data_directory = Path(__file__).parent.parent.with_name("data")
    head_vti = data_directory / "head.vti"

    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(str(head_vti))
    reader.Update()

    contour = vtk.vtkContourFilter()
    contour.SetInputConnection(reader.GetOutputPort())
    contour.SetComputeNormals(1)
    contour.SetComputeScalars(0)

    data_range = reader.GetOutput().GetPointData().GetScalars().GetRange()
    contour_value = 0.5 * (data_range[0] + data_range[1])

    contour.SetNumberOfContours(1)
    contour.SetValue(0, contour_value)

    return {
        "reader": reader,
        "contour": contour,
        "data_range": data_range,
        "contour_value": contour_value,
    }


# -----------------------------------------------------------------------------
# Trame Application
# -----------------------------------------------------------------------------


class ContourApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server=server, client_type="vue3")

        # VTK pipeline setup
        pipeline = create_pipeline()
        self.reader = pipeline["reader"]
        self.contour_filter = pipeline["contour"] # Renamed for clarity

        # VTK rendering setup for VtkLocalView
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.render_window.OffScreenRenderingOn() # Important for VtkLocalView

        self.mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()
        self.mapper.SetInputConnection(self.contour_filter.GetOutputPort())
        self.actor.SetMapper(self.mapper)
        self.renderer.AddActor(self.actor)
        self.renderer.ResetCamera()

        # Initialize state
        self._initialize_state(pipeline["data_range"], pipeline["contour_value"])

        # Build UI
        self.ui = self._build_ui()

        # Initial update
        self._on_contour_change()

    def _initialize_state(self, data_range, contour_value):
        """Initialize the application's state."""
        self.state.trame__title = "VTK Contour - Client Rendering"
        self.state.data_range = data_range
        self.state.contour_value = contour_value

    @change("contour_value")
    def _on_contour_change(self, **kwargs):
        """Update the contour filter when the contour_value state changes."""
        if self.state.contour_value is None:
            return

        self.contour_filter.SetValue(0, self.state.contour_value)
        # self.ctrl.contour_update() # VtkPolyData widget not used directly with VtkLocalView like this
        self.mapper.Update()
        if self.render_window.GetInteractor() and self.render_window.GetInteractor().GetInitialized():
            self.render_window.Render()
        self.ctrl.view_update() # Signal VtkLocalView to update

    def _build_ui(self):
        """Build the user interface."""
        with SinglePageLayout(self.server) as layout:
            layout.title.set_text("Contour Application")

            with layout.toolbar:
                vuetify.VSpacer()
                vuetify.VSlider(
                    v_model=("contour_value", self.state.contour_value),
                    min=("data_range[0]", self.state.data_range[0]),
                    max=("data_range[1]", self.state.data_range[1]),
                    hide_details=True,
                    dense=True,
                    style="max-width: 300px",
                    thumb_label=True,
                )
                vuetify.VSwitch(
                    v_model="$vuetify.theme.dark",
                    hide_details=True,
                )
                # Use view_reset_camera from VtkLocalView via ctrl
                with vuetify.VBtn(icon=True, click=self.ctrl.view_reset_camera):
                    vuetify.VIcon("mdi-crop-free")

                vuetify.VProgressLinear(
                    indeterminate=True,
                    absolute=True,
                    bottom=True,
                    active=("trame__busy",),
                )

            with layout.content:
                with vuetify.VContainer(fluid=True, classes="pa-0 fill-height"):
                    # VtkLocalView requires the render_window
                    view = vtk_widgets.VtkLocalView(
                        self.render_window,
                        ref="view", # Add ref for direct access if needed
                    )
                    self.ctrl.view_reset_camera = view.reset_camera
                    self.ctrl.view_update = view.update # Expose update method
                    # No VtkGeometryRepresentation or VtkPolyData needed here for VtkLocalView
                    # The actor is already in the renderer passed to VtkLocalView

            return layout


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main():
    """Create and start the Trame application."""
    app = ContourApp()
    app.server.start()


if __name__ == "__main__":
    main()
