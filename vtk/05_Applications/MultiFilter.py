#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
#     "vtk"
# ]
# ///

# # VTK Multi-Filter Application
#
# This application demonstrates how to use Trame to control multiple VTK filters
# (a mesh representation and a contour filter) applied to a dataset.
# It allows users to interactively change properties for each filter, such as
# representation, color mapping, opacity, and contour parameters.
#
# **Key Features:**
# - Display a VTK UnstructuredGrid (disk_out_ref.vtu).
# - Independent controls for a mesh actor and a contour actor.
# - Toggle visibility of actors and cube axes.
# - Change actor representation (points, wireframe, surface, surface with edges).
# - Color actors by different data arrays.
# - Apply different color lookup tables (LUTs).
# - Adjust actor opacity.
# - For contours: select contouring array and adjust contour value.
# - Theme switching (light/dark).
# - Interactive 3D view with camera controls (local/remote rendering).

# --- Usage Instructions ---
#
# Running if uv is available:
#   uv run ./MultiFilter.py
#   ./MultiFilter.py
#
# Required Packages:
#   uv will automatically create a virtual environment and install the packages
#   listed in the header. If you don't have uv, you can manually install them:
#   pip install trame trame-vuetify trame-vtk vtk
#
# Run as a Desktop Application:
#   python MultiFilter.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('MultiFilter.py' to 'multifilter_module.py' or similar)
#   is in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from multifilter_module import MultiFilterApp
#   app = MultiFilterApp()
#   app.server.show()
#
# Run as a Web Application (default):
#   python MultiFilter.py --server
#
# --- End Usage Instructions ---

import os

import vtkmodules.vtkRenderingOpenGL2  # noqa
import vtkmodules.vtkInteractionStyle  # noqa
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkFiltersCore import vtkContourFilter
from vtkmodules.vtkRenderingCore import vtkRenderWindowInteractor
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader
from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
)

from trame.app import TrameApp, get_server
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import vuetify3 as vuetify, vtk as vtk_widgets, trame as trame_widgets

def find_data_file(start_dir, target_suffix="data/disk_out_ref.vtu"):
    current_dir = os.path.abspath(start_dir)
    while True:
        potential_path = os.path.join(current_dir, target_suffix)
        if os.path.exists(potential_path):
            return os.path.normpath(potential_path)
        
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached the root or an unresolvable path
            break
        current_dir = parent_dir
        
    raise FileNotFoundError(
        f"Could not find '{target_suffix}' in '{os.path.abspath(start_dir)}' or any parent directory."
    )

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE_PATH = find_data_file(_SCRIPT_DIR)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

class Representation:
    Points = 0
    Wireframe = 1
    Surface = 2
    SurfaceWithEdges = 3

class LookupTable:
    Rainbow = 0
    Inverted_Rainbow = 1
    Greyscale = 2
    Inverted_Greyscale = 3

# -----------------------------------------------------------------------------
# Main Application Class
# -----------------------------------------------------------------------------

