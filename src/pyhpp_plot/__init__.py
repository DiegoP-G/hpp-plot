from .graph_viewer_thread import GraphViewerThread
from .interactive_viewer import InteractiveGraphViewer
from .websocket_bridge import GraphWebSocketBridge

__all__ = [
    "GraphViewerThread",
    "GraphWebSocketBridge",
    "InteractiveGraphViewer",
]

try:
    # `graph_viewer` is a Boost.Python extension module built only when
    # hpp-plot is compiled with -DUSE_QT=ON (see CMakeLists.txt). It is not
    # required by the recommended pyhpp_plot workflow (GraphViewerThread /
    # InteractiveGraphViewer / GraphWebSocketBridge), so its absence must not
    # prevent `import pyhpp_plot` from succeeding when built with USE_QT=OFF.
    from .graph_viewer import (
        MenuActionProxy,
        show_graph,
        show_graph_blocking,
        show_interactive_graph,
    )

    __all__ += [
        "MenuActionProxy",
        "show_graph",
        "show_graph_blocking",
        "show_interactive_graph",
    ]
except ImportError:
    pass
