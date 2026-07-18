from __future__ import annotations

from pathlib import Path

import pytest

from spine_sim.foundation.demo_validation_only import generate_validation_bundle


@pytest.fixture(scope="session")
def demo_bundle(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return generate_validation_bundle(
        tmp_path_factory.mktemp("m00-demo") / "M00_VALIDATION_ONLY.spine-result"
    )
