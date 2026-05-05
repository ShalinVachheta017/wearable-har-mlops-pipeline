import json

import pytest

from src.api import app as api_app
from src.components.model_inference import ACTIVITY_CLASSES as INF_CLASSES
from src.components.model_evaluation import ACTIVITY_CLASSES as EVAL_CLASSES
from src.utils.label_mapping import load_activity_mapping


def test_single_source_label_mapping_consistent_across_entrypoints():
    label_to_activity, _ = load_activity_mapping()
    assert INF_CLASSES == label_to_activity
    assert EVAL_CLASSES == label_to_activity
    assert api_app.ACTIVITY_CLASSES == label_to_activity


def test_label_mapping_fail_fast_on_inconsistent_metadata(tmp_path):
    bad_config = {
        "activity_to_label": {
            "ear_rubbing": 0,
            "forehead_rubbing": 2,
        },
        "label_to_activity": {
            "0": "ear_rubbing",
            "1": "forehead_rubbing",
        },
    }
    p = tmp_path / "bad_config.json"
    p.write_text(json.dumps(bad_config), encoding="utf-8")

    with pytest.raises(ValueError):
        load_activity_mapping(metadata_path=p)
