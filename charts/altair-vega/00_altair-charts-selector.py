#!/usr/bin/env -S uv run --script
# /// pyproject
# [project]
# dependencies = [
#   "trame[app]",
#   "trame-vuetify",
#   "trame-vega",
#   "altair==5.1.2",
#   "vega_datasets",
# ]
# ///
# -----------------------------------------------------------------------------
# Trame Altair Charts Selector Demo (Trame 3 / Vue 3)
#
# This example demonstrates how to select and display various Altair charts
# within a Trame 3 application using a modern class-based structure.
# It highlights the use of `trame.widgets.vega.VegaEmbed` for rendering
# Altair charts and managing compatibility with Vega-Lite versions.
#
# Key features include:
# - Modern Trame 3 / Vue 3 class-based structure (`AltairChartsApp`).
# - Dynamic chart selection using `vuetify3.VSelect`.
# - Altair chart display via `trame.widgets.vega.VegaEmbed`.
# - Conversion of Altair charts to Vega-Lite specs (`.to_dict()`).
# - State management for active chart (`active_chart`) and options (`chart_options`).
# - Reactive updates with the `@change` decorator on `active_chart`.
# - Use of `altair==5.1.2` for compatibility with `trame-vega`'s bundled Vega-Lite renderer.
#
# Running if uv is available:
#   uv run ./00_altair-charts-selector.py
#   or ./00_altair-charts-selector.py
#
# Required Packages:
#   (Handled by the /// pyproject block above if using uv run)
#   pip install "trame[app]" trame-vuetify trame-vega altair==5.1.2 vega_datasets
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('00_altair-charts-selector.py' to 'altair_selector_app.py')
#   is in the same directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from altair_selector_app import AltairChartsApp
#   app = AltairChartsApp()
#   app.server.show()
#
# To run as a Web Application (default):
#   python ./00_altair-charts-selector.py
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# More examples available at https://altair-viz.github.io/gallery/
# -----------------------------------------------------------------------------

import altair as alt
from numpy import character
from vega_datasets import data

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vega as trame_vega, vuetify3

# -----------------------------------------------------------------------------
# Application class
# -----------------------------------------------------------------------------

class AltairChartsApp(TrameApp):
    def __init__(self, server_name="AltairChartsDemo"):
        super().__init__(server_name)
        self._initialize_state()
        self._build_ui()
        self.update_chart() # Initialize with the default chart

    def _initialize_state(self):
        self.state.trame__title = "Altair Charts Selector"
        self.state.chart_options = [
            {"title": "Scatter Matrix", "value": "ScatterMatrix"},
            {"title": "US Income By State", "value": "USIncomeByState"},
            {"title": "Stacked Density Estimates", "value": "StackedDensityEstimates"},
            {"title": "StreamGraph", "value": "StreamGraph"},
        ]
        self.state.active_chart = self.state.chart_options[0]["value"]

    def _build_ui(self):
        with SinglePageLayout(self.server) as layout:
            layout.title.set_text("Trame ❤️ Altair Charts")

            with layout.toolbar:
                vuetify3.VSpacer()
                vuetify3.VSelect(
                    v_model=("active_chart", self.state.active_chart),
                    items=("chart_options", self.state.chart_options),
                    item_title="title",
                    item_value="value",
                    dense=True,
                    hide_details=True,
                    style="max-width: 300px;",
                )

            with layout.content:
                with vuetify3.VContainer(fluid=True, classes="fill-height pa-0 ma-0 d-flex justify-center align-center"):
                    self.altair_figure = trame_vega.Figure(style="width: 100%; height: 100%;")
            return layout

    # -------------------------------------------------------------------------
    # Chart generation methods
    # -------------------------------------------------------------------------

    def ScatterMatrix(self):
        source = data.cars()
        chart = (
            alt.Chart(source)
            .mark_circle()
            .encode(
                alt.X(alt.repeat("column"), type="quantitative"),
                alt.Y(alt.repeat("row"), type="quantitative"),
                color="Origin:N",
            )
            .properties(width=200, height=200)
            .repeat(
                row=["Horsepower", "Acceleration", "Miles_per_Gallon"],
                column=["Miles_per_Gallon", "Acceleration", "Horsepower"],
            )
            .interactive()
        )
        self.altair_figure.update(chart)

    def USIncomeByState(self):
        states = alt.topo_feature(data.us_10m.url, "states")
        source = data.income.url
        chart = (
            alt.Chart(source)
            .mark_geoshape()
            .encode(
                shape="geo:G",
                color="pct:Q",
                tooltip=["name:N", "pct:Q"],
                facet=alt.Facet("group:N", columns=3),
            )
            .transform_lookup(
                lookup="id", from_=alt.LookupData(data=states, key="id"), as_="geo"
            )
            .properties(
                width=300,
                height=175,
            )
            .project(type="albersUsa")
        )
        self.altair_figure.update(chart)

    def StackedDensityEstimates(self): # Method provided even if not in default options
        source = data.iris()
        chart = (
            alt.Chart(source)
            .transform_fold(
                ["petalWidth", "petalLength", "sepalWidth", "sepalLength"],
                as_=["Measurement_type", "value"],
            )
            .transform_density(
                density="value",
                bandwidth=0.3,
                groupby=["Measurement_type"],
                extent=[0, 8],
                counts=True,
                steps=200,
            )
            .mark_area()
            .encode(
                alt.X("value:Q"),
                alt.Y("density:Q", stack="zero"),
                alt.Color("Measurement_type:N"),
            )
            .properties(
                width='container', 
                height='container'
            )
        )
        self.altair_figure.update(chart)

    def StreamGraph(self):
        source = data.unemployment_across_industries.url
        chart = (
            alt.Chart(source)
            .mark_area()
            .encode(
                alt.X(
                    "yearmonth(date):T",
                    axis=alt.Axis(format="%Y", domain=False, tickSize=0),
                ),
                alt.Y("sum(count):Q", stack="center", axis=None),
                alt.Color("series:N", scale=alt.Scale(scheme="category20b")),
            )
            .properties(
                width='container', 
                height='container'
            )
            .interactive()
        )
        self.altair_figure.update(chart)

    # -------------------------------------------------------------------------
    # Callbacks
    # -------------------------------------------------------------------------

    @change("active_chart")
    def update_chart(self, active_chart=None, **kwargs):
        current_chart_selection = active_chart if active_chart is not None else self.state.active_chart
        
        method_to_call = getattr(self, current_chart_selection, None)
        if method_to_call and callable(method_to_call):
            method_to_call()
        else:
            print(f"Error: Chart method '{current_chart_selection}' not found.")
            if hasattr(self, 'altair_figure') and self.altair_figure:
                self.altair_figure.update({}) # Clear spec on error

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main():
    app = AltairChartsApp()
    app.server.start()

if __name__ == "__main__":
    main()
