"""Tests for the service instance state machine."""

import pytest

from netpalm.backend.core.service.state_machine import (
    VALID_TRANSITIONS,
    InvalidStateTransitionError,
    ServiceInstanceState,
    ServiceVersionNotFoundError,
    validate_transition,
)


class TestServiceInstanceState:
    def test_all_states_defined(self):
        expected = {"deploying", "deployed", "updating", "deleting", "deleted", "errored"}
        assert {s.value for s in ServiceInstanceState} == expected

    def test_string_enum(self):
        assert ServiceInstanceState.deploying == "deploying"
        assert ServiceInstanceState.deployed.value == "deployed"


class TestValidTransitions:
    """Verify every allowed transition succeeds and disallowed ones raise."""

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            (ServiceInstanceState.deploying, ServiceInstanceState.deployed),
            (ServiceInstanceState.deploying, ServiceInstanceState.errored),
            (ServiceInstanceState.deployed, ServiceInstanceState.updating),
            (ServiceInstanceState.deployed, ServiceInstanceState.deleting),
            (ServiceInstanceState.deployed, ServiceInstanceState.errored),
            (ServiceInstanceState.updating, ServiceInstanceState.deployed),
            (ServiceInstanceState.updating, ServiceInstanceState.errored),
            (ServiceInstanceState.deleting, ServiceInstanceState.deleted),
            (ServiceInstanceState.errored, ServiceInstanceState.deploying),
        ],
    )
    def test_valid_transition(self, from_state, to_state):
        validate_transition(from_state, to_state)  # should not raise

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            (ServiceInstanceState.deploying, ServiceInstanceState.deleting),
            (ServiceInstanceState.deploying, ServiceInstanceState.updating),
            (ServiceInstanceState.deployed, ServiceInstanceState.deploying),
            (ServiceInstanceState.deployed, ServiceInstanceState.deleted),
            (ServiceInstanceState.updating, ServiceInstanceState.deleting),
            (ServiceInstanceState.deleting, ServiceInstanceState.deploying),
            (ServiceInstanceState.deleting, ServiceInstanceState.errored),
            (ServiceInstanceState.deleted, ServiceInstanceState.deploying),
            (ServiceInstanceState.deleted, ServiceInstanceState.deployed),
            (ServiceInstanceState.errored, ServiceInstanceState.deployed),
            (ServiceInstanceState.errored, ServiceInstanceState.updating),
        ],
    )
    def test_invalid_transition_raises(self, from_state, to_state):
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            validate_transition(from_state, to_state)
        assert exc_info.value.from_state == from_state
        assert exc_info.value.to_state == to_state

    def test_deleted_is_terminal(self):
        """No transitions out of deleted."""
        for target in ServiceInstanceState:
            if target == ServiceInstanceState.deleted:
                continue
            with pytest.raises(InvalidStateTransitionError):
                validate_transition(ServiceInstanceState.deleted, target)

    def test_every_state_has_transition_entry(self):
        for state in ServiceInstanceState:
            assert state in VALID_TRANSITIONS


class TestExceptions:
    def test_invalid_transition_error_message(self):
        err = InvalidStateTransitionError(ServiceInstanceState.deployed, ServiceInstanceState.deleted)
        assert "deployed" in str(err)
        assert "deleted" in str(err)

    def test_service_version_not_found_error(self):
        err = ServiceVersionNotFoundError("abc-123", 5)
        assert "abc-123" in str(err)
        assert err.service_id == "abc-123"
        assert err.version == 5
