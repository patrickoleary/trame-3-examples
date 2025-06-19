# Project Collaboration Guidelines: Trame Examples Refactoring

"Remember our collaboration guidelines as we work on this."

## 1. General Principles
    - These guidelines form the agreed-upon framework for our collaboration in this workspace.
    - Objective: Modernize examples to Trame 3, Vuetify 3, Vue 3.
    - Prioritize accuracy, efficiency, and adherence to established patterns.
    - Actively use and refer to created Memories and these guidelines.

## 2. Task Interpretation & Scope
    - Carefully analyze the initial prompt and existing code.
    - Clarify scope: Only refactor elements necessary for Trame 3/Vuetify 3/Vue 3 compatibility and agreed-upon style improvements. Avoid unnecessary changes.
    - Preserve all original functionality unless explicitly decided otherwise.

## 3. Coding Standards & Style
    - Strictly follow the Trame style guide (e.g., class-based structure, state management, UI component usage).
    - Pay close attention to import aliases (e.g., `from trame.widgets import vtk` means using `vtk.VtkLocalView`, not `vtk_widgets.VtkLocalView`).
    - Ensure generated code is runnable and dependencies are correctly handled.
    - **Refactoring Targets in Original Scripts**:
        - Convert procedural or older Trame script structures to a modern Trame 3 class-based approach (e.g., `YourApp(trame.app.TrameApp)`).
        - Ensure methods intended to be part of the application's class logic consistently include `self` as their first parameter. Relocate variables these methods depend on from global scope or closures into instance attributes (e.g., `self.config_setting` initialized in `__init__`) or reactive state variables (`self.state.ui_value` initialized in `_initialize_state`), making them part of the application's encapsulated context.
        - Replace Trame 2/Vue 2/Vuetify 2 component instantiation, layout, and event handling (e.g., `layout.content.children += [...]`, `server.controller.on_server_ready.add(...)`) with Trame 3/Vue 3/Vuetify 3 equivalents (e.g., `trame.ui.vuetify3.SinglePageLayout`, `trame.widgets.vuetify3`, `@change` decorators, `self.ctrl.method_name`).
        - Update state management from older Trame patterns (e.g., `server.state.set("var_name", value)`) to the direct `self.state.variable_name = initial_value` pattern within the app class.
        - Modernize VTK pipeline integration, ensuring `VtkLocalView`, `VtkRemoteView`, `VtkPolyData` (and similar) components are used correctly with appropriate props and event bindings.
        - Update script headers (shebang, dependencies, usage instructions) and the `main()` function pattern to align with current best practices in the `patrickoleary/trame-3-examples` repository.
    - **Leverage Existing Patterns**: When refactoring, if UI elements or callback methods in the target script have direct analogues in existing style-guide compliant examples (from `patrickoleary/trame-3-examples`), prioritize adapting those proven code snippets rather than regenerating similar logic from scratch. This promotes consistency and efficiency.

## 4. Specific Task Guidelines
    - **README.md Updates:**
        - Always view the existing README section to understand the exact formatting, heading levels, and content structure before making changes.
        - Confirm placement of new entries carefully.
        - Ensure image paths and link targets are correct.
        - When adding a new example or significantly refactoring an existing one, ensure a corresponding entry is created or updated in `README.md`.
        - Include a brief description of the example's purpose and key features demonstrated.
        - Ensure a relevant screenshot (e.g., `docs/images/ExampleName.png`) is linked in the README entry.
    - **File Header Comments:**
        - Follow the established multi-part format (uv run block, description, key features, detailed usage instructions).
    - **Git Workflow:**
        - Use descriptive branch names (e.g., `feat/feature-name`, `refactor/component-update`).
        - All new features, refactors, or significant bug fixes should be developed on a separate feature branch.
        - Write clear and concise commit messages.
        - Ensure all relevant files (scripts, `README.md` updates, new images) are included in the commit(s) on the feature branch before merging.
        - Confirm files to be added before committing.
        - Once work on a feature branch is complete and tested, it should be merged into the `main` branch.
        - After merging into `main`, the `main` branch should be pushed to the remote repository (`origin`).

    - **Updating These Collaboration Guidelines (`COLLABORATION_GUIDELINES.md`):**
        - These guidelines are intended for local collaboration between USER and Cascade and should **not** be published to the public repository.
        - To modify these guidelines:
            1. **USER**: Manually edit the `.gitignore` file to remove the line `COLLABORATION_GUIDELINES.md`.
            2. **USER**: Commit this change to `.gitignore` (e.g., `git commit -m "DEV: Temporarily unignore collaboration guidelines for editing"`). This commit to `.gitignore` can be part of the regular commit history if desired.
            3. **Cascade**: Upon request, read and apply the desired changes to `COLLABORATION_GUIDELINES.md`.
            4. **USER**: Manually edit the `.gitignore` file to add the line `COLLABORATION_GUIDELINES.md` back.
            5. **USER**: Commit the changes to `COLLABORATION_GUIDELINES.md` AND the re-ignoring change to `.gitignore` together in a single, local-only commit (e.g., `git add COLLABORATION_GUIDELINES.md .gitignore && git commit -m "CHORE: Update collaboration guidelines (local only)"`). **This commit should not be pushed to the public remote.**

