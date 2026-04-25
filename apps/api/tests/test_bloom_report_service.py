from datetime import datetime, timezone

from app.errors import AppError
from app.integrations.fake_verification_client import FakeVerificationClient
from app.integrations.unconfigured_verification_client import UnconfiguredVerificationClient
from app.repositories.state_repository import StateRepository
from app.settings import get_settings
from app.services.bloom_report_service import BloomReportService


from app.dependencies import get_bloom_report_service


def fixed_now() -> datetime:
    return datetime(2026, 4, 25, 12, 0, tzinfo=timezone.utc)


def make_service(tmp_path) -> BloomReportService:
    return BloomReportService(
        state_repository=StateRepository(tmp_path / "state.json"),
        now_fn=fixed_now,
    )


class FakeBloomNarrativeClient:
    mode = "fake"

    def generate_weekly_report(self, *, report_context: dict) -> dict:
        return {
            "highlights": [
                {"title": "Family win", "detail": "Two gigs turned effort into EUR 12.50 this week."},
                {"title": "Savings spark", "detail": "Mila is building momentum toward her next goal."},
            ],
            "savings_insight": "EUR 12.50 earned means EUR 6.25 could go straight into savings this week.",
            "conversation_starter": "Which reward felt most worth the effort this week?",
            "raw_provider": "fake",
            "raw_model": "fake-bloom-v1",
        }


class BrokenBloomNarrativeClient:
    mode = "real"

    def generate_weekly_report(self, *, report_context: dict) -> dict:
        raise RuntimeError("narrative unavailable")


class RealBloomNarrativeClient:
    mode = "real"

    def generate_weekly_report(self, *, report_context: dict) -> dict:
        return {
            "highlights": [
                {"title": "Weekly highlight", "detail": "Paid gigs helped Mila move closer to her next savings goal."}
            ],
            "savings_insight": "This week showed that small gigs can stack into meaningful savings progress.",
            "conversation_starter": "What should next week's gig money be saved for first?",
            "raw_provider": "lmstudio",
            "raw_model": "qwen2.5-vl",
        }


def seed_weekly_state(tmp_path) -> dict:
    repository = StateRepository(tmp_path / "state.json")
    state = repository.load()
    state["balances"]["kid_001"] = {"amount": "35.00", "currency": "EUR", "source": "fake"}

    state["gigs"]["gig_001"].update(
        {
            "status": "paid",
            "reward_amount": "5.00",
            "title": "Clean your room",
            "payment_id": "payment_001",
            "updated_at": "2026-04-22T10:00:00+00:00",
        }
    )
    state["payments"]["payment_001"] = {
        "id": "payment_001",
        "gig_id": "gig_001",
        "amount": "5.00",
        "currency": "EUR",
        "from_monetary_account_id": "fake_parent_account",
        "to_monetary_account_id": "fake_kid_account",
        "bunq_payment_id": "fake_payment_001",
        "status": "succeeded",
        "created_at": "2026-04-22T10:00:00+00:00",
        "updated_at": "2026-04-22T10:00:00+00:00",
    }

    state["gigs"]["gig_002"] = {
        "id": "gig_002",
        "family_id": "family_001",
        "title": "Walk the dog",
        "description": "Take the dog around the block.",
        "reward_amount": "7.50",
        "currency": "EUR",
        "status": "paid",
        "created_by_user_id": "parent_001",
        "claimed_by_user_id": "kid_001",
        "verification_checklist": ["dog walked"],
        "before_photo_id": None,
        "after_photo_id": None,
        "verification_result_id": None,
        "payment_id": "payment_002",
        "created_at": "2026-04-24T08:00:00+00:00",
        "updated_at": "2026-04-24T09:00:00+00:00",
    }
    state["payments"]["payment_002"] = {
        "id": "payment_002",
        "gig_id": "gig_002",
        "amount": "7.50",
        "currency": "EUR",
        "from_monetary_account_id": "fake_parent_account",
        "to_monetary_account_id": "fake_kid_account",
        "bunq_payment_id": "fake_payment_002",
        "status": "succeeded",
        "created_at": "2026-04-24T09:00:00+00:00",
        "updated_at": "2026-04-24T09:00:00+00:00",
    }

    state["gigs"]["gig_003"] = {
        "id": "gig_003",
        "family_id": "family_001",
        "title": "Old gardening task",
        "description": "Pull weeds in the garden.",
        "reward_amount": "9.00",
        "currency": "EUR",
        "status": "paid",
        "created_by_user_id": "parent_001",
        "claimed_by_user_id": "kid_001",
        "verification_checklist": ["weeds removed"],
        "before_photo_id": None,
        "after_photo_id": None,
        "verification_result_id": None,
        "payment_id": "payment_003",
        "created_at": "2026-04-10T08:00:00+00:00",
        "updated_at": "2026-04-10T09:00:00+00:00",
    }
    state["payments"]["payment_003"] = {
        "id": "payment_003",
        "gig_id": "gig_003",
        "amount": "9.00",
        "currency": "EUR",
        "from_monetary_account_id": "fake_parent_account",
        "to_monetary_account_id": "fake_kid_account",
        "bunq_payment_id": "fake_payment_003",
        "status": "succeeded",
        "created_at": "2026-04-10T09:00:00+00:00",
        "updated_at": "2026-04-10T09:00:00+00:00",
    }

    repository.save(state)
    return state


