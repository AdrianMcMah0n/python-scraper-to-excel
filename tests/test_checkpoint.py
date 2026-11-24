"""The checkpoint must survive odd characters in the data and a run killed halfway through a write."""
import json

from scraper.run import load_checkpoint


def test_checkpoint_survives_line_separator_and_partial_line(tmp_path):
    cp = tmp_path / "checkpoint.jsonl"
    good = {"url": "u1", "description": "first line second line"}
    cp.write_text(json.dumps(good, ensure_ascii=False) + "\n" + '{"url": "u2", "descr', encoding="utf-8")
    done = load_checkpoint(cp)
    assert list(done) == ["u1"]
    assert done["u1"]["description"] == "first line second line"
