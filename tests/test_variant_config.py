from pathlib import Path

from rattler_build_conda_compat.loader import load_yaml
from rattler_build_conda_compat.variant_config import variant_combinations

test_data = Path(__file__).parent / "data"


def test_variant_config(snapshot) -> None:
    variants = load_yaml((test_data / "variant_config_zip.yaml").read_text())

    assert snapshot == variant_combinations(variants)
