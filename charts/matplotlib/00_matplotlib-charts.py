# /// script
# requires = [
#     "trame",
#     "trame-vuetify3",
#     "trame-matplotlib",
#     "matplotlib",
#     "numpy",
# ]
# ///
#
# -----------------------------------------------------------------------------
# Trame-Vuetify3 Matplotlib Chart Viewer
# --------------------------------------
#
# This example demonstrates how to use Matplotlib to create charts in a Trame
# application. It features a dropdown menu to switch between several different
# Matplotlib plots.
#
# The application is structured as a class, `MatplotlibApp`, which inherits
# from `trame.app.TrameApp`. The UI is built using `trame.ui.vuetify3`.
#
# A `trame.SizeObserver` is used to make the Matplotlib figure responsive
# to the size of the browser window, and the DPI is adjusted for crisp
# rendering on high-DPI (Retina) displays.
#
# Running if uv is available:
#   uv run ./00_matplotlib-charts.py
#   or ./00_matplotlib-charts.py
#
# Required Packages:
#   (Handled by the /// pyproject block above if using uv run)
#   pip install "trame[app]" trame-vuetify trame-matplotlib matplotlib numpy
#
# Run as a Desktop Application:
#   python 00_matplotlib-charts.py --app
#
# Run in Jupyter Lab / Notebook:
#   Rename and make sure this script ('00_matplotlib-charts.py' to 'matplotlib_charts.py') is renamed and in the same
#   directory as your notebook, or in a directory included in Python's path.
#   Then, in a cell, execute:
#
#   from matplotlib_charts import MatplotlibApp
#   app = MatplotlibApp()
#   app.server.show()
#
# Run as a Web Application (default):
#   python 00_matplotlib-charts.py --server

import matplotlib.pyplot as plt
import numpy as np

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, trame
from trame.widgets.matplotlib import Figure as MatplotlibFigure


class MatplotlibApp(TrameApp):
    def __init__(self, server_name="MatplotlibApp"):
        super().__init__(server_name)
        self._initialize_state()
        self._build_ui()
        if self.state.active_figure:
             self._update_chart(self.state.active_figure)

    def _initialize_state(self):
        self.state.trame__title = "Matplotlib Viewer"
        self.state.figures = [
            {"title": "First Demo", "value": "FirstDemo"},
            {"title": "Subplots", "value": "Subplots"},
            {"title": "Multi Lines", "value": "MultiLines"},
            {"title": "Dots and Points", "value": "DotsAndPoints"},
            {"title": "Moving Window Average", "value": "MovingWindowAverage"},
        ]
        self.state.active_figure = self.state.figures[0]["value"]


    # -----------------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------------
    def _build_ui(self):
        with SinglePageLayout(self.server) as layout:
            layout.title.set_text(self.state.trame__title)

            with layout.toolbar:
                vuetify3.VSpacer()
                vuetify3.VSelect(
                    v_model=("active_figure", self.state.active_figure),
                    items=("figures", self.state.figures),
                    item_title="title",
                    item_value="value",
                    hide_details=True,
                    density="compact",
                    style="max-width: 300px;",
                )

            with layout.content:
                with vuetify3.VContainer(fluid=True, classes="fill-height pa-0 ma-0"):
                    with trame.SizeObserver("figure_size"):
                        html_figure = MatplotlibFigure(style="position: absolute; width: 100%; height: 100%;")
                        self.ctrl.update_figure = html_figure.update

   # -----------------------------------------------------------------------------
    # Resize Handler
    # -----------------------------------------------------------------------------
    def figure_size(self):
        if self.state.figure_size is None:
            return {}
        pixelRatio = self.state.figure_size.get("pixelRatio")
        if pixelRatio > 1:
            pixelRatio = 2
        dpi = self.state.figure_size.get("dpi")
        rect = self.state.figure_size.get("size")
        w_inch = rect.get("width") / (pixelRatio*dpi)
        h_inch = rect.get("height") / (pixelRatio*dpi)
        return {
            "figsize": (w_inch, h_inch),
            "dpi": dpi,
        }

    # -----------------------------------------------------------------------------
    # Plotting Methods
    # -----------------------------------------------------------------------------
    def FirstDemo(self):
        plt.close("all")
        fig, ax = plt.subplots(**self.figure_size())
        np.random.seed(0)
        ax.plot(
            np.random.normal(size=100), np.random.normal(size=100), "or", ms=10, alpha=0.3
        )
        ax.plot(
            np.random.normal(size=100), np.random.normal(size=100), "ob", ms=20, alpha=0.1
        )
        ax.set_xlabel("this is x")
        ax.set_ylabel("this is y")
        ax.set_title("Matplotlib Plot Rendered in Trame!", size=14)
        ax.grid(color="lightgray", alpha=0.7)
        return fig

    def MultiLines(self):
        plt.close("all")
        fig, ax = plt.subplots(**self.figure_size())
        x = np.linspace(0, 10, 1000)
        for offset in np.linspace(0, 3, 7):
            ax.plot(x, 0.9 * np.sin(x - offset), lw=5, alpha=0.4)
        ax.set_ylim(-1.2, 1.0)
        ax.text(5, -1.1, "Here are some curves", size=18)
        ax.grid(color="lightgray", alpha=0.7)
        return fig

    def DotsAndPoints(self):
        plt.close("all")
        fig, ax = plt.subplots(**self.figure_size())
        ax.plot(
            np.random.rand(20),
            "-o",
            alpha=0.5,
            color="black",
            linewidth=5,
            markerfacecolor="green",
            markeredgecolor="lightgreen",
            markersize=20,
            markeredgewidth=10,
        )
        ax.grid(True, color="#EEEEEE", linestyle="solid")
        ax.set_xlim(-2, 22)
        ax.set_ylim(-0.1, 1.1)
        return fig

    def MovingWindowAverage(self):
        np.random.seed(0)
        t = np.linspace(0, 10, 300)
        x = np.sin(t)
        dx = np.random.normal(0, 0.3, 300)
        kernel = np.ones(25) / 25.0
        x_smooth = np.convolve(x + dx, kernel, mode="same")
        plt.close("all")
        fig, ax = plt.subplots(**self.figure_size())
        ax.plot(t, x + dx, linestyle="", marker="o", color="black", markersize=3, alpha=0.3)
        ax.plot(t, x_smooth, "-k", lw=3)
        ax.plot(t, x, "--", lw=3, color="blue")
        return fig

    def Subplots(self):
        plt.close("all")
        fig = plt.figure(**self.figure_size())
        fig.subplots_adjust(hspace=0.3)
        np.random.seed(0)
        for i in range(1, 5):
            ax = fig.add_subplot(2, 2, i)
            color = np.random.random(3)
            ax.plot(np.random.random(30), lw=2, c=color)
            ax.set_title("RGB = ({0:.2f}, {1:.2f}, {2:.2f})".format(*color), size=14)
            ax.grid(color="lightgray", alpha=0.7)
        return fig

    # -----------------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------------
    @change("active_figure", "figure_size")
    def _update_chart(self, active_figure, **kwargs):
        if not active_figure: # active_figure might be None initially or if state is cleared
            return

        method_name = active_figure
        if hasattr(self, method_name) and callable(getattr(self, method_name)):
            plot_method = getattr(self, method_name)
            fig = plot_method()
            if hasattr(self.ctrl, 'update_figure') and self.ctrl.update_figure:
                 self.ctrl.update_figure(fig)
        else:
            print(f"Error: Plotting method {method_name} not found for active_figure='{active_figure}'")

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = MatplotlibApp()
    app.server.start()
