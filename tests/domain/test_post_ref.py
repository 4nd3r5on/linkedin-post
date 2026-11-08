# Copyright (c) 2026 Dmitry Andersson
# SPDX-License-Identifier: MIT
import pytest

from linkedin_post.domain.entities import InvalidPostRefError, PostRef

ID = "7525284009694609408"
FEED = f"https://www.linkedin.com/feed/update/urn:li:activity:{ID}/"


@pytest.mark.parametrize(
    ("raw", "url"),
    [
        (f"urn:li:activity:{ID}", FEED),
        (f"  urn:li:activity:{ID}\n", FEED),
        (FEED, FEED),
        (f"{FEED}?utm_source=share", FEED),
        (f"urn:li:share:{ID}", f"https://www.linkedin.com/feed/update/urn:li:share:{ID}/"),
        (f"urn:li:ugcPost:{ID}", f"https://www.linkedin.com/feed/update/urn:li:ugcPost:{ID}/"),
        (f"https://www.linkedin.com/posts/jane_my-setup-activity-{ID}-AbCd?utm=x", FEED),
        (
            f"https://www.linkedin.com/posts/jane_title-ugcPost-{ID}-xY_z",
            f"https://www.linkedin.com/feed/update/urn:li:ugcPost:{ID}/",
        ),
    ],
)
def test_resolves_to_feed_update_page(raw: str, url: str) -> None:
    assert PostRef.parse(raw).url == url


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "hello",
        "https://www.linkedin.com/in/someone/",
        "https://example.com/posts/x-activity-7525284009694609408-ab",
        "urn:li:comment:7525284009694609408",
        "urn:li:activity:123",  # too short to be a real entity id
    ],
)
def test_rejects_non_posts(raw: str) -> None:
    with pytest.raises(InvalidPostRefError):
        PostRef.parse(raw)
