import mmh3


class Hasher:
    @staticmethod
    def hash(
        input_string: str,
    ) -> str:
        """
        Generate a hash from the input string which can be used as a file or directory name.

        It uses the non-cryptographic and deterministic MurmurHash3 algorithm to generate the hash. Specifically, it
        uses the 128-bit version of the algorithm, not using signed integers.

        As the generated hash is an integer, it is converted to a hexadecimal string before returning, removing the `0x`
        prefix, converting letters to lowercase, and padding with zeros to ensure the length is 32 characters long.
        32 characters because ``128/4=32``, as one hexadecimal character represents 4 bits.

        :param input_string: the string to hash

        :return: the hash as a hexadecimal string
        """
        return f"{mmh3.hash128(input_string, signed=False):032x}"
