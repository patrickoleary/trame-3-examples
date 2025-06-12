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
# Trame Plotly Chart Selector
#
# Running if uv is available
#   uv run ./00_plotly-charts-selector.py
#   or ./00_plotly-charts-selector.py
#
# Required Packages:
#   (Handled by the script block above if using uv run)
#   pip install "trame[app]" trame-vuetify trame-plotly plotly pandas
#
# Run as a Desktop Application:
#   python 00_plotly-charts-selector.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('plotly_selector_example.py') is in the same 
#   directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from plotly_selector_example import PlotlyViewer
#   PlotlyViewer()
#
# Run as a Web Application (default):
#   python 00_plotly-charts-selector.py --server
#   # Access via the URLs provided in the console (e.g., http://localhost:8080)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, plotly

import plotly.express as px
import plotly.graph_objects as go

# Sample Plotly figures
SCATTER_MATRIX = px.scatter_matrix(
    px.data.iris(),
    dimensions=["sepal_width", "sepal_length", "petal_width", "petal_length"],
    color="species",
)
SCATTER_3D = px.scatter_3d(
    px.data.iris(),
    x="sepal_length",
    y="sepal_width",
    z="petal_width",
    color="petal_length",
    symbol="species",
)
BAR_CHART = go.Figure(
    data=[go.Bar(x=[1, 2, 3], y=[1, 3, 2])], layout_title_text="A Bar Chart"
)
CONTOUR_PLOT = go.Figure(
    data=[
        go.Contour(
            z=[
                [10, 10.625, 12.5, 15.625, 20],
                [5.625, 6.25, 8.125, 11.25, 15.625],
                [2.5, 3.125, 5.0, 8.125, 12.5],
                [0.625, 1.25, 3.125, 6.25, 10.625],
                [0, 0.625, 2.5, 5.625, 10],
            ]
        )
    ]
)
CONTOUR_PLOT.update_layout(title_text="Contour Plot")

PLOTS = {
    "Contour": CONTOUR_PLOT,
    "Scatter3D": SCATTER_3D,
    "ScatterMatrix": SCATTER_MATRIX,
    "BarChart": BAR_CHART,
}

# -----------------------------------------------------------------------------
# Trame Application
# -----------------------------------------------------------------------------

class PlotlyViewer(TrameApp):
    def __init__(self, server=None):       
        super().__init__(server, client_type="vue3") 
        self._build_ui()

    @change("active_plot_name")
    def update_plot_figure(self, active_plot_name, **_):
        figure_data = PLOTS.get(active_plot_name)
        if figure_data:
            self.ctx.plotly_display.update(figure_data)

    def _build_ui(self):
        with SinglePageLayout(self.server, full_height=True) as self.ui:
            self.ui.title.set_text("Trame ❤️ Plotly")
            self.ui.icon.hide()

            with self.ui.toolbar:
                vuetify3.VSpacer()
                vuetify3.VSelect(
                    v_model=("active_plot_name", "Contour"),
                    items=("plots", list(PLOTS.keys())),
                    hide_details=True,
                    density="compact",
                    style="max-width: 200px;",
                    variant="outlined",
                    classes="mr-4",
                )

            with self.ui.content:
                plotly.Figure(
                    ctx_name="plotly_display",
                    display_logo=False,
                    display_mode_bar=True,
                )
            
# -----------------------------------------------------------------------------
# Main logic
# -----------------------------------------------------------------------------

def main(**kwargs):
    app = PlotlyViewer() # Instantiate the class, passing the server
    app.server.start(**kwargs) # Start the specific server instance

if __name__ == "__main__":
    main()
