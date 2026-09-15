"""ML-KEM benchmark orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .timer import TimingRecord, time_operation

LOGGER = logging.getLogger(__name__)


class MLKEMWrapper:
    """Small adapter around liboqs-python's KEM API."""

    def __init__(self, algorithm: str = "ML-KEM-768") -> None:
        try:
            import oqs
        except ImportError as error:
            raise RuntimeError(
                "liboqs-python is required. Install dependencies from requirements.txt."
            ) from error
        self._oqs = oqs
        self.algorithm = algorithm
        self._kem = oqs.KeyEncapsulation(algorithm)

    def keygen(self) -> bytes:
        """Generate a keypair and return the secret key."""
        self._kem.generate_keypair()
        return self._kem.export_secret_key()

    def encapsulate(self) -> tuple[bytes, bytes]:
        """Create a ciphertext and shared secret using the current public key."""
        return self._kem.encap_secret()

    def decapsulate(self, ciphertext: bytes) -> bytes:
        """Recover a shared secret from ``ciphertext``."""
        return self._kem.decap_secret(ciphertext)

    def close(self) -> None:
        """Release native liboqs resources when supported by the binding."""
        close = getattr(self._kem, "free", None)
        if callable(close):
            close()


@dataclass
class BenchmarkRunner:
    """Collect operation-level ML-KEM timings for one experimental condition."""

    algorithm: str = "ML-KEM-768"
    sample_count: int = 10_000

    def run(self, label: str) -> list[TimingRecord]:
        """Run key generation, encapsulation, and decapsulation timings."""
        if self.sample_count < 1:
            raise ValueError("sample_count must be positive")
        kem = MLKEMWrapper(self.algorithm)
        records: list[TimingRecord] = []
        try:
            for sample_index in range(self.sample_count):
                secret_key, keygen_record = time_operation(
                    "key_generation", label, kem.keygen
                )
                records.append(keygen_record)
                ciphertext, encaps_record = time_operation(
                    "encapsulation", label, kem.encapsulate
                )
                records.append(encaps_record)
                _, decaps_record = time_operation(
                    "decapsulation", label, kem.decapsulate, ciphertext
                )
                records.append(decaps_record)
                del secret_key
                if (sample_index + 1) % 1000 == 0:
                    LOGGER.info("Collected %d/%d samples for %s", sample_index + 1, self.sample_count, label)
        finally:
            kem.close()
        return records

    def run_function(self, operation: str, label: str, function: Any) -> list[TimingRecord]:
        """Time an arbitrary callable repeatedly for controlled experiments."""
        records = []
        for _ in range(self.sample_count):
            _, record = time_operation(operation, label, function)
            records.append(record)
        return records
