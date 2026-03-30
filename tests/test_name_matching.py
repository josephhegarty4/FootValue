from src.utils.name_matching import build_name_mapping


def test_manual_correction_priority() -> None:
    source = ["M. Ødegaard"]
    target = ["Martin Odegaard"]
    manual = {"m odegaard": "Martin Odegaard"}

    mapping = build_name_mapping(source_names=source, target_names=target, manual_corrections=manual)

    result = mapping["M. Ødegaard"]
    assert result.matched_name == "Martin Odegaard"
    assert result.method == "manual"
