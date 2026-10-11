import pytest
from cryptography.fernet import Fernet, InvalidToken

def test_fernet_key_generation():
    key = Fernet.generate_key()
    assert isinstance(key, bytes)
    assert len(key) == 44
    assert key.endswith(b"=")


def test_encryption_and_decryption_success():
    key = Fernet.generate_key()
    fernet = Fernet(key)

    original_numbers = [
        "+2348012345678",
        "08012345678",
        "+14155552671",
        "+447911123456",
    ]

    for num in original_numbers:
        encrypted = fernet.encrypt(num.encode()).decode()
        # Ciphertext must differ from original and start with standard Fernet token prefix
        assert encrypted != num
        assert encrypted.startswith("gAAAA")

        decrypted = fernet.decrypt(encrypted.encode()).decode()
        assert decrypted == num


def test_decryption_with_wrong_key_fails():
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()

    fernet1 = Fernet(key1)
    fernet2 = Fernet(key2)

    phone = "+2348012345678"
    encrypted = fernet1.encrypt(phone.encode())

    with pytest.raises(InvalidToken):
        fernet2.decrypt(encrypted)


def test_decryption_tampered_token_fails():
    key = Fernet.generate_key()
    fernet = Fernet(key)

    encrypted = fernet.encrypt(b"+2348012345678")
    # Tamper with the ciphertext
    tampered = encrypted[:-4] + b"XXXX"

    with pytest.raises(Exception):
        fernet.decrypt(tampered)
