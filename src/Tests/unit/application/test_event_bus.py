"""
test_event_bus.py — Unit tests for src/application/event_bus.py
                    and src/application/events.py

Epic: EPIC-3 | User Story: US-302
Covers acceptance criteria: AC-1, AC-2, AC-3, AC-4, AC-5
Specification: system_design.md §7
"""
from __future__ import annotations

import pytest

from src.domain.enums import PlayerSide, Rank
from src.domain.piece import Piece, Position

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.application.event_bus import EventBus
except ImportError:
    EventBus = None  # type: ignore[assignment, misc]

try:
    from src.application.events import (
        CombatResolved,
        GameLoaded,
        GameOver,
        GameSaved,
        InvalidMove,
        PieceMoved,
        PiecePlaced,
        TurnChanged,
    )
except ImportError:
    PiecePlaced = None  # type: ignore[assignment, misc]
    PieceMoved = None  # type: ignore[assignment, misc]
    CombatResolved = None  # type: ignore[assignment, misc]
    TurnChanged = None  # type: ignore[assignment, misc]
    GameOver = None  # type: ignore[assignment, misc]
    InvalidMove = None  # type: ignore[assignment, misc]
    GameSaved = None  # type: ignore[assignment, misc]
    GameLoaded = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    EventBus is None or PieceMoved is None,
    reason="src.application.event_bus / events not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_piece(rank: Rank = Rank.SCOUT, owner: PlayerSide = PlayerSide.RED) -> Piece:
    return Piece(rank=rank, owner=owner, revealed=False, has_moved=False, position=Position(8, 0))


def make_piecemoved_event() -> object:
    """Return a PieceMoved event using standard field names."""
    return PieceMoved(
        from_pos=Position(6, 4),
        to_pos=Position(5, 4),
        piece=make_piece(),
    )


# ---------------------------------------------------------------------------
# US-302 AC-1: Subscriber receives event exactly once
# ---------------------------------------------------------------------------


class TestSubscriberReceivesEvent:
    """AC-1: Registered subscriber is called exactly once per published event."""

    def test_single_subscriber_called_once_on_publish(self) -> None:
        """Subscriber callback is invoked exactly one time."""
        bus = EventBus()
        received: list[object] = []
        bus.subscribe(PieceMoved, lambda e: received.append(e))
        event = make_piecemoved_event()
        bus.publish(event)
        assert len(received) == 1

    def test_subscriber_receives_correct_event_instance(self) -> None:
        """The subscriber receives the exact event object that was published."""
        bus = EventBus()
        received: list[object] = []
        bus.subscribe(PieceMoved, lambda e: received.append(e))
        event = make_piecemoved_event()
        bus.publish(event)
        assert received[0] is event

    def test_two_publishes_invoke_subscriber_twice(self) -> None:
        """Publishing twice causes the subscriber to be called twice."""
        bus = EventBus()
        call_count: list[int] = [0]
        bus.subscribe(PieceMoved, lambda e: call_count.__setitem__(0, call_count[0] + 1))
        bus.publish(make_piecemoved_event())
        bus.publish(make_piecemoved_event())
        assert call_count[0] == 2

    def test_subscriber_for_different_type_not_called(self) -> None:
        """Subscriber registered for TurnChanged is not called for PieceMoved."""
        bus = EventBus()
        received: list[object] = []
        bus.subscribe(TurnChanged, lambda e: received.append(e))
        bus.publish(make_piecemoved_event())
        assert len(received) == 0


# ---------------------------------------------------------------------------
# US-302 AC-2: No error when no subscribers exist
# ---------------------------------------------------------------------------


class TestPublishWithNoSubscribers:
    """AC-2: Publishing an event with no subscribers must not raise."""

    def test_publish_with_no_subscribers_does_not_raise(self) -> None:
        """Publishing CombatResolved when no one subscribes raises no exception."""
        bus = EventBus()
        # Should not raise
        bus.publish(
            CombatResolved(
                attacker=make_piece(Rank.CAPTAIN, PlayerSide.RED),
                defender=make_piece(Rank.MAJOR, PlayerSide.BLUE),
                winner=PlayerSide.RED,
            )
        )

    def test_publish_unknown_event_type_does_not_raise(self) -> None:
        """Publishing an event type no one has subscribed to is safe."""
        bus = EventBus()
        bus.publish(GameSaved(filepath="/tmp/save.json"))


# ---------------------------------------------------------------------------
# US-302 AC-3: One failing subscriber does not block others
# ---------------------------------------------------------------------------