def test_bloom_report_aggregates_current_week_and_deterministic_copy(tmp_path):
    seed_weekly_state(tmp_path)
    service = make_service(tmp_path)

    report = service.get_weekly_report()

    assert report["period"] == {"start_date": "2026-04-19", "end_date": "2026-04-25"}
    assert report["stats"]["gigs_completed"] == 2
    assert report["stats"]["money_earned"] == {"amount": "12.50", "currency": "EUR"}
    assert report["stats"]["average_reward"] == {"amount": "6.25", "currency": "EUR"}
    assert report["stats"]["current_balance"] == {"amount": "35.00", "currency": "EUR", "source": "fake"}
    assert report["highlights"][0]["title"] == "Top earning gig"
    assert report["highlights"][0]["detail"] == "Walk the dog earned EUR 7.50 this week."
    assert report["savings_insight"] == "You earned EUR 12.50 this week. Saving half would set aside EUR 6.25 for the next goal."
    assert report["conversation_starter"] == "Which goal feels worth saving for with next week's gigs?"


def test_bloom_report_returns_zeroed_summary_when_no_paid_gigs_exist(tmp_path):
    service = make_service(tmp_path)

    report = service.get_weekly_report()

    assert report["stats"]["gigs_completed"] == 0
    assert report["stats"]["money_earned"] == {"amount": "0.00", "currency": "EUR"}
    assert report["stats"]["average_reward"] == {"amount": "0.00", "currency": "EUR"}
    assert report["highlights"][0]["title"] == "Weekly reset"
    assert report["savings_insight"] == "No paid gigs landed this week yet. One completed gig can start the savings habit again."


def test_bloom_report_can_layer_provider_narrative_over_aggregated_stats(tmp_path):
    seed_weekly_state(tmp_path)
    service = BloomReportService(
        state_repository=StateRepository(tmp_path / "state.json"),
        narrative_client=RealBloomNarrativeClient(),
        now_fn=fixed_now,
    )

    report = service.get_weekly_report()

    assert report["highlights"][0]["title"] == "Weekly highlight"
    assert report["savings_insight"] == "This week showed that small gigs can stack into meaningful savings progress."
    assert report["conversation_starter"] == "What should next week's gig money be saved for first?"
    assert report["mode"] == "real"
    assert report["fallback_mode"] is False


def test_fake_bloom_narrative_uses_report_context_for_zero_week(tmp_path):
    service = BloomReportService(
        state_repository=StateRepository(tmp_path / "state.json"),
        narrative_client=FakeVerificationClient(),
        now_fn=fixed_now,
    )

    report = service.get_weekly_report()

    assert report["stats"]["gigs_completed"] == 0
    assert report["highlights"][0]["title"] == "Weekly reset"
    assert "12.50" not in report["highlights"][0]["detail"]
    assert "12.50" not in report["savings_insight"]


def test_bloom_report_can_fallback_when_narrative_generation_fails(tmp_path):
    seed_weekly_state(tmp_path)
    service = BloomReportService(
        state_repository=StateRepository(tmp_path / "state.json"),
        narrative_client=BrokenBloomNarrativeClient(),
        allow_ai_fallback=True,
        now_fn=fixed_now,
    )

    report = service.get_weekly_report()

    assert report["mode"] == "ai_fallback"
    assert report["fallback_mode"] is True
    assert report["highlights"][0]["title"] == "Top earning gig"


def test_bloom_report_can_fallback_when_ai_is_unconfigured(tmp_path):
    seed_weekly_state(tmp_path)
    service = BloomReportService(
        state_repository=StateRepository(tmp_path / "state.json"),
        narrative_client=UnconfiguredVerificationClient(provider="lmstudio"),
        allow_ai_fallback=True,
        now_fn=fixed_now,
    )

    report = service.get_weekly_report()

    assert report["mode"] == "ai_fallback"
    assert report["fallback_mode"] is True
    assert report["highlights"][0]["title"] == "Top earning gig"


def test_bloom_report_raises_retryable_error_without_fallback(tmp_path):
    seed_weekly_state(tmp_path)
    service = BloomReportService(
        state_repository=StateRepository(tmp_path / "state.json"),
        narrative_client=BrokenBloomNarrativeClient(),
        allow_ai_fallback=False,
        now_fn=fixed_now,
    )

    try:
        service.get_weekly_report()
    except AppError as exc:
        assert exc.code == "report_generation_failed"
        assert exc.status_code == 502
        assert exc.retryable is True
    else:
        raise AssertionError("Expected AppError for failed weekly report generation without fallback")


def test_dependency_selects_unconfigured_client_for_bloom_report_when_ai_is_unconfigured(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    monkeypatch.setenv("BLOOM_AI_PROVIDER", "lmstudio")
    monkeypatch.setenv("BLOOM_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.setenv("BLOOM_LMSTUDIO_MODEL", "")
    monkeypatch.setenv("BLOOM_USE_FAKE_BUNQ", "true")
    monkeypatch.setenv("BLOOM_STATE_PATH", str(state_dir / "state.json"))
    monkeypatch.setenv("BLOOM_UPLOAD_DIR", str(upload_dir))

    get_settings.cache_clear()
    get_bloom_report_service.cache_clear()

    service = get_bloom_report_service()

    assert isinstance(service.narrative_client, UnconfiguredVerificationClient)

    get_settings.cache_clear()
    get_bloom_report_service.cache_clear()
