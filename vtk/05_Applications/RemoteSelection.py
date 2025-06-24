#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
#     "pandas",
#     "plotly",
# ]
# ///

#
# # VTK Remote Selection
#
# A basic application that demonstrates how to link a VTK remote view with a
# Plotly chart. The application allows for cross-selection between the two
# views.
#
# **Key Features:**
#
# - VTK remote view for 3D visualization.
# - Plotly chart for data exploration.
# - Cross-selection between the VTK view and the Plotly chart.
#
# **Usage Instructions:**
#
# **Running if `uv` is available:**
#
# ```bash
# # Directly execute the script
# ./vtk/05_Applications/RemoteSelection.py
#
# # Or run with uv
# uv run ./vtk/05_Applications/RemoteSelection.py
# ```
#
# **Required Packages:**
#
# `uv` will automatically create a virtual environment and install the required packages.
# If you are not using `uv`, you can install the packages with:
#
# ```bash
# pip install trame trame-vuetify trame-vtk pandas plotly
# ```
#
# **Run as a Desktop Application:**
#
# ```bash
# python vtk/05_Applications/RemoteSelection.py --app
# ```
#
# **Run as a Web Application (default):**
#
# ```bash
# python vtk/05_Applications/RemoteSelection.py --server
# ```
#
# **Run in Jupyter Lab / Notebook:**
#
# After renaming the file to `RemoteSelection_app.py`, you can run the following in a cell:
#
# ```python
# from RemoteSelection_app import RemoteSelectionApp
#
# app = RemoteSelectionApp()
# await app.ui.ready
# app.ui
# ```
#
# ---


import os
import pandas as pd
import plotly.express as px




# VTK imports
import vtkmodules.vtkRenderingOpenGL2  # noqa
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkIdTypeArray
from vtkmodules.vtkCommonDataModel import vtkDataObject, vtkSelection, vtkSelectionNode
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleRubberBandPick  # noqa
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkHardwareSelector,
    vtkRenderedAreaPicker,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

# Trame imports
from trame.app import get_server
from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import plotly, trame
from trame.widgets import vuetify3 as vuetify
from trame.widgets import vtk as vtk_widgets

# -----------------------------------------------------------------------------
# Helper function
# -----------------------------------------------------------------------------


def find_data_file(start_dir, target_suffix="data/disk_out_ref.vtu"):
    current_dir = os.path.abspath(start_dir)
    while True:
        potential_path = os.path.join(current_dir, target_suffix)
        if os.path.exists(potential_path):
            return os.path.normpath(potential_path)

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached the root
            return None
        current_dir = parent_dir

