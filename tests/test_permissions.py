from gelotech_ai.core.permissions import (
    PermissionAction,
    PermissionDecision,
    PermissionPolicy,
)


def test_permissions_default_to_ask() -> None:
    policy = PermissionPolicy()
    assert policy.get(PermissionAction.TERMINAL) == PermissionDecision.ASK


def test_permission_can_be_changed() -> None:
    policy = PermissionPolicy()
    policy.set(PermissionAction.READ_FILES, PermissionDecision.ALWAYS_ALLOW)
    assert policy.get(PermissionAction.READ_FILES) == PermissionDecision.ALWAYS_ALLOW
