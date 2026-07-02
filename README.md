# hpp-plot

[![Pipeline status](https://gitlab.laas.fr/humanoid-path-planner/hpp-plot/badges/master/pipeline.svg)](https://gitlab.laas.fr/humanoid-path-planner/hpp-plot/commits/master)
[![Coverage report](https://gitlab.laas.fr/humanoid-path-planner/hpp-plot/badges/master/coverage.svg?job=doc-coverage)](https://gepettoweb.laas.fr/doc/humanoid-path-planner/hpp-plot/master/coverage/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/humanoid-path-planner/hpp-plot/master.svg)](https://results.pre-commit.ci/latest/github/humanoid-path-planner/hpp-plot)

`hpp-plot` provides graphical tools to visualize and interact with the constraint graphs built by [HPP](https://github.com/humanoid-path-planner/hpp-doc) manipulation planners (`hpp-manipulation`). It contains two generations of viewers:

- **`pyhpp_plot`** — the modern, actively developed viewer: a Python package that serves an interactive constraint-graph web app (React + [cytoscape.js](https://js.cytoscape.org/)), driven live over WebSocket from a running HPP planning session. No CORBA, no `gepetto-gui` required.
- **Qt / CORBA layer** (`hpp::plot::HppManipulationGraphWidget`, `gepetto-gui` plugins, `hpp-plot-manipulation-graph` binary). **⚠️ Deprecated**: kept for backward compatibility with existing CORBA-based setups only. New projects should use `pyhpp_plot`;

> **This package is meant to be used through [`hpp-gepetto-viewer`](https://github.com/humanoid-path-planner/hpp-gepetto-viewer)**, not on its own — see [Usage](#usage).

## Table of contents

- [Package layout](#package-layout)
- [Dependencies](#dependencies)
- [Installation](#installation)
  - [From source with CMake](#from-source-with-cmake)
  - [With Nix](#with-nix)
- [Usage](#usage)
  - [Recommended: via `hpp-gepetto-viewer`](#recommended-via-hpp-gepetto-viewer)
  - [Direct API (not a tested standalone usage path)](#direct-api-not-a-tested-standalone-usage-path)
- [Web viewer architecture](#web-viewer-architecture)
- [Documentation](#documentation)
- [License](#license)

## Package layout

```
hpp-plot/
├── CMakeLists.txt              # C++/CMake build: graph widget lib, Python bindings, npm/React build
├── package.xml                 # ROS package manifest
├── pyproject.toml              # Python lint config (ruff)
├── flake.nix                   # Nix flake (build via github:gepetto/nix)
├── doc/
│   └── web_plot_spec.md            # Functional spec of the web viewer (life cycle, protocol, routing)
├── include/hpp/plot/
│   ├── graph-widget.hh              # Generic graph widget base class
│   ├── hpp-native-graph.hh          # In-process (native) graph widget — used by pyhpp_plot
│   └── hpp-manipulation-graph.hh    # Qt/CORBA-backed graph widget — DEPRECATED
├── src/
│   ├── graph-widget.cc, hpp-native-graph.cc     # Native graph widget implementation (recommended)
│   ├── hpp-manipulation-graph.cc                    # Qt/CORBA widget implementation — DEPRECATED
│   ├── pyhpp_plot/                  # Python package (installed as `pyhpp_plot`) — recommended
│   │   ├── __init__.py                  # Re-exports the public API
│   │   ├── graph_viewer.cc              # Boost.Python module `graph_viewer`: show_graph(), show_interactive_graph(), MenuActionProxy
│   │   ├── interactive_viewer.py        # InteractiveGraphViewer: business logic, HPP action dispatch
│   │   ├── graph_viewer_thread.py       # GraphViewerThread: manages the viewer life cycle in a daemon thread
│   │   ├── websocket_bridge.py          # GraphWebSocketBridge: WebSocket server, Python ⇄ React messages
│   │   ├── web_app_server.py            # StaticWebAppService: serves the built React app over HTTP
│   │   └── utils.py                     # _serialize_graph(), _jsonable(): graph/JSON serialization helpers
│   └── web_app/                     # React + Vite + cytoscape.js frontend (npm project) — recommended
│       └── src/
│           ├── App.jsx, main.jsx
│           ├── components/              # GraphCanvas, ContextMenu, Toolbar, Legend, DownloadForm, ...
│           ├── graph/                   # cytoscapeGraph.js, normalizeSnapshot.js, style.js
│           ├── hooks/webSocket.js       # WebSocket client hook
│           └── utils/                   # Type.js, downloadGraph.js, contextMenuPosition.js
├── bin/
│   └── hpp-plot-manipulation-graph.cc  # DEPRECATED: standalone Qt binary connecting to hppcorbaserver
└── plugins/                     # DEPRECATED: gepetto-gui plugins (legacy Qt/CORBA layer)
    ├── hppmanipulationcorbaplugin/      # Embeds the manipulation graph widget in gepetto-gui
    └── hppmonitoringplugin/             # Monitoring/interaction plugin — its features are now
                                          # reimplemented, CORBA-free, in pyhpp_plot.interactive_viewer
```

## Dependencies

Common, always required:

- CMake ≥ 3.22, a C++ compiler
- [`jrl-cmakemodules`](https://github.com/jrl-umi3218/jrl-cmakemodules) (fetched automatically via `FetchContent` if not already available)

Required for the recommended web viewer (`pyhpp_plot`):

- `hpp-manipulation`
- Boost.Python (found via `search_for_boost_python()`)
- Python ≥ 3.9, `numpy`
- Python `websockets` (used by `GraphWebSocketBridge`)
- Node.js / npm (to build the React frontend, unless `USE_JS=OFF`)

Additional, **only for the deprecated Qt/CORBA layer** (`USE_QT=ON`, `USE_CORBA=ON`):

- Qt5 (`Core`, `Widgets`, `Gui`, `PrintSupport`, `Concurrent`, `OpenGL`, `Network`, `Xml`)
- [`qgv`](https://github.com/gepetto/qgv) (Qt Graphviz wrapper)
- [`gepetto-viewer`](https://github.com/Gepetto/gepetto-viewer), `gepetto-viewer-corba`
- `hpp-manipulation-corba`
- `gepetto-gui` (for the `hppmanipulationcorbaplugin` / `hppmonitoringplugin` plugins)

## Installation

### From source with CMake

```bash
git clone --recursive https://github.com/humanoid-path-planner/hpp-plot.git
mkdir hpp-plot/build
cd hpp-plot/build
cmake .. -DCMAKE_INSTALL_PREFIX=<your_install_prefix>
make
make install
```

Relevant CMake options:

- `USE_JS` (default `ON`): run `npm install && npm run build` from CMake to build the React web app, installed to `share/hpp-plot/webapp`. Set to `OFF` to build it manually or skip the web frontend.
- `USE_QT` (default `OFF`, **deprecated**): build the legacy Qt-based graph widget (`hpp-manipulation-graph`), the `hpp-plot-manipulation-graph` standalone binary, and — combined with `USE_CORBA` — the `gepetto-gui` plugins. Not needed to build or use `pyhpp_plot`. Leave this `OFF` unless you specifically need the legacy workflow.
- `USE_CORBA` (default `OFF`, **deprecated**, requires `USE_QT=ON`): additionally build the CORBA-backed graph widget and the `gepetto-gui` plugins (`hppmanipulationcorbaplugin`, `hppmonitoringplugin`). Requires `hpp-manipulation-corba` and `gepetto-viewer(-corba)`.

Recommended build (modern web viewer only):

```bash
cmake .. -DUSE_QT=OFF -DUSE_JS=ON
```

### With Nix

A flake is provided and builds against [`github:gepetto/nix`](https://github.com/gepetto/nix); it builds the npm frontend through Nix's `fetchNpmDeps`/`npmConfigHook` rather than via CMake's `USE_JS`:

```bash
nix build github:humanoid-path-planner/hpp-plot
```

## Usage

> **Recommended: use `hpp-plot` through `hpp-gepetto-viewer`, not directly.** `pyhpp_plot`'s public API (`GraphViewerThread`, `InteractiveGraphViewer`, `GraphWebSocketBridge`, ...) is usable directly in Python, but the integration that is actually built, documented end-to-end, and exercised in practice is [`hpp-gepetto-viewer`](https://github.com/humanoid-path-planner/hpp-gepetto-viewer)'s `viewers`, via its `setGraph()` / `setProblem()` / `launch_graph_viewer()`. Calling `hpp-plot`'s API directly, outside of that integration, is possible but not a validated/tested usage path.

### Recommended: via `hpp-gepetto-viewer`

```python
from pyhpp_rviz import RVizVisualizer

v = RVizVisualizer()
v.initViewer(robot)
v.setGraph(graph)        # PyWGraph
v.setProblem(problem)    # PyWProblem
v.launch_graph_viewer()  # starts hpp-plot's GraphViewerThread under the hood
```

Configurations generated from the graph viewer are forwarded to `v.display()` automatically. This is the only entry point that has actually been exercised end-to-end; the direct `pyhpp_plot` API below is documented for reference and for `hpp-gepetto-viewer`'s own use, not as a standalone, supported integration surface.

### Direct API

The simplest entry point is `GraphViewerThread`, which manages the whole life cycle (static HTTP server for the React app, WebSocket bridge, and the underlying native graph renderer) in a background daemon thread:

```python
from pyhpp_plot import GraphViewerThread

def on_config_generated(config, label):
    print(f"New configuration generated ({label}): {config}")

viewer = GraphViewerThread(
    graph,               # PyWGraph from pyhpp.manipulation
    problem,              # PyWProblem from pyhpp.manipulation
    config_callback=on_config_generated,
    ws_host="127.0.0.1", ws_port=8765,
    react_host="127.0.0.1", react_port=5177,
)
viewer.start()          # non-blocking: starts the HTTP + WebSocket servers
# ... open http://127.0.0.1:5177 in a browser ...
viewer.send_viewer_snapshot(graph)   # push an updated snapshot at any time
viewer.stop()
```

This is precisely what `hpp-gepetto-viewer`'s `RVizVisualizer.launch_graph_viewer()` calls internally — see [Recommended: via `hpp-gepetto-viewer`](#recommended-via-hpp-gepetto-viewer) above.

For lower-level control, the same building blocks are available individually:

```python
from pyhpp_plot import InteractiveGraphViewer, GraphWebSocketBridge

viewer = InteractiveGraphViewer(graph, problem, config_callback=on_config_generated)
bridge = GraphWebSocketBridge(
    host="127.0.0.1", port=8765,
    on_message=viewer.handle_web_app_message,
    snapshot_provider=lambda: {"type": "viewer_snapshot", "graph": ...},
)
bridge.start()
```

## Web viewer architecture

The web viewer's life cycle, Python ⇄ React WebSocket protocol, frontend features, and business-action routing are fully documented in [`doc/web_plot_spec.md`](doc/web_plot_spec.md) — see that file for details, including the sequence diagram.

## Documentation

- Full functional spec of the web viewer: [`doc/web_plot_spec.md`](doc/web_plot_spec.md).
- Doxygen-generated API documentation is published at <https://gepettoweb.laas.fr/doc/humanoid-path-planner/hpp-plot/master/doxygen-html/index.html>.
- Notable changes between releases are listed in [`NEWS`](NEWS).

## License

`hpp-plot` is released under the [BSD 2-Clause License](LICENSE), Copyright (c) 2015-2018, hpp-plot.