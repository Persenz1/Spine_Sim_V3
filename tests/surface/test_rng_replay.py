from __future__ import annotations

import dataclasses
import math

import pytest

from spine_sim.foundation.errors import ContractViolation
from spine_sim.surface.contracts import (
    NORMAL_TRANSFORM_ID,
    RNG_PROFILE_ID,
    make_latent_noise_identity,
)
from spine_sim.surface.rng import (
    CounterAddress,
    KeyIdentity,
    Philox4x64,
    counter_words,
    encode_signed_zigzag,
    philox4x64_10,
    uint64_to_open_uniform,
)


def test_random123_philox4x64_10_zero_reference_vector() -> None:
    """Lock the published Random123 permutation independently of M01 keying."""

    assert philox4x64_10((0, 0, 0, 0), (0, 0)) == (
        0x16554D9ECA36314C,
        0xDB20FE9D672D0FDC,
        0xD7E772CEE186176B,
        0x7E68B68AEC7BA23B,
    )


def test_m01_key_counter_block_and_normal_golden_vector() -> None:
    identity = KeyIdentity(
        root_seed=0x0123456789ABCDEF0123456789ABCDEF,
        surface_seed_index=7,
        latent_noise_namespace="m01.surface.latent.test",
        frequency_band=3,
        component_or_pair_role="real_fourier_cos_sin_pair_v1",
    )
    assert identity.key_words() == (
        0xCEAA092B508617CA,
        0xA981E81417680E62,
    )
    latent = make_latent_noise_identity(
        0x0123456789ABCDEF0123456789ABCDEF,
        7,
        latent_noise_namespace="m01.surface.latent.test",
    )
    rng = Philox4x64.from_latent_identity(
        latent,
        3,
        "real_fourier_cos_sin_pair_v1",
    )
    assert rng.block(-17, 23, 5) == (
        0x8C225064E142BA5F,
        0x1FC50C0F228D0CD9,
        0x58CEA940B007FED3,
        0xD77EB0016DACA35D,
    )
    assert tuple(value.hex() for value in rng.normal_pair(-17, 23, 5, 0)) == (
        "0x1.8faf43b74bd23p-1",
        "0x1.8b3120cebf6c1p-1",
    )
    assert tuple(value.hex() for value in rng.normal_pair(-17, 23, 5, 1)) == (
        "0x1.9634542a4b89ap-1",
        "-0x1.3846c67445e4dp+0",
    )
    assert latent.seed_id == (
        "seed:893d1c2d3431aa1531e1c2dcc7e93b8472e54d84f0f636cededd7570f479a7e7"
    )
    assert latent.latent_noise_id == (
        "latent_noise:6352a246cea06e784fba2958ead37e718ca93d62a564d31ba415ee1b11e8cfaa"
    )


def test_seed_namespace_and_profile_are_part_of_replay_identity() -> None:
    first = make_latent_noise_identity(123456789, 4)
    replay = make_latent_noise_identity(123456789, 4)
    next_index = make_latent_noise_identity(123456789, 5)
    next_root = make_latent_noise_identity(123456790, 4)
    next_namespace = make_latent_noise_identity(
        123456789,
        4,
        latent_noise_namespace="m01.surface.latent.alternate",
    )

    assert first == replay
    assert first.rng_profile_id == RNG_PROFILE_ID
    assert first.normal_transform_id == NORMAL_TRANSFORM_ID
    assert first.seed_id != next_index.seed_id != next_root.seed_id
    assert first.seed_id == next_namespace.seed_id
    assert first.latent_noise_id != next_namespace.latent_noise_id
    with pytest.raises(ContractViolation):
        dataclasses.replace(first, rng_profile_id="unversioned_rng")
    with pytest.raises(ContractViolation):
        dataclasses.replace(first, normal_transform_id="unversioned_normal")


def test_counter_encoding_is_global_signed_and_collision_free_at_boundaries() -> None:
    assert [encode_signed_zigzag(value) for value in (0, -1, 1, -2, 2)] == [0, 1, 2, 3, 4]
    addresses = {
        CounterAddress(-(1 << 63), (1 << 63) - 1, 0).to_bytes(),
        CounterAddress((1 << 63) - 1, -(1 << 63), 0).to_bytes(),
        CounterAddress(-(1 << 63), (1 << 63) - 1, 1).to_bytes(),
    }
    assert len(addresses) == 3
    assert len(CounterAddress(-17, 23, 5).to_bytes()) == 32
    assert counter_words(-17, 23, 5)[:3] == (33, 46, 5)
    with pytest.raises(ValueError):
        encode_signed_zigzag(1 << 63)
    with pytest.raises(ValueError):
        CounterAddress(0, 0, -1).words()


def test_key_fields_are_length_delimited_and_stateless_access_is_order_invariant() -> None:
    baseline = KeyIdentity(1, 2, "ab", 3, "c")
    variants = (
        KeyIdentity(2, 2, "ab", 3, "c"),
        KeyIdentity(1, 3, "ab", 3, "c"),
        KeyIdentity(1, 2, "a", 3, "bc"),
        KeyIdentity(1, 2, "ab", 4, "c"),
        KeyIdentity(1, 2, "ab", 3, "d"),
    )
    assert len({baseline.key_bytes(), *(item.key_bytes() for item in variants)}) == 6

    latent = make_latent_noise_identity(99887766, 12)
    rng = Philox4x64.from_latent_identity(latent, 9, "coefficient-test")
    coordinates = ((-8, 3), (0, 0), (55, -91), (2, 7), (-8, 3))
    forward = [rng.word(x, y, lane=index % 4) for index, (x, y) in enumerate(coordinates)]
    reverse_indices = tuple(reversed(range(len(coordinates))))
    reverse = {index: rng.word(*coordinates[index], lane=index % 4) for index in reverse_indices}
    assert forward == [reverse[index] for index in range(len(coordinates))]
    assert forward[0] == forward[-1]  # Repeated global address has no stream state.
    assert rng.word(-8, 3, lane=0) != rng.word(-8, 3, lane=1)
    uniforms = [uint64_to_open_uniform(word) for word in (0, (1 << 64) - 1, *forward)]
    assert all(0.0 < value < 1.0 and math.isfinite(value) for value in uniforms)
