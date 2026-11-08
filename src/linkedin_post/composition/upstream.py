"""Run mcp-server-linkedin unchanged, with our tools registered next to its post tools.

server.py imports ``register_post_tools`` by name and calls it only in a process
that drives the browser, so replacing that name before ``cli_main.main()`` runs
adds create_post and delete_post exactly where the original post tools go.
Pinned to 4.29.0: re-check this hook when bumping the dependency.
"""

from typing import Any

import linkedin_mcp_server.server as upstream_server
from linkedin_mcp_server import cli_main

from linkedin_post.adapters.primary.mcp_tools import register_posting_tools
from linkedin_post.composition.container import build_posting

_original_register_post_tools = upstream_server.register_post_tools


def register_post_tools(mcp: Any, **kwargs: Any) -> None:
    _original_register_post_tools(mcp, **kwargs)
    register_posting_tools(mcp, build_posting(), **kwargs)


def main() -> None:
    upstream_server.register_post_tools = register_post_tools
    cli_main.main()
