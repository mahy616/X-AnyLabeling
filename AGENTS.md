# AGENTS

## Overview
X-AnyLabeling is a PyQt5-based image annotation tool with multi-task support (segmentation, detection, classification) and optional AI-assisted labeling. The app is organized around a main window that hosts a large, feature-rich LabelingWidget ("god class") which wires most UI actions, menus, and interactions.

## Entry Points
- App entry: `anylabeling/app.py`
- Main window: `anylabeling/views/mainwindow.py`
- Labeling UI wrapper: `anylabeling/views/labeling/label_wrapper.py`
- Core UI/logic: `anylabeling/views/labeling/label_widget.py`

## Key Directories
- `anylabeling/views/` UI layer and dialogs
- `anylabeling/views/labeling/` core labeling widget, canvas, widgets, dialogs
- `anylabeling/services/` background services (auto-labeling, auto-training)
- `anylabeling/configs/` YAML configuration files
- `anylabeling/resources/` icons and UI assets
- `tests/` automated tests
- `scripts/` build and utility scripts

## Configuration
Primary config: `anylabeling/configs/xanylabeling_config.yaml`
- `annotation_mode`: `vm_segmentation` or `vm_detection`
- `shortcuts`: key bindings
- `custom_models`: auto-labeling models
- `external_tools.imdlseg`: external segmentation training/inference launcher

## External Tool Integration (IMDLSeg)
Train menu actions launch IMDLSeg as a separate process.
Config fields (in `anylabeling/configs/xanylabeling_config.yaml`):
- `external_tools.imdlseg.workdir`: IMDLSeg repo root
- `external_tools.imdlseg.entry`: launcher script or exe (default `traingUI_v2.2.0.py`)
- `external_tools.imdlseg.python`: optional Python interpreter path (null uses current interpreter)
- `external_tools.imdlseg.args`: optional extra args list

Runtime behavior:
- Menu actions live in `anylabeling/views/labeling/label_widget.py`
- Launcher sets environment variable `IMDLSEG_MODE` to `train` or `infer`
- Launch uses `subprocess.Popen` and does not block the UI

## Menus and Actions
All menu/toolbar actions are created in `anylabeling/views/labeling/label_widget.py`. The Train menu is defined there. If you add new menu items, update action creation and `utils.add_actions` for the menu.

## Build/Packaging
Spec files are in repo root:
- `x-anylabeling-win-*.spec` (Windows)
- `x-anylabeling-linux-*.spec`
- `x-anylabeling-macos.spec`
Build scripts live under `scripts/`.

## Testing
- Tests are under `tests/`
- Run the app locally: `python anylabeling/app.py`

## Notes
- Prefer small, localized changes in `label_widget.py` due to its size.
- Use config-driven paths for external integrations.
