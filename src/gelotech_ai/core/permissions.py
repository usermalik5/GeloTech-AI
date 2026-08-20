"""Persistent permission policy primitives.

The first implementation is intentionally provider- and GUI-independent so the
same policy can later protect every agent tool consistently.
"""

from enum import StrEnum


class PermissionAction(StrEnum):
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    TERMINAL = "terminal"
    GIT = "git"


class PermissionDecision(StrEnum):
    ASK = "ask"
    ALLOW_ONCE = "allow_once"
    ALWAYS_ALLOW = "always_allow"
    DENY = "deny"


class PermissionPolicy:
    """In-memory policy for a project.

    Persistence and the GUI approval dialog will be added after the core tool
    execution path is established.
    """

    def __init__(self) -> None:
        self._decisions: dict[PermissionAction, PermissionDecision] = {}

    def set(self, action: PermissionAction, decision: PermissionDecision) -> None:
        self._decisions[action] = decision

    def get(self, action: PermissionAction) -> PermissionDecision:
        return self._decisions.get(action, PermissionDecision.ASK)