class MultiFilterApp(TrameApp):
    def __init__(self, server=None, **kwargs):
        super().__init__(server=server, client_type="vue3", **kwargs)
        self.app_name = "VTK Multi-Filter Application"
        self._initialize_vtk()
        self._initialize_state()
        self._build_ui()
        self._apply_initial_vtk_properties()

    def _initialize_vtk(self):
        self.renderer = vtkRenderer()
        self.render_window = vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)

        # Explicitly create and set an interactor.
        # This avoids issues with GetInteractor() auto-creation logic (like MakeCurrent())
        # potentially failing or behaving unexpectedly before Trame's view fully manages the context.
        # This interactor is needed by trame_vtk's ServerSideViewStream (for local mode).
        interactor = vtkRenderWindowInteractor()
        self.render_window.SetInteractor(interactor)
        style = vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)
        # interactor.SetRenderWindow(self.render_window) is usually handled by SetInteractor.
        # interactor.Initialize() is not needed as Trame manages the render loop.
        
        self.render_window.SetOffScreenRendering(1)

        # Read Data
        self.reader = vtkXMLUnstructuredGridReader()
        if not os.path.exists(DATA_FILE_PATH):
            raise FileNotFoundError(
                f"VTK data file not found. \n"
                f"Script directory: {_SCRIPT_DIR}\n"
                f"Calculated path: {DATA_FILE_PATH}"
            )
        self.reader.SetFileName(DATA_FILE_PATH)
        self.reader.Update()

        # Extract Array/Field information
        self.dataset_arrays = []
        fields = [
            (self.reader.GetOutput().GetPointData(), vtkDataObject.FIELD_ASSOCIATION_POINTS),
            (self.reader.GetOutput().GetCellData(), vtkDataObject.FIELD_ASSOCIATION_CELLS),
        ]
        for i, (field_arrays, association) in enumerate(fields):
            for j in range(field_arrays.GetNumberOfArrays()):
                array = field_arrays.GetArray(j)
                array_range = array.GetRange()
                # Use a unique value for each array, e.g., its name or a composite index
                array_name = array.GetName()
                self.dataset_arrays.append(
                    {
                        "title": array_name,
                        "value": f"{association}_{array_name}", # Unique value
                        "range": list(array_range),
                        "type": association,
                        "original_text": array_name, # Keep original name for VTK
                    }
                )
        self.default_array_info = self.dataset_arrays[0]
        default_min, default_max = self.default_array_info.get("range")

        # Mesh
        self.mesh_mapper = vtkDataSetMapper()
        self.mesh_mapper.SetInputConnection(self.reader.GetOutputPort())
        self.mesh_actor = vtkActor()
        self.mesh_actor.SetMapper(self.mesh_mapper)
        self.renderer.AddActor(self.mesh_actor)

        # Contour
        self.contour_filter = vtkContourFilter()
        self.contour_filter.SetInputConnection(self.reader.GetOutputPort())
        self.contour_mapper = vtkPolyDataMapper()
        self.contour_mapper.SetInputConnection(self.contour_filter.GetOutputPort())
        self.contour_actor = vtkActor()
        self.contour_actor.SetMapper(self.contour_mapper)
        self.renderer.AddActor(self.contour_actor)

        # Cube Axes
        self.cube_axes_actor = vtkCubeAxesActor()
        self.renderer.AddActor(self.cube_axes_actor)
        self.cube_axes_actor.SetBounds(self.mesh_actor.GetBounds())
        self.cube_axes_actor.SetCamera(self.renderer.GetActiveCamera())
        self.cube_axes_actor.SetXLabelFormat("%6.1f")
        self.cube_axes_actor.SetYLabelFormat("%6.1f")
        self.cube_axes_actor.SetZLabelFormat("%6.1f")
        self.cube_axes_actor.SetFlyModeToOuterEdges()

        self.renderer.ResetCamera()

    def _get_array_info_by_value(self, value):
        for arr_info in self.dataset_arrays:
            if arr_info["value"] == value:
                return arr_info
        return None

    def _initialize_state(self):
        self.state.trame__title = self.app_name
        self.state.theme_mode = "light"
        self.state.view_mode = "remote"  # Default view mode
        self.state.active_ui = "mesh"  # 'mesh' or 'contour'
        self.state.pipeline_items = [
            {"id": "1", "parent": "0", "name": "Mesh", "visible": True},
            {"id": "2", "parent": "1", "name": "Contour", "visible": True},
        ]

        self.state.dataset_arrays = self.dataset_arrays
        default_array_value = self.default_array_info["value"]
        default_min, default_max = self.default_array_info["range"]
        default_contour_value = 0.5 * (default_max + default_min)

        # General Controls
        self.state.cube_axes_visibility = True

        # Mesh Controls
        self.state.mesh_representation = Representation.Surface
        self.state.mesh_color_array_value = default_array_value
        self.state.mesh_color_preset = LookupTable.Rainbow
        self.state.mesh_opacity = 1.0

        # Contour Controls
        self.state.contour_representation = Representation.Surface
        self.state.contour_color_array_value = default_array_value
        self.state.contour_color_preset = LookupTable.Rainbow
        self.state.contour_opacity = 1.0
        self.state.contour_by_array_value = default_array_value
        self.state.contour_value = default_contour_value
        self.state.contour_min = default_min
        self.state.contour_max = default_max
        self.state.contour_step = 0.01 * (default_max - default_min)

        # For VSelect items
        self.state.representation_options = [
            {"title": "Points", "value": Representation.Points},
            {"title": "Wireframe", "value": Representation.Wireframe},
            {"title": "Surface", "value": Representation.Surface},
            {"title": "Surface With Edges", "value": Representation.SurfaceWithEdges},
        ]
        self.state.lut_options = [
            {"title": "Rainbow", "value": LookupTable.Rainbow},
            {"title": "Inv Rainbow", "value": LookupTable.Inverted_Rainbow},
            {"title": "Greyscale", "value": LookupTable.Greyscale},
            {"title": "Inv Greyscale", "value": LookupTable.Inverted_Greyscale},
        ]

    def _apply_initial_vtk_properties(self):
        # Callbacks to set initial VTK state from defaults
        self._on_cube_axes_visibility_change(self.state.cube_axes_visibility)

        self._on_mesh_representation_change(self.state.mesh_representation)
        self._on_mesh_color_array_value_change(self.state.mesh_color_array_value)
        self._on_mesh_color_preset_change(self.state.mesh_color_preset)
        self._on_mesh_opacity_change(self.state.mesh_opacity)

        self._on_contour_representation_change(self.state.contour_representation)
        self._on_contour_color_array_value_change(self.state.contour_color_array_value)
        self._on_contour_color_preset_change(self.state.contour_color_preset)
        self._on_contour_opacity_change(self.state.contour_opacity)
        self._on_contour_by_array_value_change(self.state.contour_by_array_value) # Sets contour value too

        # Initial visibility from pipeline_items
        for item in self.state.pipeline_items:
            self.on_pipeline_visibility_change({"id": item["id"], "visible": item["visible"]})


    # -------------------------------------------------------------------------
    # Callbacks
    # -------------------------------------------------------------------------

    @change("cube_axes_visibility")
    def _on_cube_axes_visibility_change(self, cube_axes_visibility, **kwargs):
        self.cube_axes_actor.SetVisibility(cube_axes_visibility)
        self.ctrl.view_update()

    def on_pipeline_actives_change(self, ids):
        if not ids: return
        active_id = ids[0]
        if active_id == "1":  # Mesh
            self.state.active_ui = "mesh"
        elif active_id == "2":  # Contour
            self.state.active_ui = "contour"
        else:
            self.state.active_ui = None # Or some default/empty state

    def on_pipeline_visibility_change(self, event):
        item_id = event["id"]
        visibility = event["visible"]
        actor_to_update = None
        if item_id == "1":  # Mesh
            actor_to_update = self.mesh_actor
        elif item_id == "2":  # Contour
            actor_to_update = self.contour_actor

        if actor_to_update:
            actor_to_update.SetVisibility(visibility)
            # Update the visible state in pipeline_items for GitTree reactivity
            for item in self.state.pipeline_items:
                if item["id"] == item_id:
                    item["visible"] = visibility
                    break
            self.state.pipeline_items = self.state.pipeline_items # Trigger reactivity
            self.ctrl.view_update()

    def _update_actor_representation(self, actor, mode):
        prop = actor.GetProperty()
        if mode == Representation.Points:
            prop.SetRepresentationToPoints()
            prop.SetPointSize(5)
            prop.EdgeVisibilityOff()
        elif mode == Representation.Wireframe:
            prop.SetRepresentationToWireframe()
            prop.SetPointSize(1)
            prop.EdgeVisibilityOff()
        elif mode == Representation.Surface:
            prop.SetRepresentationToSurface()
            prop.SetPointSize(1)
            prop.EdgeVisibilityOff()
        elif mode == Representation.SurfaceWithEdges:
            prop.SetRepresentationToSurface()
            prop.SetPointSize(1)
            prop.EdgeVisibilityOn()

    @change("mesh_representation")
    def _on_mesh_representation_change(self, mesh_representation, **kwargs):
        self._update_actor_representation(self.mesh_actor, mesh_representation)
        self.ctrl.view_update()

    @change("contour_representation")
    def _on_contour_representation_change(self, contour_representation, **kwargs):
        self._update_actor_representation(self.contour_actor, contour_representation)
        self.ctrl.view_update()

    def _color_actor_by_array(self, actor, array_info):
        if not array_info: return
        min_val, max_val = array_info.get("range")
        mapper = actor.GetMapper()
        mapper.SelectColorArray(array_info.get("original_text"))
        mapper.GetLookupTable().SetRange(min_val, max_val)
        if array_info.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
            mapper.SetScalarModeToUsePointFieldData()
        else:
            mapper.SetScalarModeToUseCellFieldData()
        mapper.SetScalarVisibility(True)
        mapper.SetUseLookupTableScalarRange(True)

    @change("mesh_color_array_value")
    def _on_mesh_color_array_value_change(self, mesh_color_array_value, **kwargs):
        array_info = self._get_array_info_by_value(mesh_color_array_value)
        self._color_actor_by_array(self.mesh_actor, array_info)
        self.ctrl.view_update()

    @change("contour_color_array_value")
    def _on_contour_color_array_value_change(self, contour_color_array_value, **kwargs):
        array_info = self._get_array_info_by_value(contour_color_array_value)
        self._color_actor_by_array(self.contour_actor, array_info)
        self.ctrl.view_update()

    def _apply_lut_preset(self, actor, preset):
        lut = actor.GetMapper().GetLookupTable()
        if preset == LookupTable.Rainbow:
            lut.SetHueRange(0.666, 0.0)
            lut.SetSaturationRange(1.0, 1.0)
            lut.SetValueRange(1.0, 1.0)
        elif preset == LookupTable.Inverted_Rainbow:
            lut.SetHueRange(0.0, 0.666)
            lut.SetSaturationRange(1.0, 1.0)
            lut.SetValueRange(1.0, 1.0)
        elif preset == LookupTable.Greyscale:
            lut.SetHueRange(0.0, 0.0)
            lut.SetSaturationRange(0.0, 0.0)
            lut.SetValueRange(0.0, 1.0)
        elif preset == LookupTable.Inverted_Greyscale:
            lut.SetHueRange(0.0, 0.0) # Corrected from original
            lut.SetSaturationRange(0.0, 0.0)
            lut.SetValueRange(1.0, 0.0)
        lut.Build()

    @change("mesh_color_preset")
    def _on_mesh_color_preset_change(self, mesh_color_preset, **kwargs):
        self._apply_lut_preset(self.mesh_actor, mesh_color_preset)
        self.ctrl.view_update()

    @change("contour_color_preset")
    def _on_contour_color_preset_change(self, contour_color_preset, **kwargs):
        self._apply_lut_preset(self.contour_actor, contour_color_preset)
        self.ctrl.view_update()

    @change("mesh_opacity")
    def _on_mesh_opacity_change(self, mesh_opacity, **kwargs):
        self.mesh_actor.GetProperty().SetOpacity(mesh_opacity)
        self.ctrl.view_update()

    @change("contour_opacity")
    def _on_contour_opacity_change(self, contour_opacity, **kwargs):
        self.contour_actor.GetProperty().SetOpacity(contour_opacity)
        self.ctrl.view_update()

    @change("contour_by_array_value")
    def _on_contour_by_array_value_change(self, contour_by_array_value, **kwargs):
        array_info = self._get_array_info_by_value(contour_by_array_value)
        if not array_info: return

        contour_min, contour_max = array_info.get("range")
        contour_step = 0.01 * (contour_max - contour_min) if (contour_max - contour_min) > 0 else 0.01
        contour_val = 0.5 * (contour_max + contour_min)

        self.contour_filter.SetInputArrayToProcess(
            0, 0, 0, array_info.get("type"), array_info.get("original_text")
        )
        self.contour_filter.SetValue(0, contour_val)

        self.state.contour_min = contour_min
        self.state.contour_max = contour_max
        self.state.contour_value = contour_val
        self.state.contour_step = contour_step
        self.ctrl.view_update()

    @change("contour_value")
    def _on_contour_value_change(self, contour_value, **kwargs):
        self.contour_filter.SetValue(0, float(contour_value))
        self.ctrl.view_update()

    # -------------------------------------------------------------------------
    # UI Building
    # -------------------------------------------------------------------------
    def _build_ui(self):
        with SinglePageWithDrawerLayout(self.server, full_height=True) as layout:
            layout.root.theme = ("theme_mode",)
            layout.title.set_text(self.app_name)

            with layout.toolbar:
                vuetify.VSpacer()
                with vuetify.VBtn(
                    icon=True,
                    click="theme_mode = theme_mode == 'light' ? 'dark' : 'light'",
                    color=("theme_mode == 'dark' ? 'primary' : None",)
                ):
                    vuetify.VIcon("mdi-theme-light-dark")

                with vuetify.VBtn(
                    icon=True,
                    click="cube_axes_visibility = !cube_axes_visibility",
                    color=("cube_axes_visibility ? 'primary' : None",)
                ):
                    vuetify.VIcon("mdi-cube-outline")

                with vuetify.VBtn(
                    icon=True,
                    click="view_mode = view_mode == 'remote' ? 'local' : 'remote'",
                    color=("view_mode == 'remote' ? 'primary' : None",)
                ):
                    vuetify.VIcon("mdi-remote")

                with vuetify.VBtn(icon=True, click=self.ctrl.view_reset_camera): # Use controller
                    vuetify.VIcon("mdi-crop-free") # Icon name is sufficient

            with layout.drawer as drawer:
                drawer.width = 350
                with vuetify.VSheet(classes="pa-2 border-lg"):
                    trame_widgets.GitTree(
                        sources=("pipeline_items",),
                        actives_change=(self.on_pipeline_actives_change, "[$event]"),
                        visibility_change=(self.on_pipeline_visibility_change, "[$event]"),
                        active_key="id",
                        children_key="children", # Not used here but good practice
                        visibility_key="visible",
                    )
                with vuetify.VExpansionPanels(v_model=("active_ui",), mandatory=True, classes="mt-2"):
                    with vuetify.VExpansionPanel(value="mesh", title="Mesh Settings"):
                        with vuetify.VExpansionPanelText():
                            self._build_actor_controls("mesh")
                    with vuetify.VExpansionPanel(value="contour", title="Contour Settings"):
                        with vuetify.VExpansionPanelText():
                            self._build_actor_controls("contour")
                            self._build_contour_specific_controls()

            with layout.content:
                with vuetify.VContainer(fluid=True, classes="pa-0 fill-height"):
                    self.ui_view = vtk_widgets.VtkRemoteLocalView(
                        self.render_window,
                        ref="view",
                        mode=("view_mode", self.state.view_mode),
                    )
                    # Assign controller methods AFTER self.ui_view is created
                    self.ctrl.view_update = self.ui_view.update
                    self.ctrl.view_reset_camera = self.ui_view.reset_camera
                    self.ctrl.view_update_image = self.ui_view.update_image
                    self.ui_view.push_remote_camera_on_end_interaction()
                    self.ui_view.mounted = self.ctrl.view_reset_camera # Reset camera on mount

            return layout

    def _build_actor_controls(self, actor_prefix):
        vuetify.VSelect(
            label="Representation",
            v_model=(f"{actor_prefix}_representation",),
            items=("representation_options",),
            item_title="title",
            item_value="value",
            density="compact", hide_details=True, classes="my-2", outlined=True,
        )
        vuetify.VSelect(
            label="Color by",
            v_model=(f"{actor_prefix}_color_array_value",),
            items=("dataset_arrays",),
            item_title="title", # dataset_arrays has 'title' and 'value'
            item_value="value",
            density="compact", hide_details=True, classes="my-2", outlined=True,
        )
        vuetify.VSelect(
            label="Lookup table",
            v_model=(f"{actor_prefix}_color_preset",),
            items=("lut_options",),
            item_title="title",
            item_value="value",
            density="compact", hide_details=True, classes="my-2", outlined=True,
        )
        vuetify.VSlider(
            label="Opacity",
            v_model=(f"{actor_prefix}_opacity",),
            min=0, max=1, step=0.01,
            density="compact", hide_details=True, classes="my-2", thumb_label=True,
        )

    def _build_contour_specific_controls(self):
        vuetify.VSelect(
            label="Contour by",
            v_model=("contour_by_array_value",),
            items=("dataset_arrays",),
            item_title="title",
            item_value="value",
            density="compact", hide_details=True, classes="my-2", outlined=True,
        )
        vuetify.VSlider(
            label="Contour value",
            v_model=("contour_value",),
            min=("contour_min",),
            max=("contour_max",),
            step=("contour_step",),
            density="compact", hide_details=True, classes="my-2", thumb_label=True,
        )

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main(**kwargs):
    server = get_server(client_type="vue3")
    app = MultiFilterApp(server, **kwargs)
    server.start()

if __name__ == "__main__":
    main()
