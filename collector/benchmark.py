"""ML-KEM benchmark orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .timer import TimingRecord, time_operation

LOGGER = logging.getLogger(__name__)


class MLKEMWrapper:
    """Hardware-independent adapter around liboqs-python's ML-KEM API."""

    def __init__(self, algorithm: str = "ML-KEM-768") -> None:
        if not algorithm:
            raise ValueError("algorithm must be a non-empty string")
        try:
            import oqs
        except ImportError as error:
            raise RuntimeError(
                "liboqs-python is required. Install dependencies from requirements.txt."
            ) from error
        self._oqs = oqs
        self.algorithm = algorithm
        try:
            self._kem = oqs.KeyEncapsulation(algorithm)
        except Exception as error:
            raise RuntimeError(
                f"Unable to initialize liboqs algorithm {algorithm!r}"
            ) from error

    def keygen(self) -> tuple[bytes, bytes]:
        """Generate and return an ML-KEM public and secret key pair."""
        try:
            public_key = self._kem.generate_keypair()
            secret_key = self._kem.export_secret_key()
        except Exception as error:
            LOGGER.exception("ML-KEM key generation failed for %s", self.algorithm)
            raise RuntimeError("ML-KEM key generation failed") from error
        if not isinstance(public_key, bytes) or not isinstance(secret_key, bytes):
            raise TypeError("liboqs returned non-byte key material")
        LOGGER.debug("Generated an ML-KEM key pair using %s", self.algorithm)
        return public_key, secret_key

    def encapsulate(self, public_key: bytes) -> tuple[bytes, bytes]:
        """Encapsulate to ``public_key`` and return ciphertext and shared secret."""
        if not isinstance(public_key, bytes):
            raise TypeError("public_key must be bytes")
        try:
            ciphertext, shared_secret = self._kem.encap_secret(public_key)
        except Exception as error:
            LOGGER.exception("ML-KEM encapsulation failed for %s", self.algorithm)
            raise RuntimeError("ML-KEM encapsulation failed") from error
        if not isinstance(ciphertext, bytes) or not isinstance(shared_secret, bytes):
            raise TypeError("liboqs returned non-byte encapsulation material")
        return ciphertext, shared_secret

    def decapsulate(self, ciphertext: bytes) -> bytes:
        """Decapsulate ``ciphertext`` and return the recovered shared secret."""
        if not isinstance(ciphertext, bytes):
            raise TypeError("ciphertext must be bytes")
        try:
            shared_secret = self._kem.decap_secret(ciphertext)
        except Exception as error:
            LOGGER.exception("ML-KEM decapsulation failed for %s", self.algorithm)
            raise RuntimeError("ML-KEM decapsulation failed") from error
        if not isinstance(shared_secret, bytes):
            raise TypeError("liboqs returned a non-byte shared secret")
        return shared_secret

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
                (public_key, secret_key), keygen_record = time_operation(
                    "key_generation", label, kem.keygen
                )
                records.append(keygen_record)
                (ciphertext, _), encaps_record = time_operation(
                    "encapsulation", label, kem.encapsulate, public_key
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    wrapper = MLKEMWrapper()
    try:
        public_key, _ = wrapper.keygen()
        ciphertext, encapsulated_secret = wrapper.encapsulate(public_key)
        decapsulated_secret = wrapper.decapsulate(ciphertext)
        if encapsulated_secret != decapsulated_secret:
            raise RuntimeError("ML-KEM self-test failed: shared secrets do not match")
        print(f"ML-KEM self-test succeeded using {wrapper.algorithm}")
    finally:
        wrapper.close()
