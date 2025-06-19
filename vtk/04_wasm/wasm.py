#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "trame>=3.10",
#     "trame-components>=2.5",
#     "trame-vtklocal",
#     "trame-vuetify",
#     "vtk==9.5.0rc2",
# ]
#
# [[tool.uv.index]]
# url = "https://wheels.vtk.org"
# ///

# # Bike CFD with VTKLocal (WASM)
#
# This application demonstrates client-side rendering of a bike CFD simulation
# using `trame-vtklocal` (VTK compiled to WebAssembly - WASM). It allows
# interaction with a line widget to change streamlines and adjust the bike's opacity.
#
# **Key Features:**
# - Client-side VTK rendering with `vtklocal.LocalView`.
# - Interactive line widget for streamline seeding.
# - Opacity control for the bike model.
# - Demonstrates `HttpFile` for remote data fetching.
# - WASM-specific event handling for widget interaction.

# ---
# Running if uv is available:
#   uv run ./vtk/04_wasm/wasm.py
#   # or simply (if +x)
#   ./vtk/04_wasm/wasm.py
#
# Required Packages:
#   The `uv run` command above will handle dependencies automatically.
#   If you don't have `uv`, you can try:
#   pip install trame trame-components trame-vtklocal trame-vuetify vtk==9.5.0rc2 --index-url https://wheels.vtk.org
#
# Run as a Desktop Application:
#   python ./vtk/04_wasm/wasm.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('wasm.py' to 'bike_cfd_wasm.py') is
#   in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from bike_cfd_wasm import BikeCFDWasmApp
#   app = BikeCFDWasmApp()
#   app.server.show()
#
# Run as a Web Application (default):
#   python ./vtk/04_wasm/wasm.py --server
# ---

import vtk

from trame.app import TrameApp, get_server
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import vtklocal, trame as tw_widgets, vuetify3
from trame.decorators import change
from trame.assets.remote import HttpFile
from trame.assets.local import to_url

# -----------------------------------------------------------------------------
# Data Fetching Setup
# -----------------------------------------------------------------------------
BIKE_FILE = HttpFile(
    "data/bike.vtp",
    "https://github.com/Kitware/trame-app-bike/raw/master/data/bike.vtp",
)
TUNNEL_FILE = HttpFile(
    "data/tunnel.vtu",
    "https://github.com/Kitware/trame-app-bike/raw/master/data/tunnel.vtu",
)
IMAGE_FILE = HttpFile(
    "docs/images/seeds.jpg",
    "https://github.com/Kitware/trame-app-bike/raw/master/data/seeds.jpg",
)



# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
P1_INITIAL = [-0.4, 0, 0.05]
P2_INITIAL = [-0.4, 0, 1.5]
K_RANGE = [0.0, 15.6]
LINE_SEED_RESOLUTION = 50

