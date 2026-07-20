"""Tests for the nightly eval runner."""

import pytest


def test_run_nightly_writes_last_ok_on_green(tmp_path, monkeypatch):
    """The synthetic golden set is perfect -> ``last_ok`` is written."""
    from ops.eval import run_nightly

    marker = tmp_path / "last_ok"
    monkeypatch.setattr(run_nightly, "LAST_OK_MARKER", marker)
    run_nightly.main()
    assert marker.exists()


def test_run_nightly_fails_when_threshold_too_high(tmp_path, monkeypatch):
    """A threshold above 1.0 (impossible) fails the runner."""
    import yaml

    from ops.eval import run_nightly

    thresholds = tmp_path / "thresholds.yaml"
    thresholds.write_text(yaml.safe_dump({"email_parse_macro_f1": 1.5}))
    marker = tmp_path / "last_ok"
    monkeypatch.setattr(run_nightly, "THRESHOLDS_PATH", thresholds)
    monkeypatch.setattr(run_nightly, "LAST_OK_MARKER", marker)
    with pytest.raises(SystemExit):
        run_nightly.main()
    assert not marker.exists()