class TestFailingSubscriberDoesNotBlockOthers:
    """AC-3: An exception in one subscriber must not prevent other subscribers."""

    def test_failing_subscriber_does_not_prevent_second_subscriber(self) -> None:
        """Second subscriber still receives event even if first one raises."""
        bus = EventBus()
        second_received: list[object] = []

        def bad_callback(e: object) -> None:
            raise RuntimeError("subscriber error")

        bus.subscribe(PieceMoved, bad_callback)
        bus.subscribe(PieceMoved, lambda e: second_received.append(e))

        event = make_piecemoved_event()
        bus.publish(event)  # must not raise

        assert len(second_received) == 1

    def test_publish_does_not_raise_when_subscriber_raises(self) -> None:
        """publish() itself must not re-raise subscriber exceptions."""
        bus = EventBus()
        bus.subscribe(PieceMoved, lambda e: 1 / 0)  # ZeroDivisionError
        # publish must swallow the error
        bus.publish(make_piecemoved_event())


# ---------------------------------------------------------------------------
# US-302 AC-4: unsubscribe stops future delivery
# ---------------------------------------------------------------------------


class TestUnsubscribe:
    """AC-4: After unsubscribe, the callback must no longer be invoked."""

    def test_unsubscribed_callback_not_called(self) -> None:
        """Callback is not called after unsubscribe."""
        bus = EventBus()
        received: list[object] = []
        cb = lambda e: received.append(e)  # noqa: E731
        bus.subscribe(PieceMoved, cb)
        bus.unsubscribe(PieceMoved, cb)
        bus.publish(make_piecemoved_event())
        assert len(received) == 0

    def test_unsubscribe_only_removes_given_callback(self) -> None:
        """Unsubscribing one callback leaves other callbacks intact."""
        bus = EventBus()
        received_a: list[object] = []
        received_b: list[object] = []
        cb_a = lambda e: received_a.append(e)  # noqa: E731
        cb_b = lambda e: received_b.append(e)  # noqa: E731
        bus.subscribe(PieceMoved, cb_a)
        bus.subscribe(PieceMoved, cb_b)
        bus.unsubscribe(PieceMoved, cb_a)
        bus.publish(make_piecemoved_event())
        assert len(received_a) == 0
        assert len(received_b) == 1

    def test_unsubscribe_nonexistent_callback_does_not_raise(self) -> None:
        """Calling unsubscribe for a callback that was never registered is safe."""
        bus = EventBus()
        bus.unsubscribe(PieceMoved, lambda e: None)  # should not raise


# ---------------------------------------------------------------------------
# US-302 AC-5: All 8 event types are frozen dataclasses
# ---------------------------------------------------------------------------


class TestAllEightEventTypesDefined:
    """AC-5: All 8 domain event types must be importable and frozen."""

    @pytest.mark.parametrize(
        "event_class, kwargs",
        [
            (
                "PiecePlaced",
                lambda: {"pos": Position(8, 0), "piece": make_piece()},
            ),
            (
                "PieceMoved",
                lambda: {
                    "from_pos": Position(6, 4),
                    "to_pos": Position(5, 4),
                    "piece": make_piece(),
                },
            ),
            (
                "CombatResolved",
                lambda: {
                    "attacker": make_piece(Rank.CAPTAIN, PlayerSide.RED),
                    "defender": make_piece(Rank.MAJOR, PlayerSide.BLUE),
                    "winner": PlayerSide.RED,
                },
            ),
            (
                "TurnChanged",
                lambda: {"active_player": PlayerSide.BLUE},
            ),
            (
                "GameOver",
                lambda: {"winner": PlayerSide.RED, "reason": "Flag captured"},
            ),
            (
                "GameSaved",
                lambda: {"filepath": "/tmp/save.json"},
            ),
        ],
        ids=[
            "PiecePlaced",
            "PieceMoved",
            "CombatResolved",
            "TurnChanged",
            "GameOver",
            "GameSaved",
        ],
    )
    def test_event_is_frozen_dataclass(self, event_class: str, kwargs: object) -> None:
        """Each event must be instantiable and immutable (frozen dataclass)."""
        from dataclasses import FrozenInstanceError

        import src.application.events as ev_module

        cls = getattr(ev_module, event_class)
        instance = cls(**kwargs())  # type: ignore[operator]
        with pytest.raises(FrozenInstanceError):
            # Attempt to set an arbitrary attribute — must raise.
            object.__setattr__(instance, "_test_mutation", True)

    def test_invalid_move_event_exists(self) -> None:
        """InvalidMove event is importable from src.application.events."""
        from src.application.events import InvalidMove as IM

        assert IM is not None

    def test_game_loaded_event_exists(self) -> None:
        """GameLoaded event is importable from src.application.events."""
        from src.application.events import GameLoaded as GL

        assert GL is not None

    def test_user_story_example_subscribe_and_publish(self) -> None:
        """Verbatim example from US-302: subscribe to PieceMoved, publish, assert received."""
        bus = EventBus()
        received: list[object] = []
        scout = make_piece()
        bus.subscribe(PieceMoved, lambda e: received.append(e))
        bus.publish(PieceMoved(from_pos=Position(6, 4), to_pos=Position(5, 4), piece=scout))
        assert len(received) == 1
