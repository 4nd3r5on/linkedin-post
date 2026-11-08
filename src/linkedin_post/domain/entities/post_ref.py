"""A reference to one LinkedIn post, from a URL or a URN."""

import re
from dataclasses import dataclass

# Upstream's permalink recognizer: urn:li:{activity,share,ugcPost}:<id> and
# linkedin.com/posts/<slug> URLs, in plain or JSON-escaped form.
from linkedin_mcp_server.linkedin.feed_payload import permalink_paths_from_payload

from linkedin_post.common.linkedin import absolute_url

_FEED_UPDATE = "/feed/update/"
# The entity a /posts/<slug> permalink names, e.g. name_title-activity-<id>-AbCd.
_SLUG_ENTITY = re.compile(r"-(activity|share|ugcPost)-(\d+)-")


class InvalidPostRef(ValueError):
    """Not a LinkedIn post URL or URN."""


@dataclass(frozen=True, slots=True)
class PostRef:
    """A post's canonical /feed/update/urn:li:<kind>:<id>/ page."""

    path: str

    @classmethod
    def parse(cls, raw: str) -> "PostRef":
        paths = permalink_paths_from_payload(raw.strip())
        for path in paths:
            if path.startswith(_FEED_UPDATE):
                return cls(path)
        for path in paths:
            match = _SLUG_ENTITY.search(path)
            if match:
                kind, entity_id = match.groups()
                return cls(f"{_FEED_UPDATE}urn:li:{kind}:{entity_id}/")
        raise InvalidPostRef("Give a LinkedIn post URL or a urn:li:activity/share/ugcPost URN.")

    @property
    def url(self) -> str:
        return absolute_url(self.path)
