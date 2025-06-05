#!/usr/bin/env -S uv run --script
# -----------------------------------------------------------------------------
# Trame Deck.gl Mapping Demo
#
# Running if uv is available
#   uv run ./00_mapping-demo.py
#   or ./00_mapping-demo.py
#
# Required Packages:
#   pip install "trame[app]" trame-vuetify trame-deckgl pydeck pandas
#
# Run as a Desktop Application:
#   python 00_mapping-demo.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('mapping_demo.py') is in the same 
#   directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from mapping_demo import MappingDemoApp
#   app = MappingDemoApp()
#   app.server.show()
#
# Run as a Web Application (default):
#   python 00_mapping-demo.py --server
# -----------------------------------------------------------------------------
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "pydeck",
#     "trame-deckgl",
#     "trame-vuetify",
#     "trame[app]",
# ]
# ///
# -----------------------------------------------------------------------------

import os
import pandas as pd
import pydeck as pdk

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import deckgl, vuetify3

# -----------------------------------------------------------------------------
# Data and Layer Definitions
# -----------------------------------------------------------------------------

def from_data_file(filename):
    url = (
        "https://raw.githubusercontent.com/streamlit/"
        "example-data/master/hello/v1/%s" % filename
    )
    return pd.read_json(url)

ALL_LAYERS = {
    "Bike Rentals": pdk.Layer(
        "HexagonLayer",
        data=from_data_file("bike_rental_stats.json"),
        get_position=["lon", "lat"],
        radius=200,
        elevation_scale=4,
        elevation_range=[0, 1000],
        extruded=True,
    ),
    "Bart Stop Exits": pdk.Layer(
        "ScatterplotLayer",
        data=from_data_file("bart_stop_stats.json"),
        get_position=["lon", "lat"],
        get_fill_color=[200, 30, 0, 160],
        get_radius="[exits]",
        radius_scale=0.05,
    ),
    "Bart Stop Names": pdk.Layer(
        "TextLayer",
        data=from_data_file("bart_stop_stats.json"),
        get_position=["lon", "lat"],
        get_text="name",
        get_color=[0, 0, 0, 200],
        get_size=15,
        get_alignment_baseline="'bottom'",
    ),
    "Outbound Flow": pdk.Layer(
        "ArcLayer",
        data=from_data_file("bart_path_stats.json"),
        get_source_position=["lon", "lat"],
        get_target_position=["lon2", "lat2"],
        get_source_color=[200, 30, 0, 160],
        get_target_color=[200, 30, 0, 160],
        auto_highlight=True,
        width_scale=0.0001,
        get_width="outbound",
        width_min_pixels=3,
        width_max_pixels=30,
    ),
}

DEFAULT_LAYERS = [
    "Bike Rentals",
    "Bart Stop Exits",
    "Bart Stop Names",
    "Outbound Flow",
]

# -----------------------------------------------------------------------------
# Mapbox API Key Information
# -----------------------------------------------------------------------------
# By default, pydeck provides basemap tiles through Carto.
# You can optionally use a Mapbox API key.
# Set the MAPBOX_API_KEY environment variable with your token.
# For more info:
# [1] https://account.mapbox.com/auth/signup/
# [2] https://account.mapbox.com/access-tokens/
# [3] https://docs.mapbox.com/help/how-mapbox-works/access-tokens/#how-access-tokens-work
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Trame Application
# -----------------------------------------------------------------------------

class MappingDemoApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")
        self.state.activeLayers = DEFAULT_LAYERS[:]  # Use a copy
        self._deck_widget = None  # To store the deck widget instance
        self._build_ui()
        self.update_map() # Initial map rendering

    @change("activeLayers")
    def update_map(self, activeLayers=None, **kwargs):
        if activeLayers is None: # Handle initial call from __init__
            activeLayers = self.state.activeLayers

        selected_layers = [
            layer
            for layer_name, layer in ALL_LAYERS.items()
            if layer_name in activeLayers
        ]

        if self._deck_widget:
            if selected_layers:
                deck = pdk.Deck(
                    map_provider="mapbox",
                    map_style="mapbox://styles/mapbox/light-v9", # or another style
                    initial_view_state={
                        "latitude": 37.76,
                        "longitude": -122.4,
                        "zoom": 11,
                        "pitch": 50,
                    },
                    layers=selected_layers,
                    # tooltip=True # Optional: enable default tooltip
                )
                self._deck_widget.update(deck)
            else:
                # Clear the map or show a placeholder if no layers are selected
                # For simplicity, we'll update with an empty list of layers
                deck = pdk.Deck(
                    map_provider="mapbox",
                    map_style="mapbox://styles/mapbox/light-v9",
                    initial_view_state={
                        "latitude": 37.76,
                        "longitude": -122.4,
                        "zoom": 11,
                        "pitch": 50,
                    },
                    layers=[],
                )
                self._deck_widget.update(deck)
                print("No layers selected. Map cleared.")


    def _build_ui(self):
        with SinglePageLayout(self.server, full_height=True) as self.ui:
            self.ui.title.set_text("Trame Deck.gl Demo")
            self.ui.icon.hide()

            with self.ui.toolbar:
                vuetify3.VSpacer()
                vuetify3.VSelect(
                    v_model=("activeLayers",), # Binds to self.state.activeLayers
                    items=("available_layers", list(ALL_LAYERS.keys())),
                    label="Select Layers",
                    multiple=True,
                    chips=True,
                    dense=True,
                    hide_details=True,
                    density="compact",
                    style="max-width: 500px;", # Adjusted width
                    variant="outlined",
                    classes="mr-4",
                )


            with self.ui.content:
                self._deck_widget = deckgl.Deck(
                    mapbox_api_key=os.environ.get("MAPBOX_API_KEY"),
                    style="width: 100%; height: 100%;", # Ensure it fills content
                    classes="fill-height",
                )

# -----------------------------------------------------------------------------
# Main logic
# -----------------------------------------------------------------------------

def main(**kwargs):
    app = MappingDemoApp()
    app.server.start(**kwargs)

if __name__ == "__main__":
    main()
