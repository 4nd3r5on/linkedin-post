"""Wire the domain service to its LinkedIn adapters."""

from linkedin_post.adapters.secondary.linkedin_composer import LinkedInComposer
from linkedin_post.adapters.secondary.linkedin_remover import LinkedInRemover
from linkedin_post.adapters.secondary.linkedin_session import UpstreamSessionGate
from linkedin_post.domain.ports.primary.posting import Posting
from linkedin_post.domain.services.posting import PostingService


def build_posting() -> Posting:
    return PostingService(UpstreamSessionGate(), LinkedInComposer(), LinkedInRemover())
