"""Tests for alert CRUD operations."""

import json
import uuid

from axiom.core.db import Database
from axiom.core.models import Alert, AlertChannel, AlertEvent, UserProfile, eet_now


def _make_alert(user_id: str, ca: str = "token-alpha") -> Alert:
    return Alert(
        alert_id=str(uuid.uuid4()),
        user_id=user_id,
        ca=ca,
        chain="sol",
        alert_type="price_above",
        condition_json=json.dumps({"threshold": 1.0}),
        is_active=True,
        created_at=eet_now(),
        updated_at=eet_now(),
    )


def test_create_alert(user_db: Database) -> None:
    """Test creating a new alert."""
    profile = UserProfile(
        user_id="user-123",
        email="test@example.com",
        created_at=eet_now(),
    )
    alert = _make_alert("user-123")

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert)

        result = user_db.get_alert(alert.alert_id)

    assert result is not None
    assert result["alert_type"] == "price_above"
    assert result["is_active"] is True


def test_update_alert(user_db: Database) -> None:
    """Test updating an alert."""
    profile = UserProfile(
        user_id="user-456",
        email="test@example.com",
        created_at=eet_now(),
    )
    alert = _make_alert("user-456")

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert)

        alert.is_active = False
        alert.trigger_count = 5
        alert.updated_at = eet_now()

        user_db.update_alert(alert)
        result = user_db.get_alert(alert.alert_id)

    assert result is not None
    assert result["is_active"] is False
    assert result["trigger_count"] == 5


def test_delete_alert(user_db: Database) -> None:
    """Test deleting an alert."""
    profile = UserProfile(
        user_id="user-789",
        email="test@example.com",
        created_at=eet_now(),
    )
    alert = _make_alert("user-789")

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert)

        assert user_db.get_alert(alert.alert_id) is not None

        user_db.delete_alert(alert.alert_id)

        assert user_db.get_alert(alert.alert_id) is None


def test_list_alerts(user_db: Database) -> None:
    """Test listing user's alerts."""
    profile = UserProfile(
        user_id="user-111",
        email="test@example.com",
        created_at=eet_now(),
    )

    alert1 = _make_alert("user-111", "token-alpha")
    alert2 = _make_alert("user-111", "token-beta")

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert1)
        user_db.create_alert(alert2)

        alerts = user_db.list_alerts("user-111")

    assert len(alerts) == 2
    cas = {a["ca"] for a in alerts}
    assert cas == {"token-alpha", "token-beta"}


def test_list_alerts_with_filters(user_db: Database) -> None:
    """Test listing alerts with filters."""
    profile = UserProfile(
        user_id="user-222",
        email="test@example.com",
        created_at=eet_now(),
    )

    alert1 = _make_alert("user-222", "token-alpha")
    alert1.is_active = True

    alert2 = _make_alert("user-222", "token-beta")
    alert2.is_active = False

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert1)
        user_db.create_alert(alert2)

        active_alerts = user_db.list_alerts("user-222", is_active=True)
        assert len(active_alerts) == 1
        assert active_alerts[0]["ca"] == "token-alpha"

        alpha_alerts = user_db.list_alerts("user-222", ca="token-alpha")
        assert len(alpha_alerts) == 1
        assert alpha_alerts[0]["ca"] == "token-alpha"


def test_add_alert_channel(user_db: Database) -> None:
    """Test adding a delivery channel to an alert."""
    profile = UserProfile(
        user_id="user-333",
        email="test@example.com",
        created_at=eet_now(),
    )
    alert = _make_alert("user-333")

    channel = AlertChannel(
        alert_id=alert.alert_id,
        channel_type="email",
        channel_config_json=json.dumps({"email": "user@example.com"}),
        is_enabled=True,
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert)
        user_db.add_alert_channel(channel)

        channels = user_db.list_alert_channels(alert.alert_id)

    assert len(channels) == 1
    assert channels[0]["channel_type"] == "email"
    assert channels[0]["is_enabled"] is True


def test_remove_alert_channel(user_db: Database) -> None:
    """Test removing a delivery channel from an alert."""
    profile = UserProfile(
        user_id="user-444",
        email="test@example.com",
        created_at=eet_now(),
    )
    alert = _make_alert("user-444")

    channel = AlertChannel(
        alert_id=alert.alert_id,
        channel_type="webhook",
        channel_config_json=json.dumps({"url": "https://example.com/webhook"}),
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert)
        user_db.add_alert_channel(channel)
        assert len(user_db.list_alert_channels(alert.alert_id)) == 1

        user_db.remove_alert_channel(alert.alert_id, "webhook")

        channels_after = user_db.list_alert_channels(alert.alert_id)
        assert len(channels_after) == 0


def test_log_alert_event(user_db: Database) -> None:
    """Test logging an alert event."""
    profile = UserProfile(
        user_id="user-555",
        email="test@example.com",
        created_at=eet_now(),
    )
    alert = _make_alert("user-555")

    event = AlertEvent(
        event_id=str(uuid.uuid4()),
        alert_id=alert.alert_id,
        triggered_at=eet_now(),
        condition_met_json=json.dumps({"price": 1.5, "threshold": 1.0}),
        delivery_status="pending",
        delivery_attempts=0,
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert)
        user_db.log_alert_event(event)

        events = user_db.list_alert_events(alert.alert_id)

    assert len(events) == 1
    assert events[0]["delivery_status"] == "pending"
    assert events[0]["delivery_attempts"] == 0


def test_update_alert_event(user_db: Database) -> None:
    """Test updating an alert event."""
    profile = UserProfile(
        user_id="user-666",
        email="test@example.com",
        created_at=eet_now(),
    )
    alert = _make_alert("user-666")

    event = AlertEvent(
        event_id=str(uuid.uuid4()),
        alert_id=alert.alert_id,
        triggered_at=eet_now(),
        condition_met_json=json.dumps({}),
        delivery_status="pending",
        delivery_attempts=0,
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert)
        user_db.log_alert_event(event)

        event.delivery_status = "delivered"
        event.delivery_attempts = 1
        event.delivered_at = eet_now()

        user_db.update_alert_event(event)
        events = user_db.list_alert_events(alert.alert_id)

    assert len(events) == 1
    assert events[0]["delivery_status"] == "delivered"
    assert events[0]["delivery_attempts"] == 1
    assert events[0]["delivered_at"] is not None


def test_alert_cascade_delete(user_db: Database) -> None:
    """Test that deleting an alert cascades to channels and events."""
    profile = UserProfile(
        user_id="user-777",
        email="test@example.com",
        created_at=eet_now(),
    )
    alert = _make_alert("user-777")

    channel = AlertChannel(
        alert_id=alert.alert_id,
        channel_type="email",
        channel_config_json=json.dumps({"email": "test@example.com"}),
    )

    event = AlertEvent(
        event_id=str(uuid.uuid4()),
        alert_id=alert.alert_id,
        triggered_at=eet_now(),
        condition_met_json=json.dumps({}),
        delivery_status="delivered",
    )

    with user_db:
        user_db.upsert_user_profile(profile)
        user_db.create_alert(alert)
        user_db.add_alert_channel(channel)
        user_db.log_alert_event(event)

        assert len(user_db.list_alert_channels(alert.alert_id)) == 1
        assert len(user_db.list_alert_events(alert.alert_id)) == 1

        user_db.delete_alert(alert.alert_id)

        assert len(user_db.list_alert_channels(alert.alert_id)) == 0
        assert len(user_db.list_alert_events(alert.alert_id)) == 0
