#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame",
#     "trame-vuetify",
#     "trame-vtk",
# ]
# ///
# -----------------------------------------------------------------------------
# Trame VTK Remote Rendering Cone (RemoteRendering)
#
# This example demonstrates a basic VTK application with remote rendering.
# It showcases how to create a simple VTK pipeline, manage application state,
# and build a user interface with Trame.
#
# **Key Features:**
#
# - **Remote Rendering:** The VTK rendering happens on the server-side.
# - **State Management:** The cone's resolution is managed as a reactive state variable.
# - **UI Components:** A slider controls the resolution, and a `VtkRemoteView` displays the rendered image.
# - **Class-based Structure:** The application is organized into a class for better structure and reusability.
# - **Custom Event Handling:** Includes a commented-out implementation for advanced, full-payload event handling.
#
# ---
#
# ## Running the Application
#
# ### If `uv` is available:
#
# ```bash
# # Run directly
# ./vtk/01_SimpleCone/RemoteRendering.py
#
# # or
# uv run ./vtk/01_SimpleCone/RemoteRendering.py
# ```
#
# ### Required Packages
#
# If `uv` is not available, you can install the required packages manually:
#
# ```bash
# pip install trame trame-vuetify trame-vtk
# ```
#
# ### Running as a Desktop or Web Application
#
# ```bash
# # Run as a Web Application (default)
# python ./vtk/01_SimpleCone/RemoteRendering.py --server
#
# # Run as a Desktop Application
# python ./vtk/01_SimpleCone/RemoteRendering.py --app
# ```
#
# ### Running in Jupyter Lab / Notebook
#
# To run this example in a Jupyter environment, you need to rename the file
# to `RemoteRendering_app.py` and place it in the same directory as your notebook.
#
# Then, in a notebook cell, execute the following:
#
# ```python
# from RemoteRendering_app import RemoteRenderingApp
#
# app = RemoteRenderingApp()
# await app.ready
# app
# ```
# ---

import vtk

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, vtk as vtk_widgets


# -----------------------------------------------------------------------------
# VTK View event types for custom/advanced event handling
# -----------------------------------------------------------------------------
VTK_VIEW_EVENTS = [
    "StartAnimation",
    "Animation",
    "EndAnimation",
    "MouseEnter",
    "MouseLeave",
    "StartMouseMove",
    "MouseMove",
    "EndMouseMove",
    "LeftButtonPress",
    "LeftButtonRelease",
    "MiddleButtonPress",
    "MiddleButtonRelease",
    "RightButtonPress",
    "RightButtonRelease",
    "KeyPress",
    "KeyDown",
    "KeyUp",
    "StartMouseWheel",
    "MouseWheel",
    "EndMouseWheel",
    "StartPinch",
    "Pinch",
    "EndPinch",
    "StartPan",
    "Pan",
    "EndPan",
    "StartRotate",
    "Rotate",
    "EndRotate",
    "Button3D",
    "Move3D",
    "StartPointerLock",
    "EndPointerLock",
    "StartInteraction",
    "Interaction",
    "EndInteraction",
]


