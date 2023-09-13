from QR_Code.error_correction.Polynomial import GF256Polynomial, G256_EXP
from QR_Code.processing.Sequencing import (Encoder,
                                           get_total_codewords,
                                           get_smallest_version_and_ec,
                                           get_encoding_mode)


def get_generator_polynomial(degree: int) -> GF256Polynomial:
    poly = GF256Polynomial([1])
    for d in range(degree):
        poly = poly * GF256Polynomial([1, G256_EXP[d % 256]])
    return poly


def get_error_correction_words(data: GF256Polynomial, codewords: int):
    deg: int = codewords - len(data)
    return (GF256Polynomial(data.coefficients, deg) % get_generator_polynomial(deg)).coefficients


if __name__ == '__main__':
    msg = 'https://www.qrcode.com/'
    enc_mode = get_encoding_mode(msg)
    version, ec_code = get_smallest_version_and_ec(len(msg), enc_mode)
    e = Encoder(version, ec_code)
    byte_data = e.encode(msg)
    print(get_error_correction_words(GF256Polynomial(byte_data), get_total_codewords(version, ec_code)))
