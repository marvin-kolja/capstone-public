from core.hasher import Hasher


class TestHasher:
    def test_hash_returns_hash_of_input_string(self):
        """
        GIVEN an input string

        WHEN the hash method is called with the input string

        THEN the return value is the hash of the input in hexadecimal format
        """
        input_string = "input"

        result = Hasher.hash(input_string)

        assert result == "b0492e8d4528a9abdc70c7800b9b91c3"

    def test_hash_returns_hash_of_input_string_with_special_characters(self):
        """
        GIVEN an input string with special characters

        WHEN the hash method is called with the input string

        THEN the return value is the hash of the input in hexadecimal format
        """
        input_string = "input!@#$%^&*()_+"

        result = Hasher.hash(input_string)

        assert result == "0d1c8a82b714210a7b96bb23f4973e8d"