class RemoteRenderingApp(TrameApp):
    """A Trame application for demonstrating remote VTK rendering."""

    def __init__(self, server=None, **kwargs):
        super().__init__(server=server, client_type="vue3")

        # VTK pipeline
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)
        self.render_window_interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self.cone_source = vtk.vtkConeSource()
        self.mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()

        self.mapper.SetInputConnection(self.cone_source.GetOutputPort())
        self.actor.SetMapper(self.mapper)
        self.renderer.AddActor(self.actor)
        self.renderer.ResetCamera()
        self.render_window.Render()

        # Initialize state
        self._initialize_state()

        # Build UI
        self._build_ui()

        # Initial update
        self._on_resolution_change()

    def _initialize_state(self):
        """Initialize the application's state."""
        self.state.trame__title = "VTK Remote Rendering"
        self.state.resolution = 6

    @change("resolution")
    def _on_resolution_change(self, resolution=6, **kwargs):
        """Update the cone resolution and trigger a view update."""
        self.cone_source.SetResolution(resolution)
        self.ctrl.view_update()

    # def on_event(self, event_data, *args, **kwargs):
    #     """Handles VTK view events, expecting a dictionary with event details."""
    #     if not isinstance(event_data, dict):
    #         print(f"ERROR: Received unexpected event_data format: {type(event_data)}")
    #         print(f"  Data: {event_data}")
    #         if args:
    #             print(f"  Extra Args: {args}")
    #         if kwargs:
    #             print(f"  Extra Kwargs: {kwargs}")
    #         return
    # 
    #     event_type = event_data.get('type', 'UnknownEvent')
    #     print(f"VTK Event: {event_type}")
    # 
    #     # Log common event properties if they exist
    #     if 'position' in event_data:
    #         pos = event_data['position']
    #         print(f"  Position: X={pos.get('x', 'N/A')}, Y={pos.get('y', 'N/A')}, Z={pos.get('z', 'N/A')}")
    #     if 'key' in event_data:
    #         print(f"  Key: '{event_data['key']}'")
    #     if 'keyCode' in event_data:
    #         print(f"  KeyCode: {event_data['keyCode']}")
    #     # Modifier keys are often present
    #     modifiers = []
    #     if event_data.get('controlKey'):
    #         modifiers.append("Ctrl")
    #     if event_data.get('altKey'):
    #         modifiers.append("Alt")
    #     if event_data.get('shiftKey'):
    #         modifiers.append("Shift")
    #     if modifiers:
    #         print(f"  Modifiers: {', '.join(modifiers)}")
    # 
    #     # Example: Custom logic for LeftButtonPress
    #     if event_type == "LeftButtonPress":
    #         print("  >>> Custom action for LeftButtonPress! Cone resolution might change.")
    #         # Example: Change cone resolution on left click
    #         # current_res = self.cone_source.GetResolution()
    #         # self.state.resolution = (current_res + 1) % 20 + 3 # Cycle resolution 3-22
    # 
    #     # For very detailed logging of all event data, uncomment the following:
    #     # print("  Full Event Data:")
    #     # for key, value in event_data.items():
    #     #     print(f"    {key}: {value}")
    # 
    #     if args:
    #         print(f"  (Received unexpected extra positional args: {args})")
    #     if kwargs:
    #         print(f"  (Received unexpected extra keyword args: {kwargs})")
    # 
    # def _event_listeners(self, events):
    #     """Helper function to create event listeners for VTK view."""
    #     result = {}
    #     for event_name in events:
    #         # The string "[utils.vtk.event($event)]" will be evaluated on the client.
    #         # It assumes a 'utils.vtk.event' function is available in the client scope.
    #         result[event_name] = (self.on_event, "[utils.vtk.event($event)]") # User suggestion
    #     return result

    def _build_ui(self):
        """Build the user interface."""
        with SinglePageLayout(self.server, full_height=True) as layout:
            layout.title.set_text("Cone Application")

            with layout.toolbar:
                vuetify3.VSpacer()
                vuetify3.VSlider(
                    v_model=("resolution", self.state.resolution),
                    min=3,
                    max=60,
                    step=1,
                    hide_details=True,
                    dense=True,
                    thumb_label=True,
                    style="max-width: 300px;",
                )


            with layout.content:
                with vuetify3.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                ):
                    # For advanced event handling, uncomment the following lines:
                    #
                    # This enables a list of VTK view events to be monitored and passed
                    # from the client to the server-side Python callback.
                    # The `interactor_events` prop specifies which events to listen for,
                    # and `**self._event_listeners` maps them to the `on_event` method,
                    # which receives the full event payload.
                    view = vtk_widgets.VtkRemoteView(
                        self.render_window,
                        # interactor_events=("event_types", VTK_VIEW_EVENTS),
                        # **self._event_listeners(VTK_VIEW_EVENTS),
                    )
                    self.ctrl.view_update = view.update




def main():
    """Create and start the Trame application."""
    app = RemoteRenderingApp()
    app.server.start()


if __name__ == "__main__":
    main()