# -----------------------------------------------------------------------------
# Main Application Class
# -----------------------------------------------------------------------------
class BikeCFDWasmApp(TrameApp):
    def __init__(self, server=None, **kwargs):
        super().__init__(server=server, client_type="vue3", **kwargs)


        self.trame__title = "Bike CFD (WASM)"

        self._initialize_vtk()
        self._initialize_state()
        self._build_ui()

    def _initialize_state(self):

        self.state.trame__favicon = to_url(IMAGE_FILE.path)
        self.state.line_widget = {
            "p1": list(P1_INITIAL),
            "p2": list(P2_INITIAL),
        }
        self.state.bike_opacity = 1.0

    def _initialize_vtk(self):
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)

        # Interactor setup for vtkLineWidget2
        self.interactor = vtk.vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.render_window)
        self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        # Readers
        self.bike_reader = vtk.vtkXMLPolyDataReader()
        self.bike_reader.SetFileName(BIKE_FILE.path)

        self.tunnel_reader = vtk.vtkXMLUnstructuredGridReader()
        self.tunnel_reader.SetFileName(TUNNEL_FILE.path)
        self.tunnel_reader.Update() # Important to read data

        # Line seed source for streamlines
        self.line_seed_source = vtk.vtkLineSource()
        self.line_seed_source.SetPoint1(*P1_INITIAL)
        self.line_seed_source.SetPoint2(*P2_INITIAL)
        self.line_seed_source.SetResolution(LINE_SEED_RESOLUTION)
        self.line_seed_source.Update()

        # Interactive Line Widget
        self.line_widget = vtk.vtkLineWidget2()
        line_widget_rep = self.line_widget.GetRepresentation()
        line_widget_rep.SetPoint1WorldPosition(P1_INITIAL)
        line_widget_rep.SetPoint2WorldPosition(P2_INITIAL)
        self.line_widget.SetInteractor(self.interactor) # Link widget to interactor

        # Stream Tracer
        self.stream_tracer = vtk.vtkStreamTracer()
        self.stream_tracer.SetInputConnection(self.tunnel_reader.GetOutputPort())
        self.stream_tracer.SetSourceConnection(self.line_seed_source.GetOutputPort())
        self.stream_tracer.SetIntegrationDirectionToForward()
        self.stream_tracer.SetIntegratorTypeToRungeKutta45()
        self.stream_tracer.SetMaximumPropagation(3)
        self.stream_tracer.SetIntegrationStepUnit(2) # VTK_CELL_LENGTH_UNIT
        self.stream_tracer.SetInitialIntegrationStep(0.2)
        self.stream_tracer.SetMinimumIntegrationStep(0.01)
        self.stream_tracer.SetMaximumIntegrationStep(0.5)
        self.stream_tracer.SetMaximumError(1.0e-6)
        self.stream_tracer.SetMaximumNumberOfSteps(2000)
        self.stream_tracer.SetTerminalSpeed(1.0e-12)

        # Tube Filter for streamlines
        self.tube_filter = vtk.vtkTubeFilter()
        self.tube_filter.SetInputConnection(self.stream_tracer.GetOutputPort())
        self.tube_filter.SetRadius(0.01)
        self.tube_filter.SetNumberOfSides(6)
        self.tube_filter.CappingOn()
        self.tube_filter.Update()

        # Bike Actor
        self.bike_mapper = vtk.vtkPolyDataMapper()
        self.bike_actor = vtk.vtkActor()
        self.bike_mapper.SetInputConnection(self.bike_reader.GetOutputPort())
        self.bike_actor.SetMapper(self.bike_mapper)
        self.renderer.AddActor(self.bike_actor)

        # Streamlines Actor
        self.stream_mapper = vtk.vtkPolyDataMapper()
        self.stream_actor = vtk.vtkActor()
        self.stream_mapper.SetInputConnection(self.tube_filter.GetOutputPort())
        self.stream_actor.SetMapper(self.stream_mapper)
        self.renderer.AddActor(self.stream_actor)

        # Lookup Table for streamline coloring
        lut = vtk.vtkLookupTable()
        lut.SetHueRange(0.7, 0)
        lut.SetSaturationRange(1.0, 0)
        lut.SetValueRange(0.5, 1.0)
        self.stream_mapper.SetLookupTable(lut)
        self.stream_mapper.SetColorModeToMapScalars()
        self.stream_mapper.SetScalarModeToUsePointData()
        self.stream_mapper.SelectColorArray("k") # Ensure this array exists
        self.stream_mapper.SetScalarRange(K_RANGE)

        # Renderer and Camera setup
        self.renderer.SetBackground(0.4, 0.4, 0.4)
        self.renderer.ResetCamera()
        self.line_widget.On() # Enable the widget

    @change("bike_opacity")
    def _on_opacity_change(self, bike_opacity, **_kwargs):
        self.bike_actor.GetProperty().SetOpacity(bike_opacity)
        if self.ctrl.view_update:
            self.ctrl.view_update()

    @change("line_widget")
    def _on_line_widget_change(self, line_widget, **_kwargs):
        if line_widget is None:
            return

        p1 = line_widget.get("p1")
        p2 = line_widget.get("p2")

        # Defensive check for valid points
        if not (
            p1 and len(p1) == 3 and all(isinstance(v, (int, float)) for v in p1) and
            p2 and len(p2) == 3 and all(isinstance(v, (int, float)) for v in p2)
        ):
            return

        # Update the streamline source
        self.line_seed_source.SetPoint1(p1)
        self.line_seed_source.SetPoint2(p2)
        self.line_seed_source.Update()

        # If the update came from the UI sliders, update the 3D widget's position
        if line_widget.get("widget_update"):
            self.line_widget.GetRepresentation().SetPoint1WorldPosition(p1)
            self.line_widget.GetRepresentation().SetPoint2WorldPosition(p2)

        if self.ctrl.view_update:
            self.ctrl.view_update()

    def _build_ui(self):
        with SinglePageWithDrawerLayout(self.server, full_height=True) as layout:
            self.ui = layout  # For Jupyter integration


            layout.title.set_text(self.trame__title)

            with layout.toolbar:
                layout.toolbar.density = "compact"
                vuetify3.VSpacer()
                vuetify3.VSlider(
                    v_model=("bike_opacity", self.state.bike_opacity),
                    min=0,
                    max=1,
                    step=0.05,
                    density="compact",
                    hide_details=True,
                    style="max-width: 200px; margin-right: 10px;",
                    thumb_label=True,
                )
                vuetify3.VBtn(icon="mdi-crop-free", click=self.ctrl.view_reset_camera)

            with layout.drawer:
                tw_widgets.LineSeed(
                    image=("trame__favicon",),
                    point_1=("line_widget.p1",),
                    point_2=("line_widget.p2",),
                    bounds=("[-0.399, 1.80, -1.12, 1.11, -0.43, 1.79]",),
                    update_seed="line_widget = { ...$event, widget_update: 1 }",
                    n_sliders=2,
                )

            with layout.content:
                with vtklocal.LocalView(self.render_window, throttle_rate=20) as view:
                    self.ctrl.view_update = view.update_throttle
                    self.ctrl.view_reset_camera = view.reset_camera

                    widget_id = view.register_vtk_object(self.line_widget)

                    # Listeners to update Python state from WASM widget interaction
                    view.listeners = (
                        "wasm_interaction_listeners",
                        {
                            widget_id: {
                                "InteractionEvent": {
                                    "line_widget": {
                                        "p1": (widget_id, "WidgetRepresentation", "Point1WorldPosition"),
                                        "p2": (widget_id, "WidgetRepresentation", "Point2WorldPosition"),
                                    }
                                },
                            },
                        },
                    )



# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------
def main(**kwargs):
    server = get_server(client_type="vue3")
    app = BikeCFDWasmApp(server=server, **kwargs)
    app.server.start()

if __name__ == "__main__":
    main()