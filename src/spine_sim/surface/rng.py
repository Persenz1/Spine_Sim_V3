"""Frozen counter-based random stream used by M01 synthetic surfaces.

The implementation is intentionally self contained.  In particular it does not
delegate Philox to NumPy: doing so would make the replay contract depend on a
library state object and on the order in which values are requested.

Profile ``M01_PHILOX4X64_10_KEYED_1`` freezes the following details:

* Philox-4x64 with ten rounds and the Random123 constants below;
* a tagged, length-delimited, little-endian SHA-256 key preimage;
* two signed 64-bit lattice coordinates encoded with zigzag;
* an unsigned 64-bit block ordinal and a fixed counter-domain word; and
* open-interval uniforms followed by ordered Box--Muller pairs ``(0, 1)`` and
  ``(2, 3)``.

No object in this module has mutable stream state.  A word is a pure function of
its identity tuple, lattice coordinate, block ordinal, and lane.
"""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass

from .contracts import NORMAL_TRANSFORM_ID, RNG_PROFILE_ID, LatentNoiseIdentity

__all__ = [
    "BOX_MULLER_VERSION",
    "CounterAddress",
    "KeyIdentity",
    "Philox4x64",
    "Philox4x64RNG",
    "box_muller_pair",
    "counter_bytes",
    "counter_words",
    "derive_key",
    "derive_philox_key",
    "encode_signed_zigzag",
    "normal",
    "normal_pair",
    "philox4x64_10",
    "uint64_to_open_uniform",
    "uniform",
    "word",
]

_UINT64_MASK = (1 << 64) - 1
_UINT64_LIMIT = 1 << 64
_INT64_MIN = -(1 << 63)
_INT64_MAX = (1 << 63) - 1

# Constants from the published Random123 Philox-4x64 construction.
_PHILOX_M0 = 0xD2E7470EE14C6C93
_PHILOX_M1 = 0xCA5A826395121157
_PHILOX_W0 = 0x9E3779B97F4A7C15
_PHILOX_W1 = 0xBB67AE8584CAA73B

# ``M01CNTR1`` interpreted as a little-endian integer.  Keeping a non-zero
# domain word prevents a future three-coordinate profile from aliasing this one.
_COUNTER_DOMAIN_WORD = int.from_bytes(b"M01CNTR1", "little")
_KEY_MAGIC = b"M01_PHILOX4X64_10_KEYED_1\x00"
_KEY_ENCODING_VERSION = 1
BOX_MULLER_VERSION = NORMAL_TRANSFORM_ID


