# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
