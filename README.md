# Trame 3+ Examples with Vuetify 3 and Vue 3

This repository showcases modern Trame application development using Trame 3+, Vue 3, and Vuetify 3. The examples demonstrate best practices, including the use of the `@TrameApp()` decorator and an inheritance-based application structure.

## Migrating from Trame 2 / Vue 2 / Vuetify 2

Moving to the latest versions of Trame, Vue, and Vuetify offers significant improvements in performance, features, and developer experience. Here are some key considerations:

*   **Trame 3+**: Leverages the latest Python features and provides a more streamlined API.
*   **Vue 3**: Introduces the Composition API, improved performance, and better TypeScript support.
*   **Vuetify 3**: A complete rewrite for Vue 3, offering enhanced components and customization options. It's available via the `trame-vuetify` package.

### Modern Application Structure: `@TrameApp()` and Inheritance

A recommended approach for structuring Trame 3 applications is to use the `@TrameApp("AppName")` decorator on a class that inherits from `trame.app.TrameApp`. This pattern promotes modularity and organization.

```python
from trame.app import get_server, TrameApp
from trame.ui.vuetify3 import VAppLayout # Or other UI components

@TrameApp()
class MyApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server)
        # Initialize your state, controllers, and UI here
        self.ui = self._build_ui()

    def _build_ui(self):
        with VAppLayout(self.server) as layout:
            # Define your layout and components
            # ...
            return layout

if __name__ == "__main__":
    app = MyApp()
    app.server.start()
```

## Examples

Below are the examples included in this repository. Each example demonstrates specific features or use cases of Trame.

---

### 1. Plotly Charts Selector

*   **Script:** [`00_plotly-charts-selector.py`](./00_plotly-charts-selector.py)
*   **Description:** This application demonstrates how to dynamically select and display different Plotly charts within a Trame application. It serves as a foundational example for integrating Plotly with Trame and showcases a responsive UI for chart selection.
*   **Image:**
    ```
    ![Plotly Charts Selector](./docs/images/00_plotly-charts-selector.png)
    ```
    *(Please replace with the actual path and image if different)*

---

### 2. Resizable Plotly Charts

*   **Script:** [`01_plotly-charts-resizable.py`](./01_plotly-charts-resizable.py)
*   **Description:** This example builds upon basic chart display by demonstrating how to make Plotly charts resizable within the Trame UI. It showcases handling layout changes and ensuring charts adapt to their container size.
*   **Image:**
    ```
    ![Resizable Plotly Charts](./docs/images/01_plotly-charts-resizable.png)
    ```
    *(Please replace with the actual path and image if different)*

---

*More examples to come!*

## Running the Examples

1.  Ensure you have Python and pip installed.
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install the required dependencies (you might need to create a `requirements.txt` file based on the imports in the scripts, typically `trame`, `trame-vuetify`, `plotly`):
    ```bash
    pip install trame trame-vuetify plotly
    ```
4.  Run an example script:
    ```bash
    python 00_plotly-charts-selector.py
    ```
5.  Open your web browser and navigate to the URL provided in the console (usually `http://localhost:8080`).

