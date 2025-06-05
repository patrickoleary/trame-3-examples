#!/usr/bin/env -S uv run --script
# -----------------------------------------------------------------------------
# Trame Deck.gl and Vega Uber Pickups Demo (Trame 3 / Vue 3)
#
# This example visualizes Uber pickup data in New York City using Deck.gl for
# hexagonal heatmaps and Vega (via Altair) for a histogram of pickups by minute.
# It demonstrates how to integrate these libraries within a Trame 3 application
# with a Vue 3 frontend, following modern coding practices.
#
# Running if uv is available:
#   uv run ./01_uber-nyc-pickups.py
#   or ./01_uber-nyc-pickups.py
#
# Required Packages:
#   (Handled by the /// script block below if using uv run)
#   pip install "trame[app]" trame-vuetify trame-deckgl trame-vega altair==5.1.2 pandas pydeck numpy
#
# To run as a Desktop Application:
#   python 01_uber-nyc-pickups.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('uber_    nyc_pickups.py') is in the same 
#   directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from uber_nyc_pickups import UberPickupsApp
#   app = UberPickupsApp()
#   app.server.show()
#
# To run as a Web Application (default):
#   python 01_uber-nyc-pickups.py --server
#
# IMPORTANT: Set your MAPBOX_API_KEY environment variable for the maps to render.
# Example: export MAPBOX_API_KEY="your_actual_mapbox_api_key_here"
# -----------------------------------------------------------------------------
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "pydeck",
#     "numpy",
#     "altair==5.1.2",
#     "trame-deckgl",
#     "trame-vega",
#     "trame-vuetify",
#     "trame[app]",
# ]
# ///
# -----------------------------------------------------------------------------

import os
import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import deckgl, vega, vuetify3, html

# -----------------------------------------------------------------------------
# Constants and Data Loading
# -----------------------------------------------------------------------------
DATE_TIME = "date/time"
DATA_URL = (
    "http://s3-us-west-2.amazonaws.com/streamlit-demo-data/uber-raw-data-sep14.csv.gz"
)
DEFAULT_PICKUP_HOUR = 10 # A common default hour

def lowercase(x):
    return str(x).lower()

def load_data(nrows):
    try:
        data = pd.read_csv(DATA_URL, nrows=nrows)
        data.rename(lowercase, axis="columns", inplace=True)
        data[DATE_TIME] = pd.to_datetime(data[DATE_TIME])
        return data
    except Exception as e:
        print(f"Error loading data from {DATA_URL}: {e}")
        # Return an empty DataFrame with expected columns to prevent downstream errors
        return pd.DataFrame(columns=['lat', 'lon', DATE_TIME])

# -----------------------------------------------------------------------------
# Trame Application
# -----------------------------------------------------------------------------