def _checked_u64(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if not 0 <= value < _UINT64_LIMIT:
        raise ValueError(f"{field_name} must fit an unsigned 64-bit field")
    return value


def _checked_i64(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if not _INT64_MIN <= value <= _INT64_MAX:
        raise ValueError(f"{field_name} must fit a signed 64-bit field")
    return value


def encode_signed_zigzag(value: int) -> int:
    """Encode one signed 64-bit integer as the frozen unsigned zigzag word."""

    checked = _checked_i64(value, "signed coordinate")
    return ((checked << 1) ^ (checked >> 63)) & _UINT64_MASK


@dataclass(frozen=True, slots=True)
class CounterAddress:
    """Canonical global address of one four-word Philox block."""

    coordinate_x: int
    coordinate_y: int
    block_ordinal: int = 0

    def words(self) -> tuple[int, int, int, int]:
        return counter_words(self.coordinate_x, self.coordinate_y, self.block_ordinal)

    def to_bytes(self) -> bytes:
        return counter_bytes(self.coordinate_x, self.coordinate_y, self.block_ordinal)


def counter_words(
    coordinate_x: int,
    coordinate_y: int,
    block_ordinal: int = 0,
) -> tuple[int, int, int, int]:
    """Return the collision-free four-word counter for a global lattice address."""

    return (
        encode_signed_zigzag(coordinate_x),
        encode_signed_zigzag(coordinate_y),
        _checked_u64(block_ordinal, "block_ordinal"),
        _COUNTER_DOMAIN_WORD,
    )


def counter_bytes(coordinate_x: int, coordinate_y: int, block_ordinal: int = 0) -> bytes:
    """Serialize a counter as exactly 32 little-endian bytes."""

    return struct.pack("<4Q", *counter_words(coordinate_x, coordinate_y, block_ordinal))


def _tagged(tag: int, payload: bytes) -> bytes:
    if not 0 < tag < 256:
        raise ValueError("key field tag must fit one non-zero byte")
    if len(payload) >= 1 << 16:
        raise ValueError("key field payload exceeds the frozen uint16 length")
    return bytes((tag,)) + struct.pack("<H", len(payload)) + payload


def _utf8(value: str, field_name: str) -> bytes:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    encoded = value.encode("utf-8", errors="strict")
    if not encoded:
        raise ValueError(f"{field_name} cannot be empty")
    return encoded


@dataclass(frozen=True, slots=True)
class KeyIdentity:
    """Identity fields that derive a Philox 128-bit key.

    Numeric payloads have fixed widths (u128, u64, u64); strings are strict
    UTF-8 and carry an explicit uint16 little-endian byte length.  Every field
    also has a one-byte tag, so concatenations cannot be ambiguous.
    """

    root_seed: int
    surface_seed_index: int
    latent_noise_namespace: str
    frequency_band: int
    component_or_pair_role: str
    stream_namespace: str = "m01.surface"

    def __post_init__(self) -> None:
        if isinstance(self.root_seed, bool) or not isinstance(self.root_seed, int):
            raise TypeError("root_seed must be an integer")
        if not 0 <= self.root_seed < 1 << 128:
            raise ValueError("root_seed must fit an unsigned 128-bit field")
        _checked_u64(self.surface_seed_index, "surface_seed_index")
        _checked_u64(self.frequency_band, "frequency_band")
        if self.stream_namespace != "m01.surface":
            raise ValueError("M01 stream_namespace must be 'm01.surface'")
        _utf8(self.stream_namespace, "stream_namespace")
        _utf8(self.latent_noise_namespace, "latent_noise_namespace")
        _utf8(self.component_or_pair_role, "component_or_pair_role")

    @classmethod
    def from_latent_identity(
        cls,
        latent_identity: LatentNoiseIdentity,
        frequency_band: int,
        component_or_pair_role: str,
    ) -> KeyIdentity:
        return cls(
            root_seed=latent_identity.root_seed,
            surface_seed_index=latent_identity.surface_seed_index,
            latent_noise_namespace=latent_identity.latent_noise_namespace,
            frequency_band=frequency_band,
            component_or_pair_role=component_or_pair_role,
            stream_namespace=latent_identity.stream_namespace,
        )

    def preimage(self) -> bytes:
        """Return the exact frozen SHA-256 preimage (golden-test API)."""

        return b"".join(
            (
                _KEY_MAGIC,
                bytes((_KEY_ENCODING_VERSION,)),
                _tagged(1, self.root_seed.to_bytes(16, "little", signed=False)),
                _tagged(2, _utf8(self.stream_namespace, "stream_namespace")),
                _tagged(
                    3,
                    self.surface_seed_index.to_bytes(8, "little", signed=False),
                ),
                _tagged(
                    4,
                    _utf8(self.latent_noise_namespace, "latent_noise_namespace"),
                ),
                _tagged(5, self.frequency_band.to_bytes(8, "little", signed=False)),
                _tagged(
                    6,
                    _utf8(self.component_or_pair_role, "component_or_pair_role"),
                ),
            )
        )

    def key_bytes(self) -> bytes:
        """Return the first 128 digest bits in canonical byte order."""

        return hashlib.sha256(self.preimage()).digest()[:16]

    def key_words(self) -> tuple[int, int]:
        """Return two little-endian uint64 Philox key words."""

        return struct.unpack("<2Q", self.key_bytes())


def derive_philox_key(
    root_seed: int,
    surface_seed_index: int,
    latent_noise_namespace: str,
    frequency_band: int,
    component_or_pair_role: str,
    *,
    stream_namespace: str = "m01.surface",
) -> tuple[int, int]:
    """Derive the profile's 128-bit Philox key from its complete identity tuple."""

    return KeyIdentity(
        root_seed,
        surface_seed_index,
        latent_noise_namespace,
        frequency_band,
        component_or_pair_role,
        stream_namespace,
    ).key_words()


# Short, discoverable alias for callers that already know the RNG profile.
derive_key = derive_philox_key


def _mulhilo64(multiplier: int, value: int) -> tuple[int, int]:
    product = multiplier * value
    return (product >> 64) & _UINT64_MASK, product & _UINT64_MASK


def philox4x64_10(
    counter: tuple[int, int, int, int],
    key: tuple[int, int],
) -> tuple[int, int, int, int]:
    """Apply the frozen ten-round Philox-4x64 permutation.

    This low-level function accepts only unsigned 64-bit words and is useful for
    independent golden-vector testing.
    """

    if len(counter) != 4 or len(key) != 2:
        raise ValueError("Philox-4x64 requires four counter and two key words")
    c0, c1, c2, c3 = (
        _checked_u64(value, f"counter[{index}]") for index, value in enumerate(counter)
    )
    k0, k1 = (_checked_u64(value, f"key[{index}]") for index, value in enumerate(key))

    for round_index in range(10):
        hi0, lo0 = _mulhilo64(_PHILOX_M0, c0)
        hi1, lo1 = _mulhilo64(_PHILOX_M1, c2)
        c0, c1, c2, c3 = (
            (hi1 ^ c1 ^ k0) & _UINT64_MASK,
            lo1,
            (hi0 ^ c3 ^ k1) & _UINT64_MASK,
            lo0,
        )
        if round_index != 9:
            k0 = (k0 + _PHILOX_W0) & _UINT64_MASK
            k1 = (k1 + _PHILOX_W1) & _UINT64_MASK
    return c0, c1, c2, c3


def uint64_to_open_uniform(value: int) -> float:
    """Map a uint64 word to a binary64 value strictly inside ``(0, 1)``.

    The top 53 bits select one of ``2**53`` equal cells and the returned value
    is the cell midpoint.  Consequently both logarithm and Box--Muller are
    finite, and low bits that binary64 cannot represent do not affect replay.
    """

    checked = _checked_u64(value, "uniform word")
    mapped = ((checked >> 11) + 0.5) * (1.0 / (1 << 53))
    # The mathematical midpoint of the last binary53 cell is closer to 1.0
    # than to the preceding binary64 value, so the multiplication above can
    # round upward.  Freeze the endpoint handling without perturbing any other
    # word in the profile.
    return min(mapped, math.nextafter(1.0, 0.0))


def box_muller_pair(first_uniform: float, second_uniform: float) -> tuple[float, float]:
    """Frozen ordered Box--Muller map ``u0,u1 -> radius*cos, radius*sin``."""

    if not 0.0 < first_uniform < 1.0 or not 0.0 < second_uniform < 1.0:
        raise ValueError("Box--Muller inputs must lie strictly inside (0, 1)")
    radius = math.sqrt(-2.0 * math.log(first_uniform))
    angle = math.tau * second_uniform
    return radius * math.cos(angle), radius * math.sin(angle)


@dataclass(frozen=True, slots=True)
class Philox4x64:
    """A stateless keyed view of one M01 frequency-band/role stream."""

    key_identity: KeyIdentity

    @classmethod
    def from_latent_identity(
        cls,
        latent_identity: LatentNoiseIdentity,
        frequency_band: int,
        component_or_pair_role: str,
    ) -> Philox4x64:
        if latent_identity.rng_profile_id != RNG_PROFILE_ID:
            raise ValueError(f"unsupported RNG profile: {latent_identity.rng_profile_id}")
        if latent_identity.normal_transform_id != NORMAL_TRANSFORM_ID:
            raise ValueError(f"unsupported normal transform: {latent_identity.normal_transform_id}")
        return cls(
            KeyIdentity.from_latent_identity(
                latent_identity,
                frequency_band,
                component_or_pair_role,
            )
        )

    @property
    def key(self) -> tuple[int, int]:
        return self.key_identity.key_words()

    def block(
        self,
        coordinate_x: int,
        coordinate_y: int,
        block_ordinal: int = 0,
    ) -> tuple[int, int, int, int]:
        return philox4x64_10(
            counter_words(coordinate_x, coordinate_y, block_ordinal),
            self.key,
        )

    def word(
        self,
        coordinate_x: int,
        coordinate_y: int,
        block_ordinal: int = 0,
        lane: int = 0,
    ) -> int:
        if isinstance(lane, bool) or not isinstance(lane, int) or not 0 <= lane < 4:
            raise ValueError("lane must be one of 0, 1, 2, 3")
        return self.block(coordinate_x, coordinate_y, block_ordinal)[lane]

    def uniform(
        self,
        coordinate_x: int,
        coordinate_y: int,
        block_ordinal: int = 0,
        lane: int = 0,
    ) -> float:
        return uint64_to_open_uniform(self.word(coordinate_x, coordinate_y, block_ordinal, lane))

    def normal_pair(
        self,
        coordinate_x: int,
        coordinate_y: int,
        block_ordinal: int = 0,
        pair_index: int = 0,
    ) -> tuple[float, float]:
        if pair_index not in (0, 1):
            raise ValueError("pair_index must be 0 for lanes (0,1) or 1 for lanes (2,3)")
        block = self.block(coordinate_x, coordinate_y, block_ordinal)
        lane = pair_index * 2
        return box_muller_pair(
            uint64_to_open_uniform(block[lane]),
            uint64_to_open_uniform(block[lane + 1]),
        )

    def normal(
        self,
        coordinate_x: int,
        coordinate_y: int,
        block_ordinal: int = 0,
        lane: int = 0,
    ) -> float:
        if isinstance(lane, bool) or not isinstance(lane, int) or not 0 <= lane < 4:
            raise ValueError("normal lane must be one of 0, 1, 2, 3")
        pair = self.normal_pair(
            coordinate_x,
            coordinate_y,
            block_ordinal,
            lane // 2,
        )
        return pair[lane % 2]


# Compatibility name that makes the profile's role explicit at import sites.
Philox4x64RNG = Philox4x64


def _rng_from_identity(
    latent_identity: LatentNoiseIdentity,
    frequency_band: int,
    component_or_pair_role: str,
) -> Philox4x64:
    return Philox4x64.from_latent_identity(
        latent_identity,
        frequency_band,
        component_or_pair_role,
    )


def word(
    latent_identity: LatentNoiseIdentity,
    frequency_band: int,
    component_or_pair_role: str,
    coordinate_x: int,
    coordinate_y: int,
    *,
    block_ordinal: int = 0,
    lane: int = 0,
) -> int:
    """Functional golden-test API for one deterministic uint64 word."""

    return _rng_from_identity(latent_identity, frequency_band, component_or_pair_role).word(
        coordinate_x,
        coordinate_y,
        block_ordinal,
        lane,
    )


def uniform(
    latent_identity: LatentNoiseIdentity,
    frequency_band: int,
    component_or_pair_role: str,
    coordinate_x: int,
    coordinate_y: int,
    *,
    block_ordinal: int = 0,
    lane: int = 0,
) -> float:
    """Functional golden-test API for one deterministic open uniform."""

    return _rng_from_identity(
        latent_identity,
        frequency_band,
        component_or_pair_role,
    ).uniform(coordinate_x, coordinate_y, block_ordinal, lane)


def normal_pair(
    latent_identity: LatentNoiseIdentity,
    frequency_band: int,
    component_or_pair_role: str,
    coordinate_x: int,
    coordinate_y: int,
    *,
    block_ordinal: int = 0,
    pair_index: int = 0,
) -> tuple[float, float]:
    """Functional golden-test API for an ordered deterministic normal pair."""

    return _rng_from_identity(
        latent_identity,
        frequency_band,
        component_or_pair_role,
    ).normal_pair(coordinate_x, coordinate_y, block_ordinal, pair_index)


def normal(
    latent_identity: LatentNoiseIdentity,
    frequency_band: int,
    component_or_pair_role: str,
    coordinate_x: int,
    coordinate_y: int,
    *,
    block_ordinal: int = 0,
    lane: int = 0,
) -> float:
    """Functional golden-test API for one ordered deterministic normal."""

    return _rng_from_identity(latent_identity, frequency_band, component_or_pair_role).normal(
        coordinate_x,
        coordinate_y,
        block_ordinal,
        lane,
    )
