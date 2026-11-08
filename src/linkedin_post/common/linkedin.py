# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""LinkedIn URLs shared by the domain and the browser adapters."""

BASE_URL = "https://www.linkedin.com"
SHARE_URL = f"{BASE_URL}/feed/?shareActive=true"


def absolute_url(path: str) -> str:
    """Turn a site-relative LinkedIn path into a full URL; leave full URLs alone."""
    return BASE_URL + path if path.startswith("/") else path
