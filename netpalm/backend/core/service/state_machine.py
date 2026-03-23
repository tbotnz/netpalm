"""
Service instance state machine.

Defines all valid states and the allowed transition table.
Raises InvalidStateTransitionError for any disallowed transition.
"""

from __future__ import annotations

from enum import StrEnum


class ServiceInstanceState(StrEnum):
    deploying = "deploying"
    deployed = "deployed"
    updating = "updating"
    deleting = "deleting"
    deleted = "deleted"
    errored = "errored"


# Allowed transitions: from_state → set of valid to_states
VALID_TRANSITIONS: dict[ServiceInstanceState, set[ServiceInstanceState]] = {
    ServiceInstanceState.deploying: {
        ServiceInstanceState.deployed,
        ServiceInstanceState.errored,
    },
    ServiceInstanceState.deployed: {
        ServiceInstanceState.updating,
        ServiceInstanceState.deleting,
        ServiceInstanceState.errored,
    },
    ServiceInstanceState.updating: {
        ServiceInstanceState.deployed,
        ServiceInstanceState.errored,
    },
    ServiceInstanceState.deleting: {
        ServiceInstanceState.deleted,
    },
    ServiceInstanceState.errored: {
        ServiceInstanceState.deploying,
    },
    ServiceInstanceState.deleted: set(),  # terminal state
}


class InvalidStateTransitionError(Exception):
    """Raised when a requested state transition is not permitted."""

    def __init__(self, from_state: ServiceInstanceState, to_state: ServiceInstanceState) -> None:
        super().__init__(f"Invalid state transition: {from_state.value} → {to_state.value}")
        self.from_state = from_state
        self.to_state = to_state


class ServiceVersionNotFoundError(Exception):
    """Raised when a requested version snapshot does not exist."""

    def __init__(self, service_id: str, version: int) -> None:
        super().__init__(f"Version {version} not found for service {service_id}")
        self.service_id = service_id
        self.version = version


def validate_transition(
    from_state: ServiceInstanceState,
    to_state: ServiceInstanceState,
) -> None:
    """Raise InvalidStateTransitionError if the transition is not permitted."""
    allowed = VALID_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise InvalidStateTransitionError(from_state, to_state)