class UberPickupsApp(TrameApp):
    def __init__(self, server_name=None):
        super().__init__(server_name, client_type="vue3")
        self.state.pickupHour = DEFAULT_PICKUP_HOUR
        self.state.loading = True
        self._data_cache = load_data(100000) # Load data once
        if self._data_cache.empty:
            print("Warning: Data cache is empty. Check data loading.")

        # Calculate initial lat/lon for NYC map if data is available
        initial_nyc_lat = np.average(self._data_cache["lat"]) if not self._data_cache.empty and "lat" in self._data_cache else 40.730610
        initial_nyc_lon = np.average(self._data_cache["lon"]) if not self._data_cache.empty and "lon" in self._data_cache else -73.935242

        self.map_definitions = [
            {
                "id": "nyc", "title_key": "nycTitle", "widget_name": "_deck_nyc",
                "lat": initial_nyc_lat, "lon": initial_nyc_lon,
                "zoom": 10, "static_title": "New York City - Pickups"
            },
            {
                "id": "jfk", "title_key": "jfkTitle", "widget_name": "_deck_jfk",
                "lat": 40.6413, "lon": -73.7781, "zoom": 11, "static_title": "JFK Airport"
            },
            {
                "id": "lga", "title_key": "lgaTitle", "widget_name": "_deck_lga",
                "lat": 40.7769, "lon": -73.8740, "zoom": 12, "static_title": "LaGuardia Airport"
            },
            {
                "id": "nwk", "title_key": "nwkTitle", "widget_name": "_deck_nwk",
                "lat": 40.6895, "lon": -74.1745, "zoom": 11, "static_title": "Newark Airport"
            },
        ]

        # Initialize widget references and state for titles
        for map_def in self.map_definitions:
            setattr(self, map_def["widget_name"], None)
            self.state[map_def["title_key"]] = map_def["static_title"]
        self._hour_histogram = None
        self.state.chartTitle = ""
        self.state.mapboxApiKey = os.environ.get("MAPBOX_API_KEY")

        if not self.state.mapboxApiKey:
            print("WARNING: MAPBOX_API_KEY environment variable not set. Maps may not render correctly.")
            print("Please set it and restart the application. You can get a free key from https://www.mapbox.com/")

        self._build_ui()
        self.update_data_and_plots() # Initial data processing and plot rendering
        self.state.loading = False

    @change("pickupHour")
    def update_data_and_plots(self, pickupHour=None, **kwargs):
        self.state.loading = True
        if pickupHour is None:
            pickupHour = int(self.state.pickupHour)
        else:
            pickupHour = int(pickupHour)

        current_hour_display = f"{pickupHour:02d}:00 - {pickupHour:02d}:59"
        self.state.chartTitle = f"Pickups per minute for {current_hour_display}"

        # Filter data by hour selected
        if self._data_cache.empty or DATE_TIME not in self._data_cache.columns:
            filtered_data_for_hour = pd.DataFrame(columns=['lat', 'lon', DATE_TIME])
        else:
            filtered_data_for_hour = self._data_cache[
                self._data_cache[DATE_TIME].dt.hour == pickupHour
            ]

        # Update all maps
        for map_def in self.map_definitions:
            deck_widget = getattr(self, map_def["widget_name"])
            if deck_widget:
                deck_config = pdk.Deck(
                    map_provider="mapbox",
                    map_style="mapbox://styles/mapbox/light-v9", # Use a default style
                    initial_view_state=pdk.ViewState(
                        latitude=map_def["lat"],
                        longitude=map_def["lon"],
                        zoom=map_def["zoom"],
                        pitch=50,
                    ),
                    layers=[
                        pdk.Layer(
                            "HexagonLayer",
                            data=filtered_data_for_hour if not filtered_data_for_hour.empty else pd.DataFrame(columns=['lon', 'lat']),
                            get_position=["lon", "lat"],
                            radius=100,
                            elevation_scale=4,
                            elevation_range=[0, 1000],
                            pickable=True,
                            extruded=True,
                            auto_highlight=True,
                        ),
                    ],
                    api_keys={"mapbox": self.state.mapboxApiKey} if self.state.mapboxApiKey else None,
                    tooltip={"html": "<b>Pickups:</b> {elevationValue}", "style": {"color": "white", "backgroundColor": "rgba(0,0,0,0.7)"}}
                )
                deck_widget.update(deck_config)
                if map_def["id"] == "nyc":
                    self.state[map_def["title_key"]] = f"{map_def['static_title']} ({current_hour_display})"
                else:
                    self.state[map_def["title_key"]] = map_def['static_title']

        # Update histogram
        if self._hour_histogram:
            if not filtered_data_for_hour.empty and DATE_TIME in filtered_data_for_hour.columns:
                hist_data = np.histogram(
                    filtered_data_for_hour[DATE_TIME].dt.minute, bins=60, range=(0, 59) # range up to 59 for 60 bins
                )[0]
            else:
                hist_data = np.zeros(60)
            
            chart_data = pd.DataFrame({"minute": range(60), "pickups": hist_data})

            altair_chart = (
                alt.Chart(chart_data)
                .mark_area(interpolate="step-after", color="#1E88E5", line=True)
                .encode(
                    x=alt.X("minute:Q", scale=alt.Scale(nice=False), title="Minute of the Hour"),
                    y=alt.Y("pickups:Q", title="Number of Pickups"),
                    tooltip=[
                        alt.Tooltip("minute:Q", title="Minute"),
                        alt.Tooltip("pickups:Q", title="Pickups"),
                    ],
                )
                .properties(title=self.state.chartTitle, width="container", height=150)
            ).configure_axis(grid=False).configure_view(strokeWidth=0).configure_title(fontSize=14, anchor='middle')
            self._hour_histogram.update(altair_chart)
        self.state.loading = False

    def _build_ui(self):
        # Simplified card properties - remove complex flex styling for now
        card_props = {"elevation": 2, "rounded": "lg", "class_": "ma-1"} 
        card_text_props = {"class_": "pa-1", "style": "overflow: hidden;"} # Basic padding, ensure content fits
        
        NYC_map_deck_style = "width: 100%; height: 100%; min-height: 40vh; border-radius: inherit;"
        map_deck_style = "width: 100%; height: 100%; min-height: 10.0vh; border-radius: inherit;"
        # Altair chart height is 200px, set in update_data_and_plots

        with SinglePageLayout(self.server, full_height=True) as self.ui:
            self.ui.title.set_text("NYC Uber Pickups Explorer")
            with self.ui.toolbar:
                vuetify3.VProgressLinear(
                    indeterminate=True, absolute=True, bottom=True,
                    active=("loading", False), color="primary_accent"
                )
                vuetify3.VSpacer()
                html.Div("Hour: {{ pickupHour.toString().padStart(2, '0') }}:00", classes="text-subtitle-1 mr-4 align-self-center")

            with self.ui.content:
                # VContainer for the map grid
                with vuetify3.VContainer(fluid=True, classes="pa-1 ma-0"):
                    # --- ROW 1: JFK (left) | NYC (right) ---
                    with vuetify3.VRow(no_gutters=True, classes="flex-shrink-0"):
                        # COL 1.2: Other Maps
                        with vuetify3.VCol(cols=6, classes="pa-1"):
                            # ROW 1.2.1: JFK Map
                            with vuetify3.VRow(no_gutters=True, classes="flex-shrink-0"):
                                with vuetify3.VCol(cols=12, classes="pa-1"):
                                    map_jfk_def = next(m for m in self.map_definitions if m["id"] == "jfk")
                                    with vuetify3.VCard():
                                        vuetify3.VCardTitle(f"{{{{ {map_jfk_def['title_key']} }}}}", classes="py-1 text-caption")
                                        with vuetify3.VCardText():
                                            setattr(self, map_jfk_def["widget_name"], deckgl.Deck(
                                            mapbox_api_key=self.state.mapboxApiKey,
                                            style=map_deck_style,
                                        ))
                            # ROW 1.2.2: Newark Map
                            with vuetify3.VRow(no_gutters=True, classes="flex-shrink-0"):
                                with vuetify3.VCol(cols=12, classes="pa-1"):
                                    map_nwk_def = next(m for m in self.map_definitions if m["id"] == "nwk")
                                    with vuetify3.VCard():
                                        vuetify3.VCardTitle(f"{{{{ {map_nwk_def['title_key']} }}}}", classes="py-1 text-caption")
                                        with vuetify3.VCardText():
                                            setattr(self, map_nwk_def["widget_name"], deckgl.Deck(
                                            mapbox_api_key=self.state.mapboxApiKey,
                                            style=map_deck_style,
                                        ))
                            # ROW 1.2.3: LaGuardia Map
                            with vuetify3.VRow(no_gutters=True, classes="flex-shrink-0"):
                                with vuetify3.VCol(cols=12,classes="pa-1"):
                                    map_lga_def = next(m for m in self.map_definitions if m["id"] == "lga")
                                    with vuetify3.VCard():
                                        vuetify3.VCardTitle(f"{{{{ {map_lga_def['title_key']} }}}}", classes="py-1 text-caption")
                                        with vuetify3.VCardText():
                                            setattr(self, map_lga_def["widget_name"], deckgl.Deck(
                                            mapbox_api_key=self.state.mapboxApiKey,
                                            style=map_deck_style,
                                        ))
                        # COL 1.1: NYC Map
                        with vuetify3.VCol(cols=6, classes="pa-1"):
                            map_nyc_def = next(m for m in self.map_definitions if m["id"] == "nyc")
                            with vuetify3.VCard():
                                vuetify3.VCardTitle(f"{{{{ {map_nyc_def['title_key']} }}}}", classes="py-2 text-subtitle-1")
                                with vuetify3.VCardText():
                                    setattr(self, map_nyc_def["widget_name"], deckgl.Deck(
                                        mapbox_api_key=self.state.mapboxApiKey,
                                        style=NYC_map_deck_style,
                                    ))
                # New html.Div for Histogram and Slider, directly under self.ui.content (sibling to VContainer above)
                with html.Div(classes="pa-2"):
                    # Histogram
                    self._hour_histogram = vega.Figure(style="width: 100%; height: 150px;") # Altair chart height is 150px, width is container
                    
                    # Spacer - simple div for margin, or use Vuetify spacer if preferred in this context
                    html.Div(style="height: 16px;")

                    # Slider & Info Text
                    html.P(
                        "Examining how Uber pickups vary over time in New York City's and at its major regional airports. By sliding the slider on the left you can view different slices of time and explore different transportation trends.",
                        classes="text-body-2 mb-2",
                    )
                    if not self.state.mapboxApiKey:
                        vuetify3.VAlert(
                            text="MAPBOX_API_KEY is not set. Maps will not render. Please set the environment variable and restart.",
                            type="warning", density="compact", variant="tonal", closable=True, icon="mdi-alert-circle-outline",
                            class_="mb-2"
                        )
                    vuetify3.VSlider(
                        v_model_number=("pickupHour", DEFAULT_PICKUP_HOUR),
                        min=0, max=23, step=1, thumb_label="always",
                        density="compact", hide_details=True, color="primary",
                        track_color="grey-lighten-1", classes="align-self-center"
                    )

# -----------------------------------------------------------------------------
# Main logic
# -----------------------------------------------------------------------------

def main(**kwargs):
    app = UberPickupsApp()
    app.server.start(**kwargs)

if __name__ == "__main__":
    main()
