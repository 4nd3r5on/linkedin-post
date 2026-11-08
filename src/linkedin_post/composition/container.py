# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
"""Wire the domain service to its LinkedIn adapters."""

from linkedin_post.adapters.secondary.linkedin_composer import LinkedInComposer
from linkedin_post.adapters.secondary.linkedin_remover import LinkedInRemover
from linkedin_post.adapters.secondary.linkedin_session import UpstreamSessionGate
from linkedin_post.domain.ports.primary.posting import Posting
from linkedin_post.domain.services.posting import PostingService


def build_posting() -> Posting:
    """Build the Posting port backed by upstream's browser."""
    return PostingService(UpstreamSessionGate(), LinkedInComposer(), LinkedInRemover())
