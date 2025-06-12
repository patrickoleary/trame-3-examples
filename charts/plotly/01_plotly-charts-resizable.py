#!/usr/bin/env -S uv run --script
# requires-python = ">=3.10"
# dependencies = [
#     "trame[app]",
#     "trame-vuetify",
#     "trame-plotly",
#     "plotly",
#     "pandas",
# ]
# ///
# -----------------------------------------------------------------------------
# Trame Plotly Chart Resizable Example
#
# This example demonstrates how to create resizable Plotly charts.
# Two charts are displayed side-by-side and will adjust their size
# automatically when the browser window or their container is resized,
# leveraging Vuetify 3's responsive layout capabilities.
#
# Running if uv is available
#   uv run ./01_plotly-charts-resizable.py
#   or ./01_plotly-charts-resizable.py
#
# Required Packages:
#   (Handled by the script block above if using uv run)
#   pip install "trame[app]" trame-vuetify trame-plotly plotly pandas
#
# Run as a Desktop Application:
#   python 01_plotly-charts-resizable.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('plotly_resizable_example.py') is in the same 
#   directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from plotly_resizable_example import PlotlyResizableApp
#   app = PlotlyResizableApp()
#   app.server.show()
#
# Run as a Web Application (default):
#   python 01_plotly-charts-resizable.py --server
# -----------------------------------------------------------------------------
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "plotly",
#     "trame-plotly",
#     "trame-vuetify",
#     "trame[app]",
# ]
# ///
# -----------------------------------------------------------------------------
from trame.app import TrameApp
from trame.decorators import change, TrameApp as TrameAppDecorator
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, plotly

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Data for new charts from trame-plotly example
contour_raw_data = pd.read_json(
    "https://raw.githubusercontent.com/plotly/datasets/master/contour_data.json"
)
polar_data = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/polar_dataset.csv"
)

# Helper function from trame-plotly example
def clean_data(data_in):
    """
    Cleans data in a format which can be conveniently
    used for drawing traces. Takes a dictionary as the
    input, and returns a list in the following format:

    input = {'key': ['a b c']}
    output = [key, [a, b, c]]
    """
    key = list(data_in.keys())[0]
    data_out = [key]
    for i in data_in[key]:
        data_out.append(list(map(float, i.split(" "))))
    return data_out

# Chart creation functions from trame-plotly example
def create_ternary_fig(**kwargs):
    contour_dict = contour_raw_data["Data"]
    colors = [
        "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
        "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",
    ]
    colors_iterator = iter(colors)
    fig = go.Figure()
    for raw_data in contour_dict:
        data = clean_data(raw_data)
        a = [inner_data[0] for inner_data in data[1:]]
        a.append(data[1][0])  # Closing the loop
        b = [inner_data[1] for inner_data in data[1:]]
        b.append(data[1][1])  # Closing the loop
        c = [inner_data[2] for inner_data in data[1:]]
        c.append(data[1][2])  # Closing the loop
        fig.add_trace(
            go.Scatterternary(
                text=data[0], a=a, b=b, c=c, mode="lines",
                line=dict(color="#444", shape="spline"),
                fill="toself", fillcolor=colors_iterator.__next__(),
            )
        )
    fig.update_layout(margin=dict(l=50, r=50, t=50, b=50), title_text="Ternary Chart")
    return fig

def create_polar_fig(**kwargs):
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=polar_data["x1"].tolist(), theta=polar_data["y"].tolist(),
            mode="lines", name="Figure 8", line_color="peru",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=polar_data["x2"].tolist(), theta=polar_data["y"].tolist(),
            mode="lines", name="Cardioid", line_color="darkviolet",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=polar_data["x3"].tolist(), theta=polar_data["y"].tolist(),
            mode="lines", name="Hypercardioid", line_color="deepskyblue",
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=False, title_text="Polar Chart")
    return fig

# -----------------------------------------------------------------------------
# Trame Application
# -----------------------------------------------------------------------------

class PlotlyResizableApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)
        self._build_ui()

    def _build_ui(self):
        with SinglePageLayout(self.server, full_height=True) as self.ui:
            self.ui.title.set_text("Trame Resizable Plotly Charts")
            self.ui.icon.hide()

            with self.ui.content:
                with vuetify3.VContainer(fluid=True, classes="fill-height pa-0 ma-0"):
                    with vuetify3.VRow(classes="fill-height", no_gutters=True):
                        with vuetify3.VCol(cols=6, classes="d-flex flex-column pa-1", style="height: 100%"):
                            plotly.Figure(
                                figure=create_polar_fig(),
                                display_mode_bar=False,
                                style="width: 100%; height: 100%;"
                            )

                        with vuetify3.VCol(cols=6, classes="d-flex flex-column pa-1", style="height: 100%"):
                            plotly.Figure(
                                figure=create_ternary_fig(),
                                display_mode_bar=False,
                                style="width: 100%; height: 100%;"
                            )

# -----------------------------------------------------------------------------
# Main logic
# -----------------------------------------------------------------------------

def main(**kwargs):
    app = PlotlyResizableApp()
    app.server.start(**kwargs)

if __name__ == "__main__":
    main()