#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas",
#     "trame-vuetify",
#     "trame[app]",
# ]
# ///

import pandas as pd

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import html, vuetify3

# -----------------------------------------------------------------------------
# Data Definition
# -----------------------------------------------------------------------------

DATA = [
    {
        "name": "Frozen Yogurt",
        "calories": 200,
        "fat": 6,
        "carbs": 24,
        "protein": 4,
        "iron": "1%",
        "glutenfree": True,
    },
    {
        "name": "Ice cream sandwich",
        "calories": 200,
        "fat": 9,
        "carbs": 37,
        "protein": 4.3,
        "iron": "1%",
        "glutenfree": False,
    },
    {
        "name": "Eclair",
        "calories": 300,
        "fat": 16,
        "carbs": 23,
        "protein": 6,
        "iron": "7%",
        "glutenfree": False,
    },
    {
        "name": "Cupcake",
        "calories": 300,
        "fat": 3.7,
        "carbs": 67,
        "protein": 4.3,
        "iron": "8%",
        "glutenfree": True,
    },
    {
        "name": "Gingerbread",
        "calories": 400,
        "fat": 16,
        "carbs": 49,
        "protein": 3.9,
        "iron": "16%",
        "glutenfree": True,
    },
    {
        "name": "Jelly bean",
        "calories": 400,
        "fat": 0,
        "carbs": 94,
        "protein": 0,
        "iron": "0%",
        "glutenfree": False,
    },
    {
        "name": "Lollipop",
        "calories": 400,
        "fat": 0.2,
        "carbs": 98,
        "protein": 0,
        "iron": "2%",
        "glutenfree": True,
    },
    {
        "name": "Honeycomb",
        "calories": 400,
        "fat": 3.2,
        "carbs": 87,
        "protein": 6.5,
        "iron": "45%",
        "glutenfree": True,
    },
    {
        "name": "Donut",
        "calories": 500,
        "fat": 25,
        "carbs": 51,
        "protein": 4.9,
        "iron": "22%",
        "glutenfree": True,
    },
    {
        "name": "KitKat",
        "calories": 500,
        "fat": 26,
        "carbs": 65,
        "protein": 7,
        "iron": "6%",
        "glutenfree": True,
    },
]

# -----------------------------------------------------------------------------
# Trame Application
# -----------------------------------------------------------------------------

class DataFrameTableApp(TrameApp):
    def __init__(self, server_name=None, **kwargs):
        super().__init__(server_name, client_type="vue3", **kwargs)
        self._ui = None
        self.frame = pd.DataFrame.from_dict(DATA)
        self._initialize_state()
        self._build_ui()

    def _initialize_state(self):
        # Configure table columns and options
        headers = [
            {"key": "name", "title": "Dessert", "align": "start", "sortable": False},
            {"key": "calories", "title": "Calories"},
            {"key": "fat", "title": "Fat (g)"},
            {"key": "carbs", "title": "Carbs (g)"},
            {"key": "protein", "title": "Protein (g)"},
            {"key": "iron", "title": "Iron (%)"},
            {"key": "glutenfree", "title": "Gluten-Free"},
        ]
        df_headers_from_util, rows_from_util = vuetify3.dataframe_to_grid(self.frame)

        self.state.group_by = [{"key": "glutenfree", "order": "asc"}]
        self.state.headers = headers # Using manually defined headers
        self.state.rows = rows_from_util
        self.state.items_per_page = 10 # Define items_per_page in state
        self.state.items_per_page_options_list = [
            {"value": 10, "title": "10"},
            {"value": 25, "title": "25"},
            {"value": 50, "title": "50"},
            {"value": -1, "title": "All"}
        ]
        self.state.query = ""

    @change("rows")
    def _handle_row_change(self, rows, **kwargs):
        # This is an example of a reactive function. 
        # You can add logic here if needed when rows change.
        # print(f"Rows updated. Total rows: {len(rows)}")
        pass

    def _build_ui(self):
        with SinglePageLayout(self.server, full_height=True) as self._ui:
            self._ui.title.set_text("Vuetify Table")

            with self._ui.toolbar:
                vuetify3.VSpacer()
                vuetify3.VTextField(
                    v_model=("query",),  # Bind to self.state.query
                    placeholder="Search",
                    dense=True,
                    hide_details=True,
                    clearable=True,
                    classes="ma-2",
                )

            with self._ui.content:
                table_config = {
                    "group_by": ("group_by",),
                    "headers": ("headers",),      # Bind to self.state.headers
                    "items": ("rows",),          # Bind to self.state.rows
                    "item_value": "name",        # Required for VDataTable with objects. Ensures 'name' is a unique key in each item.
                    "search": ("query",),        # Bind to self.state.query
                    "classes": "elevation-1 ma-4",
                    "multi_sort": True,
                    "dense": True,
                    "items_per_page": ("items_per_page",), # Bind to state variable
                    "items_per_page_options": ("items_per_page_options_list",), # Bind to state variable
                    "show_select": True, # Example: add checkboxes
                    "v_model:selected": ("selected_items", []), # Store selected items
                }
                with vuetify3.VDataTable(**table_config):
                    # All custom templates removed for debugging.
                    # The table will use default rendering for all cells.
                    pass

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main(**kwargs):
    app = DataFrameTableApp()
    app.server.start(**kwargs)

if __name__ == "__main__":
    main()
