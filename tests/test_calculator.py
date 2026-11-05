import base64
import math
import subprocess
from types import SimpleNamespace

import pytest

from games.expedition33.calculator import save_import
from games.expedition33.calculator.core import CALCULATOR_DATA, DEFAULT_SKILLS, calculate_damage, resolve_affinity
from games.expedition33.calculator.logic import calculate_skill_result, can_satisfy_lune_stains


@pytest.mark.parametrize("character, multiplier", [
    ("gustave", 1.5), ("lune", 3.6), ("maelle", 2.4),
    ("monoco", 1.5), ("sciel", 10.0), ("verso", 4.9),
])
def test_default_skill_damage(character, multiplier):
    row = CALCULATOR_DATA[character]["skills"][DEFAULT_SKILLS[character]]
    result = calculate_skill_result(character, row, {})
    assert result["multiplier"] == pytest.approx(multiplier)
    assert calculate_damage(1000, result["multiplier"]) == pytest.approx(multiplier * 1000)


@pytest.mark.parametrize("character", CALCULATOR_DATA)
def test_all_loaded_skills_have_finite_results(character):
    for row in CALCULATOR_DATA[character]["records"]:
        result = calculate_skill_result(character, row, {})
        assert result["multiplier"] is None or math.isfinite(result["multiplier"]), row["Skill"]


@pytest.mark.parametrize("charges, expected", [(-1, 1.5), (5, 3.0), (10, 4.5), (999, 4.5)])
def test_overcharge_scaling_and_bounds(charges, expected):
    row = CALCULATOR_DATA["gustave"]["skills"][DEFAULT_SKILLS["gustave"]]
    assert calculate_skill_result("gustave", row, {"charges": charges})["multiplier"] == pytest.approx(expected)


@pytest.mark.parametrize("element, affinity, factor", [("Fire", "weak", 1.5), ("Ice", "resist", 0.5), ("Physical", "weak", 1), ("Fire", "invalid", 1)])
def test_element_affinity(element, affinity, factor):
    assert resolve_affinity({"Damage Element": element}, affinity)["factor"] == factor


def test_light_stains_are_consumed_as_wildcards_only_once():
    assert can_satisfy_lune_stains("Fire|Ice", {"light_stains": 2})
    assert not can_satisfy_lune_stains("Fire|Ice", {"light_stains": 1})
    assert not can_satisfy_lune_stains("Light|Fire", {"light_stains": 1})


def test_upload_decodes_exact_binary():
    raw = b"GVAS\x00\xff\x01"
    contents = "data:application/octet-stream;base64," + base64.b64encode(raw).decode()
    assert save_import.decode_upload_contents(contents) == raw


@pytest.mark.parametrize("contents", ["", "data:;base64,", "data:;base64,%%%", "data:;base64,a"])
def test_malformed_upload_is_rejected(contents):
    with pytest.raises(save_import.SaveImportError):
        save_import.decode_upload_contents(contents)


def test_oversized_upload_rejected_before_decoding(monkeypatch):
    monkeypatch.setattr(save_import, "MAX_SAVE_UPLOAD_BYTES", 3)
    with pytest.raises(save_import.SaveImportError, match="too large"):
        save_import.decode_upload_contents("data:;base64," + base64.b64encode(b"1234").decode())


def test_wrong_file_type_never_reaches_converter(monkeypatch):
    def unexpected_conversion(_):
        pytest.fail("Invalid extensions must be rejected before running uesave")
    monkeypatch.setattr(save_import, "convert_save_bytes_to_json", unexpected_conversion)
    with pytest.raises(save_import.SaveImportError, match="Only .sav"):
        save_import.parse_uploaded_save("data:;base64,R1ZBUw==", "bad.exe")


@pytest.mark.parametrize("outcome, message", [
    (subprocess.TimeoutExpired("uesave", 10), "too long"),
    (SimpleNamespace(returncode=1, stderr=b"invalid save", stdout=b""), "could not be parsed"),
    (SimpleNamespace(returncode=0, stderr=b"", stdout=b"not json"), "invalid JSON"),
])
def test_converter_failures_are_user_errors(monkeypatch, outcome, message):
    monkeypatch.setattr(save_import, "resolve_uesave_binary", lambda: "/tmp/fake-uesave")
    def run(*args, **kwargs):
        assert args[0] == ["/tmp/fake-uesave", "to-json", "--no-warn", "-i", "-", "-o", "-"]
        assert kwargs["timeout"] == 10
        assert kwargs["input"] == b"GVAS"
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
    monkeypatch.setattr(save_import.subprocess, "run", run)
    with pytest.raises(save_import.SaveImportError, match=message):
        save_import.convert_save_bytes_to_json(b"GVAS")
