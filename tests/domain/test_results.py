import pytest

from linkedin_post.domain.entities import DeleteResult, DeleteStatus, PublishResult, PublishStatus


@pytest.mark.parametrize(
    ("status", "posted", "retry_safe"),
    [
        (PublishStatus.POSTED, True, False),
        (PublishStatus.OUTCOME_UNKNOWN, False, False),
        (PublishStatus.DRY_RUN, False, True),
        (PublishStatus.INVALID_TEXT, False, True),
        (PublishStatus.EDITOR_NOT_FOUND, False, True),
        (PublishStatus.INSERT_FAILED, False, True),
    ],
)
def test_publish_flags_follow_status(status: PublishStatus, posted: bool, retry_safe: bool) -> None:
    result = PublishResult(status, "m")
    assert (result.posted, result.retry_safe) == (posted, retry_safe)


@pytest.mark.parametrize("status", list(DeleteStatus))
def test_delete_is_always_retry_safe(status: DeleteStatus) -> None:
    result = DeleteResult(status, "m")
    assert result.retry_safe is True
    assert result.deleted is (status is DeleteStatus.DELETED)


def test_publish_dict_drops_unset_fields() -> None:
    result = PublishResult(PublishStatus.POSTED, "Post published.", visibility="Anyone", post_url="u")
    assert result.to_dict() == {
        "status": "posted",
        "message": "Post published.",
        "visibility": "Anyone",
        "post_url": "u",
        "posted": True,
        "retry_safe": False,
    }


def test_delete_dict_shape() -> None:
    assert DeleteResult(DeleteStatus.DRY_RUN, "ok", "u").to_dict() == {
        "status": "dry_run",
        "message": "ok",
        "url": "u",
        "deleted": False,
        "retry_safe": True,
    }