## 5. Tool Usage
    - When reading files (`view_file`), if the initial output is incomplete or doesn't match expectations, re-attempt with broader parameters or specific line ranges to get full context.
    - Double-check arguments for all tool calls to prevent errors.

## 6. Communication & Feedback
    - Proactively ask for clarification if any part of a request is unclear.
    - Acknowledge feedback and explicitly state how it will be incorporated.
    - If a mistake is made, identify the root cause and how to prevent it in the future.

## 7. Memory System and Learning

### 7.1. Proactive Memory Creation and Review
    - Cascade will proactively create memories for important patterns, decisions, and user preferences.
    - USER will review and approve/reject memories.
    - Both USER and Cascade will strive to ensure memories are accurate and consistently applied.

### 7.2. Corrective Feedback and Learning
    - If Cascade makes an error, the USER can provide a concise correction.
    - A simple format like `Correction: [task X] should be [method Y]` or `Correction: [incorrect approach] should be [correct approach]` is effective.
    - Cascade will interpret this and create an internal memory to learn from the feedback.
    - *Example*: "Correction: state updates are done via `self.state.variable_name = value`."

## 8. Workflow Aliases

    - **"Git Finalize"**:
        1. Create and switch to a new feature branch (e.g., `feat/descriptive-name`).
        2. Add specified files (Python script, new or updated images in `docs/images/`, updated `README.md`).
        3. Commit changes with a descriptive message.
        4. Switch back to the `main` branch.
        5. Pull the latest changes from `origin main` (to avoid conflicts).
        6. Merge the feature branch into `main`.
        7. Push `main` to `origin`.
        8. (Optional) Delete the local feature branch and return to the previous working branch.

        Usage Examples:
            - "Let's do a **Git Finalize**. The feature was adding a new contour slider." (Cascade will infer files or ask for clarification)
            - "Time for a **Git Finalize**. Please include `LocalViewRemoteViewRendering.py`, `README.md`, and the new screenshot `contour_view.png`. The branch name should be `feat/local-remote-view-refactor` and the commit message 'Refactor LocalViewRemoteViewRendering with dual views'."
            - "Okay, **Git Finalize** this refactor." (If context is clear, Cascade will ask for branch name, files, and commit message)

    - **"Refactor Example"** (for a given `example_script.py`):
        1. **Analyze Script** (Input: `target_script.py`. Style Guides: USER can specify files/directories; otherwise, Cascade will use relevant modern examples from `patrickoleary/trame-3-examples` as primary references):
            - Review `target_script.py` to identify Trame 2/Vue 2/Vuetify 2 patterns.
            - Consult existing Trame 3 examples in the repository (e.g., `patrickoleary/trame-3-examples`) as style guides for structure, component usage, and best practices.
            - Note all core functionalities in `target_script.py` that must be preserved.
        2. **Core Refactor to Trame 3/Vue 3/Vuetify 3**:
            - Create a new class (e.g., `ExampleNameApp`) inheriting from `trame.app.TrameApp`.
            - Implement `__init__(self, server=None)`:
                - Call `super().__init__(server=server)`.
                - Initialize any core components (like VTK sources, data readers).
                - Call `self._initialize_state()`.
                - Call `self._build_ui()`.
                - Call any initial update/setup methods if needed.
            - Implement `_initialize_state()`:
                - Define all reactive state variables using `self.state.variable_name = initial_value`.
            - Implement `_build_ui()`:
                - Use `trame.ui.vuetify3.SinglePageLayout(self.server)`.
                - Reconstruct the UI using `trame.widgets.vuetify3` and `trame.widgets.vtk` (or other relevant widget sets).
                - Ensure all UI components are correctly bound to state variables and event handlers.
            - Update event handlers (e.g., methods decorated with `@change("state_variable")`) to use Trame 3 patterns.
            - Ensure all original functionalities are present and working.
        3. **Update Header Comments**:
            - Modify the header of `example_script.py` to match the standard format (uv run, description, key features, usage instructions).
        4. **Testing**:
            - Run the `example_script.py` to ensure it works correctly.
            - Test all interactive elements and functionalities.
        5. **Update README.md**:
            - Add or update the entry for `example_script.py` in `README.md`, ensuring correct formatting, description, and image links.
        6. **(Optional) Git Finalize**:
            - Perform the "Git Finalize" workflow if the refactor is complete and ready for merging.

        Usage Examples:
            - "Let's **Refactor Example** for `vtk/some_old_directory/old_script.py`."
            - "Okay, let's **Refactor Example** for this script." (when the script is clear from context)
            - "Let's **Refactor Example** for `vtk/old_examples/old_cone.py`. For style guides, please refer to `vtk/01_SimpleCone/ClientView.py` and the examples in `vtk/02_ContourGeometry/`."
            - "Let's **Refactor Example** for this charting script. Use our recent Altair examples as the main style guide."
