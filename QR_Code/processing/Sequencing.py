from __future__ import annotations
from typing import Sized
from QR_Code.utils.Classes import Regex, EncodingMode, ECCode
from QR_Code.utils.Constants import CHARACTER_CAPACITIES_BY_VERSION, EC_CODE_IDX, CODEWORDS_AND_BLOCK_INFO, CHARACTER_CAPACITIES_BY_EC
from QR_Code.utils.Exceptions import DataLimitExceededError, ModeNotImplementedError

import re
from bitarray import bitarray


def get_smallest_version_and_ec(message_len: int, enc_mode: EncodingMode) -> tuple[int, ECCode]:
    capacities_by_version: dict[int, list[int]] = CHARACTER_CAPACITIES_BY_VERSION[enc_mode]
    version: int = 1
    while version <= 40:
        for e, code_words in enumerate(capacities_by_version[version][::-1]):
            if code_words >= message_len:
                return version, EC_CODE_IDX[3 - e]
        version += 1
    raise DataLimitExceededError(f"the length of your message is {message_len}, which is too long for {enc_mode} encoding")


def get_smallest_version_from_ec(message_len: int, enc_mode: EncodingMode, ec_level: ECCode) -> tuple[int, ECCode]:
    capacities_by_ec: list[int] = CHARACTER_CAPACITIES_BY_EC[enc_mode][ec_level]
    version: int = 1
    while version <= 40:
        if capacities_by_ec[version - 1] >= message_len:
            return version, ec_level
        version += 1
    raise DataLimitExceededError(f"the length of your message is {message_len}, which is too long for {enc_mode} encoding")


def get_encoding_mode(message: str) -> EncodingMode:
    if re.fullmatch(Regex.NUMERIC, message):
        return EncodingMode.NUMERIC
    if re.fullmatch(Regex.ALPHA_NUMERIC, message):
        return EncodingMode.ALPHA_NUMERIC
    if re.fullmatch(Regex.BYTE, message):
        return EncodingMode.BYTE
    if re.fullmatch(Regex.KANJI, message):
        return EncodingMode.KANJI
    return EncodingMode.ECI


LENGTH_BITS = {
    EncodingMode.NUMERIC: [10, 12, 14],
    EncodingMode.ALPHA_NUMERIC: [9, 11, 13],
    EncodingMode.BYTE: [8, 16, 16],
    EncodingMode.KANJI: [8, 10, 12]
}


def get_length_bits(enc_mode: EncodingMode, version: int) -> int:
    idx: int = 2 if version > 26 else 1 if version > 9 else 0
    return LENGTH_BITS[enc_mode][idx]


def int_to_bit(i: int, length_bits: int = 8) -> str:
    return bin(i)[2:].rjust(length_bits, '0')


def get_data_codewords(version: int, ec_code: ECCode):
    return CODEWORDS_AND_BLOCK_INFO[f'{version}{ec_code.name}'][0]


def get_total_codewords(version: int, ec_code: ECCode):
    data: tuple = CODEWORDS_AND_BLOCK_INFO[f'{version}{ec_code.name}']
    return data[0] + (data[2] + data[4]) * data[1]


def split_into_chunks(l: Sized, chunk_size: int) -> list:
    return [l[i: i + chunk_size] for i in range(0, len(l), chunk_size)]


ALPHANUMERIC_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'


# ALPHANUMERIC_CHARS = '0123456789abcdefghijklmnopqrstuvwxyz $%*+-./:'


class Encoder:
    def __init__(self, version: int, ec_code: ECCode):
        self._message = ''
        self._enc_mode = EncodingMode.NUMERIC
        self.version = version
        self.ec_code = ec_code

    def _encode_numeric_message(self) -> bitarray:
        bits = bitarray('0001')
        bits.extend(int_to_bit(len(self._message), get_length_bits(EncodingMode.NUMERIC, self.version)))

        for chunk in split_into_chunks(self._message, 3):
            _int = int(chunk)
            match len(chunk):
                case 3:
                    bits.extend(int_to_bit(_int, 10))
                case 2:
                    bits.extend(int_to_bit(_int, 7))
                case 1:
                    bits.extend(int_to_bit(_int, 4))

            bits.extend('0000')
            bits.extend('0' * (8 - len(bits) % 8))

        for i in range(get_data_codewords(self.version, self.ec_code) - len(bits) // 8):
            bits.extend('11101100') if i % 2 == 0 else bits.extend('00010001')

        return bits

    def _encode_alphanumeric_message(self) -> bitarray:
        bits = bitarray('0010')
        bits.extend(int_to_bit(len(self._message), get_length_bits(EncodingMode.ALPHA_NUMERIC, self.version)))

        for chunk in split_into_chunks(self._message, 2):
            print(chunk)
            if len(chunk) == 2:
                bits.extend(int_to_bit(45 * ALPHANUMERIC_CHARS.index(chunk[0]) + ALPHANUMERIC_CHARS.index(chunk[1]), 11))
            else:
                bits.extend(int_to_bit(ALPHANUMERIC_CHARS.index(chunk), 6))
        bits.extend('0000')
        bits.extend('0' * (8 - len(bits) % 8))

        for i in range(get_data_codewords(self.version, self.ec_code) - len(bits) // 8):
            bits.extend('11101100') if i % 2 == 0 else bits.extend('00010001')

        return bits

    def _encode_byte_message(self) -> bitarray:
        bits = bitarray('0100')
        bits.extend(int_to_bit(len(self._message), get_length_bits(EncodingMode.BYTE, self.version)))

        for char in self._message:
            bits.extend(int_to_bit(ord(char), 8))

        bits.extend('0000')

        for i in range(get_data_codewords(self.version, self.ec_code) - len(bits) // 8):
            bits.extend('11101100') if i % 2 == 0 else bits.extend('00010001')

        return bits

    def encode(self, message: str):
        self._message = message
        self._enc_mode = get_encoding_mode(message)
        print(self._enc_mode)

        bits = bitarray('0')

        match self._enc_mode:
            case EncodingMode.NUMERIC:
                bits = self._encode_numeric_message()
            case EncodingMode.ALPHA_NUMERIC:
                bits = self._encode_alphanumeric_message()
            case EncodingMode.BYTE:
                bits = self._encode_byte_message()
            case EncodingMode.KANJI:
                raise ModeNotImplementedError("Kanji mode is not yet implemented")
            case _:
                raise ModeNotImplementedError(f"Unrecognized Encoding Mode: {self._enc_mode}")

        return list(map(int, bits.tobytes()))


def print_bit_array(bits: bitarray, num_bytes: int = 5):
    if num_bytes <= 0:
        num_bytes = -1
    i, j = 0, 0
    for bit in bits:
        i += 1
        if i < 8:
            print(bit, end='')
        else:
            print(bit, end=' ')
            i = 0
            j += 1
        if j == num_bytes:
            print()
            j = 0
    print()


if __name__ == '__main__':
    e = Encoder(2, ECCode.M)
    b = e.encode('https://www.qrcode.com/')
    b = e.encode('12')
    print(b)

    print(get_encoding_mode('12'))
