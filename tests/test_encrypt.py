import unittest
from shared.encrypt import encrypt_message, decrypt_message

class TestEncryptionModule(unittest.TestCase):

    def test_encrypt_decrypt_cycle(self):
        """Test that a message can be encrypted and decrypted correctly."""
        original = "Hello, World! 🌍🚀"
        encrypted = encrypt_message(original)
        decrypted = decrypt_message(encrypted)
        self.assertEqual(decrypted, original)

    def test_encrypt_returns_bytes(self):
        """Test that encrypt_message returns a bytes object."""
        message = "sample message"
        encrypted = encrypt_message(message)
        self.assertIsInstance(encrypted, bytes)

    def test_decrypt_returns_str(self):
        """Test that decrypt_message returns a string."""
        message = "another message"
        encrypted = encrypt_message(message)
        decrypted = decrypt_message(encrypted)
        self.assertIsInstance(decrypted, str)

    def test_encrypt_non_string_raises(self):
        """Encrypting a non-string should raise TypeError."""
        with self.assertRaises(TypeError):
            encrypt_message(12345)  # not a string

    def test_decrypt_non_bytes_raises(self):
        """Decrypting a non-bytes object should raise TypeError."""
        with self.assertRaises(TypeError):
            decrypt_message("not bytes")  # should be bytes

    def test_unicode_handling(self):
        """Ensure messages with Unicode characters are preserved."""
        message = "Xin chào 🌸 – こんにちは – Здравствуйте – مرحبا"
        encrypted = encrypt_message(message)
        decrypted = decrypt_message(encrypted)
        self.assertEqual(decrypted, message)

    def test_decryption_fails_with_wrong_input(self):
        """Ensure decrypting invalid data raises an exception."""
        with self.assertRaises(Exception):
            decrypt_message(b"invalid_token_data")

if __name__ == '__main__':
    print("Test running: encryption/decryption")
    unittest.main()
