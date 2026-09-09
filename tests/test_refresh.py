from __future__ import annotations

import json
from pathlib import Path

from datetime import date

from app.cli import main
from app.services.refresh import HORIZON_MIDYEAR, HORIZON_YEAR_END, classify_horizon, refresh_families
from app.sources.american_funds import AmericanFundsSource
from app.sources.base import FetchResult


def test_cli_refresh_fixture_writes_summary(engine, tmp_path: Path, capsys) -> None:
    json_path = tmp_path / "refresh-summary.json"
    md_path = tmp_path / "refresh-summary.md"
    code = main(
        [
            "refresh",
            "--mode",
            "fixture",
            "--output",
            str(json_path),
            "--markdown",
            str(md_path),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "families_attempted:" in out
    assert "live_vs_fixture:" in out

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["mode"] == "fixture"
    assert payload["families_attempted"] == 113
    assert payload["created"] > 0
    assert payload["errors"] == []
    assert payload["live_vs_fixture"]["live"] == 0
    assert payload["live_vs_fixture"]["fixture"] == 113
    assert payload["nav"]["mode"] == "fixture"
    assert payload["nav"]["tickers_attempted"] > 0
    assert payload["nav"]["created"] + payload["nav"]["updated"] + payload["nav"]["unchanged"] > 0
    for ticker in ("ABALX", "VFIAX", "SPY", "DBEF"):
        assert payload["nav"]["sample"][ticker]["nav_per_share"] is not None
    assert "Weekly NAV refresh" in md
    assert "Weekly NAV refresh" in out
    assert payload["midyear_created"] > 0
    assert payload["year_end_created"] > 0
    md = md_path.read_text(encoding="utf-8")
    assert "Weekly ingest refresh" in md
    assert "Midyear:" in md
    assert "Year-end:" in md
    assert "midyear:" in out
    assert "year_end:" in out


def test_cli_refresh_single_family(engine, capsys) -> None:
    code = main(["refresh", "--mode", "fixture", "--family", "american_funds"])
    assert code == 0
    out = capsys.readouterr().out
    assert "families_attempted: 1" in out
    assert "american_funds" in out


def test_refresh_live_falls_back_to_fixture(session, monkeypatch) -> None:
    real_fetch = AmericanFundsSource.fetch

    def boom(self, *, mode: str = "fixture"):
        if mode == "live":
            raise RuntimeError("403 Forbidden")
        return real_fetch(self, mode="fixture")

    monkeypatch.setattr(AmericanFundsSource, "fetch", boom)
    summary = refresh_families(session, mode="auto", slugs=["american_funds"])
    session.commit()
    assert summary.hard_failure is False
    assert summary.errors == []
    row = summary.families[0]
    assert row.slug == "american_funds"
    assert row.status == "fallback"
    assert row.mode_used == "fixture"
    assert row.created > 0
    assert "403" in (row.notes[0] if row.notes else "")
    assert summary.live_vs_fixture == {"live": 0, "fixture": 1}


def test_refresh_all_failed_is_hard_failure(session, monkeypatch) -> None:
    def boom(self, *, mode: str = "fixture"):
        raise RuntimeError("parse exploded")

    monkeypatch.setattr(AmericanFundsSource, "fetch", boom)
    summary = refresh_families(session, mode="fixture", slugs=["american_funds"])
    assert summary.hard_failure is True
    assert summary.errors == ["american_funds"]
    assert summary.created == 0


def test_cli_refresh_hard_failure_exits_nonzero(engine, monkeypatch) -> None:
    def boom(self, *, mode: str = "fixture"):
        raise RuntimeError("parse exploded")

    monkeypatch.setattr(AmericanFundsSource, "fetch", boom)
    code = main(["refresh", "--mode", "fixture", "--family", "american_funds"])
    assert code == 1


def test_refresh_fixture_only_does_not_call_live(session, monkeypatch) -> None:
    calls: list[str] = []
    real_fetch = AmericanFundsSource.fetch

    def wrapped(self, *, mode: str = "fixture"):
        calls.append(mode)
        return real_fetch(self, mode=mode)

    monkeypatch.setattr(AmericanFundsSource, "fetch", wrapped)
    summary = refresh_families(session, mode="fixture", slugs=["american_funds"])
    assert calls == ["fixture"]
    assert summary.families[0].mode_used == "fixture"
    assert summary.families[0].status == "success"


def test_classify_horizon_url_and_month() -> None:
    assert (
        classify_horizon(
            source_url="https://www.capitalgroup.com/individual/service-and-support/tax-center/midyear-cap-gains.html",
            as_of=date(2026, 1, 22),
        )
        == HORIZON_MIDYEAR
    )
    assert (
        classify_horizon(
            source_url="https://www.capitalgroup.com/individual/service-and-support/tax-center/2025-year-end-distributions.html",
            as_of=date(2026, 6, 16),
        )
        == HORIZON_YEAR_END
    )
    assert (
        classify_horizon(
            source_url="https://www.ishares.com/us/capital-gains-distributions",
            as_of=date(2026, 9, 7),
            ex_date=date(2026, 6, 15),
        )
        == HORIZON_MIDYEAR
    )
    assert (
        classify_horizon(
            source_url="https://www.ishares.com/us/capital-gains-distributions",
            as_of=date(2026, 9, 7),
            ex_date=date(2025, 12, 1),
        )
        == HORIZON_YEAR_END
    )
    assert (
        classify_horizon(
            source_url="https://www.allspringglobal.com/investments/equity/mutual-funds/special-mid-cap-value/",
            as_of=date(2025, 12, 15),
        )
        == HORIZON_YEAR_END
    )
    assert classify_horizon(source_url="https://example.invalid/tax", as_of=date(2026, 9, 1)) is None


def test_refresh_american_funds_breaks_out_midyear(session) -> None:
    summary = refresh_families(session, mode="fixture", slugs=["american_funds"])
    row = summary.families[0]
    assert row.midyear_created > 0
    assert row.year_end_created > 0
    assert summary.midyear_created == row.midyear_created
    assert summary.year_end_created == row.year_end_created


def test_refresh_live_success_counts_as_live(session, monkeypatch) -> None:
    real_fetch = AmericanFundsSource.fetch

    def fake_live(self, *, mode: str = "fixture"):
        if mode != "live":
            return FetchResult(records=[], notes=["unexpected fixture"])
        result = real_fetch(self, mode="fixture")
        result.notes = [note for note in result.notes if "fixture" not in note.lower()]
        result.notes.append("live html parsed")
        return result

    monkeypatch.setattr(AmericanFundsSource, "fetch", fake_live)
    summary = refresh_families(session, mode="live", slugs=["american_funds"])
    row = summary.families[0]
    assert row.status == "success"
    assert row.mode_used == "live"
    assert row.created > 0
    assert summary.live_vs_fixture == {"live": 1, "fixture": 0}