class RemoteSelectionApp(TrameApp):
    """A Trame application for remote selection."""

    def __init__(self, server=None):
        super().__init__(server=server, client_type="vue3")

        # VTK objects
        self.reader = vtkXMLUnstructuredGridReader()
        self.dataset = None
        self.renderer = vtkRenderer()
        self.render_window = vtkRenderWindow()
        self.rw_interactor = vtkRenderWindowInteractor()
        self.interactor_trackball = None
        self.interactor_selection = vtkInteractorStyleRubberBandPick()
        self.area_picker = vtkRenderedAreaPicker()
        self.surface_filter = vtkGeometryFilter()
        self.mapper = vtkDataSetMapper()
        self.actor = vtkActor()
        self.selection_extract = vtkExtractSelection()
        self.selection_mapper = vtkDataSetMapper()
        self.selection_actor = vtkActor()
        self.selector = vtkHardwareSelector()
        self.py_ds = None

        # DataFrame
        self.dataframe = None

        # Initialize
        self._initialize_vtk()
        self._initialize_dataframe()
        self._initialize_state()
        self._build_ui()

    def _initialize_vtk(self):
        _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        data_file = find_data_file(_SCRIPT_DIR)
        if not data_file:
            print("Could not find data/disk_out_ref.vtu")
            return

        self.reader.SetFileName(data_file)
        self.reader.Update()
        self.dataset = self.reader.GetOutput()
        self.py_ds = dsa.WrapDataObject(self.dataset)

        self.renderer.SetBackground(1, 1, 1)
        self.render_window.AddRenderer(self.renderer)
        self.render_window.SetOffScreenRendering(1)

        self.rw_interactor.SetRenderWindow(self.render_window)
        self.interactor_trackball = self.rw_interactor.GetInteractorStyle()
        self.interactor_trackball.SetCurrentStyleToTrackballCamera()
        self.rw_interactor.SetPicker(self.area_picker)

        self.surface_filter.SetInputConnection(self.reader.GetOutputPort())
        self.surface_filter.SetPassThroughPointIds(True)

        self.mapper.SetInputConnection(self.surface_filter.GetOutputPort())
        self.actor.GetProperty().SetOpacity(0.5)
        self.actor.SetMapper(self.mapper)

        # Selection actor setup
        self.selection_mapper.SetInputConnection(self.selection_extract.GetOutputPort())
        self.selection_actor.GetProperty().SetColor(1, 0, 1)
        self.selection_actor.GetProperty().SetPointSize(5)
        self.selection_actor.SetMapper(self.selection_mapper)
        self.selection_actor.SetVisibility(0)

        self.renderer.AddActor(self.actor)
        self.renderer.AddActor(self.selection_actor)
        self.renderer.ResetCamera()

        self.selector.SetRenderer(self.renderer)
        self.selector.SetFieldAssociation(vtkDataObject.FIELD_ASSOCIATION_POINTS)

    def _initialize_dataframe(self):
        pt_data = self.py_ds.PointData
        cols = {}
        for name in pt_data.keys():
            array = pt_data[name]
            shp = array.shape
            if len(shp) == 1:
                cols[name] = array
            else:
                for i in range(shp[1]):
                    cols[f"{name}_{i}"] = array[:, i]
        self.dataframe = pd.DataFrame(cols)

    def _initialize_state(self):
        field_names = list(self.dataframe.keys())
        self.state.trame__title = "VTK Remote Selection"
        self.state.scatter_x = field_names[0]
        self.state.scatter_y = field_names[1]
        self.state.field_names = field_names
        self.state.selected_indices = []
        self.state.vtk_selection = False

    @change("scatter_x", "scatter_y")
    def _update_figure(self, scatter_x, scatter_y, **kwargs):
        fig = px.scatter(
            self.dataframe,
            x=scatter_x,
            y=scatter_y,
        )

        # Update selection settings
        fig.data[0].update(
            selectedpoints=self.state.selected_indices,
            selected={"marker": {"color": "red"}},
            unselected={"marker": {"opacity": 0.5}},
        )

        # Update chart
        self.ctrl.plotly_figure_update(fig)

    @change("vtk_selection")
    def _update_interactor(self, vtk_selection, **kwargs):
        if vtk_selection:
            self.rw_interactor.SetInteractorStyle(self.interactor_selection)
            self.interactor_selection.StartSelect()
        else:
            self.rw_interactor.SetInteractorStyle(self.interactor_trackball)

    def _on_chart_selection(self, selected_point_idxs):
        self.state.selected_indices = selected_point_idxs if selected_point_idxs else []
        npts = len(self.state.selected_indices)

        ids = vtkIdTypeArray()
        ids.SetNumberOfTuples(npts)
        for idx, p_id in enumerate(self.state.selected_indices):
            ids.SetTuple1(idx, p_id)

        sel_node = vtkSelectionNode()
        sel_node.GetProperties().Set(
            vtkSelectionNode.CONTENT_TYPE(), vtkSelectionNode.INDICES
        )
        sel_node.GetProperties().Set(vtkSelectionNode.FIELD_TYPE(), vtkSelectionNode.POINT)
        sel_node.SetSelectionList(ids)
        sel = vtkSelection()
        sel.AddNode(sel_node)

        # Use the full dataset for chart selections
        self.selection_extract.SetInputDataObject(0, self.py_ds.VTKObject)
        self.selection_extract.SetInputDataObject(1, sel)
        self.selection_extract.Update()
        self.selection_actor.SetVisibility(1 if npts > 0 else 0)

        self.ctrl.view_update()

    def _on_box_selection_change(self, event):
        if event.get("mode") == "remote":
            self.actor.GetProperty().SetOpacity(1)
            self.selector.SetArea(
                int(self.renderer.GetPickX1()),
                int(self.renderer.GetPickY1()),
                int(self.renderer.GetPickX2()),
                int(self.renderer.GetPickY2()),
            )
        elif event.get("mode") == "local":
            camera = self.renderer.GetActiveCamera()
            camera_props = event.get("camera")

            # Sync client view to server one
            camera.SetPosition(camera_props.get("position"))
            camera.SetFocalPoint(camera_props.get("focalPoint"))
            camera.SetViewUp(camera_props.get("viewUp"))
            camera.SetParallelProjection(camera_props.get("parallelProjection"))
            camera.SetParallelScale(camera_props.get("parallelScale"))
            camera.SetViewAngle(camera_props.get("viewAngle"))
            self.render_window.SetSize(event.get("size"))

            self.actor.GetProperty().SetOpacity(1)
            self.render_window.Render()

            area = event.get("selection")
            self.selector.SetArea(
                int(area[0]),
                int(area[2]),
                int(area[1]),
                int(area[3]),
            )

        # Common server selection
        s = self.selector.Select()
        n = s.GetNode(0)
        if not n:
            self.state.vtk_selection = False
            return

        ids = dsa.vtkDataArrayToVTKArray(n.GetSelectionData().GetArray("SelectedIds"))
        surface = dsa.WrapDataObject(self.surface_filter.GetOutput())
        self.state.selected_indices = surface.PointData["vtkOriginalPointIds"][ids].tolist()

        self.selection_extract.SetInputConnection(0, self.surface_filter.GetOutputPort())
        self.selection_extract.SetInputDataObject(1, s)
        self.selection_extract.Update()
        self.selection_actor.SetVisibility(len(self.state.selected_indices) > 0)
        self.actor.GetProperty().SetOpacity(0.5)

        # Update scatter plot with selection
        self._update_figure(**self.state.to_dict())

        # Update 3D view
        self.ctrl.view_update()

        # disable selection mode
        self.state.vtk_selection = False

    def _build_ui(self):
        self.ctrl.on_server_ready.add(self.ctrl.view_update)
        self.ctrl.on_server_ready.add(self._update_figure)

        with SinglePageLayout(self.server) as layout:
            layout.title.set_text("VTK & Plotly Cross-Selection")
            layout.icon.click = self.ctrl.view_reset_camera

            with layout.toolbar:
                vuetify.VSpacer()
                vuetify.VSelect(
                    v_model=("scatter_y", self.state.scatter_y),
                    items=("field_names", self.state.field_names),
                    label="Y-axis",
                    dense=True,
                    hide_details=True,
                    classes="px-2",
                    style="max-width: 200px;",
                )
                vuetify.VSelect(
                    v_model=("scatter_x", self.state.scatter_x),
                    items=("field_names", self.state.field_names),
                    label="X-axis",
                    dense=True,
                    hide_details=True,
                    classes="px-2",
                    style="max-width: 200px;",
                )

            with layout.content:
                with vuetify.VContainer(fluid=True, classes="fill-height pa-0 ma-0"):
                    with vuetify.VRow(dense=True, style="height: 100%;"):
                        with vuetify.VCol(
                            classes="pa-0",
                            style="border-right: 1px solid #ccc; position: relative;",
                        ):
                            view = vtk_widgets.VtkRemoteView(
                                self.render_window,
                                box_selection=("vtk_selection", False),
                                box_selection_change=(self._on_box_selection_change, "[$event]"),
                                interactive_ratio=1,
                                interactive_quality=80,
                            )
                            self.ctrl.view_update = view.update
                            self.ctrl.view_reset_camera = view.reset_camera
                            vuetify.VCheckbox(
                                small=True,
                                on_icon="mdi-selection-drag",
                                off_icon="mdi-rotate-3d",
                                v_model=("vtk_selection", False),
                                style="position: absolute; top: 0; right: 0; z-index: 1;",
                                dense=True,
                                hide_details=True,
                        label="Selection",
                            )
                        with vuetify.VCol(classes="pa-0"):
                            html_plot = plotly.Figure(
                                selected=(
                                    self._on_chart_selection,
                                    "[$event?.points.map(({pointIndex}) => pointIndex)]",
                                ),
                            )
                            self.ctrl.plotly_figure_update = html_plot.update


def main():
    """Run the application."""
    app = RemoteSelectionApp()
    app.server.start()


if __name__ == "__main__":
    main()
