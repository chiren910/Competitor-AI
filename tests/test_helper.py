from utils.helper import safe_parse_json, clean_jsonb_field, prepare_data_for_jsonb


def test_safe_parse_json_handles_strings_and_none():
    assert safe_parse_json(None) is None
    assert safe_parse_json('{"a": 1}') == {"a": 1}
    assert safe_parse_json("not-json") == "not-json"
    assert safe_parse_json({"a": 1}) == {"a": 1}


def test_clean_jsonb_field():
    assert clean_jsonb_field(None) is None
    assert clean_jsonb_field([]) is None
    assert clean_jsonb_field("") is None
    assert clean_jsonb_field('{"a": 1}') == {"a": 1}


def test_prepare_data_for_jsonb_nested():
    data = {
        "name": "Acme",
        "phone": "",
        "services": [],
        "tags": ["a", "b"],
        "profile": {
            "about": "",
            "social": ["x"],
            "metadata": None,
        },
    }
    cleaned = prepare_data_for_jsonb(data)
    assert cleaned["name"] == "Acme"
    assert cleaned["phone"] is None
    assert cleaned["services"] is None
    assert cleaned["tags"] == ["a", "b"]
    assert cleaned["profile"]["about"] is None
    assert cleaned["profile"]["social"] == ["x"]
    assert cleaned["profile"]["metadata"] is None


def test_prepare_data_for_jsonb_empty():
    assert prepare_data_for_jsonb(None) is None
    # Empty dicts are treated as "no data" -> NULL (consistent with other empty values)
    assert prepare_data_for_jsonb({}) is None