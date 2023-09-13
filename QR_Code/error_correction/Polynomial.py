from __future__ import annotations
from typing import Iterator, Any
from QR_Code.utils.Exceptions import OutOfFieldError

G256_EXP = [1] * 256
G256_LOG = [0] * 256

val: int = 1
for exp in range(1, 256):
    val = ((val << 1) ^ 285) if val > 127 else val << 1  # not exactly sure why 285 but it makes it so that the field is cyclic with
    # all the elements
    G256_LOG[val] = exp % 255
    G256_EXP[exp % 255] = val


def g256_mul(a: int, b: int) -> int:
    return G256_EXP[(G256_LOG[a] + G256_LOG[b]) % 255] if a > 0 and b > 0 else 0


def g256_div(a: int, b: int) -> int:
    return G256_EXP[(G256_LOG[a] + G256_LOG[b] * 254) % 255]


def pad_list_left(list_1: list, list_2: list, padding: Any = 0) -> tuple[list, list]:
    """adds padding to the smaller list on the left side(right justifies the smaller list) and returns both lists in the order
    they were passed"""
    diff: int = abs(len(list_1) - len(list_2))
    if diff == 0:
        return list_1, list_2
    elif len(list_1) > len(list_2):
        return list_1, [padding] * diff + list_2
    else:
        return [padding] * diff + list_1, list_2


def pad_list_right(list_1: list, list_2: list, padding: Any = 0) -> tuple[list, list]:
    """adds padding to the smaller list on the right side(left justifies the smaller list) and returns both lists in the order
    they were passed"""
    diff: int = abs(len(list_1) - len(list_2))
    if diff == 0:
        return list_1, list_2
    elif len(list_1) > len(list_2):
        return list_1, list_2 + [padding] * diff
    else:
        return list_1 + [padding] * diff, list_2


class GF256Polynomial:
    """
    A class representing a polynomial whose coefficients and arithmetic are of the Galois Field(cyclic field i.e. a^n
    = a for every 'a' in the field)

    let p be the primitive i.e a = p^k, a belongs to the field
    addition is XOR
    subtraction turns out to be equivalent to addition

    multiplication is a.b = p^(k1+k2) = p^(k1+k2)%n
    division; a^n = a => a^n-2 = a^-1 so a/b = p^(k1 + k2*(n-2))%n

    since all the elements can now be expressed in powers of p it is more efficient to keep exp and log tables of p
    in the galois field

    in this implementation since it is 256 so euler's_totient_func(256) = 192, so we choose p = 2
    """

    def __init__(self, coefficients: list[int], offset: int = 0) -> None:
        self.__coefficients = coefficients + [0] * offset
        self._remove_trailing_zeros()

    def __iter__(self) -> Iterator[int]:
        return iter(self.__coefficients)

    def __eq__(self, other):
        return self.coefficients == other.coefficients

    def __str__(self) -> str:
        if self.__coefficients == [0]:
            return '0'

        ans: str = ''
        for coefficient, exponent in zip(self.__coefficients, range(self.degree, -1, -1)):
            if coefficient != 0:
                if exponent != self.degree:
                    ans += ' - ' if coefficient < 0 else ' + '
                if exponent > 1:
                    ans += f'{abs(coefficient)}x^{exponent}' if abs(coefficient) != 1 else f'x^{exponent}'
                elif exponent == 1:
                    ans += f'{abs(coefficient)}x' if abs(coefficient) != 1 else 'x'
                else:
                    ans += str(abs(coefficient))
        return ans

    def __len__(self) -> int:
        return len(self.__coefficients)

    def __add__(self, other: GF256Polynomial) -> GF256Polynomial:
        coefficients_1, coefficients_2 = pad_list_left(self.coefficients, other.coefficients)
        resultant_coefficients: list[int] = [c1 ^ c2 for c1, c2 in zip(coefficients_1, coefficients_2)]
        return GF256Polynomial(resultant_coefficients)

    def __sub__(self, other: GF256Polynomial) -> GF256Polynomial:
        return self + other  # addition and subtraction are equivalent in Galois field

    def __mul__(self, other: GF256Polynomial) -> GF256Polynomial:
        resulting_coefficients: list[int] = [0] * (self.degree + other.degree + 1)

        for i, coefficient_1 in enumerate(self.coefficients):
            for j, coefficient_2 in enumerate(other.coefficients):
                resulting_coefficients[i + j] ^= g256_mul(coefficient_1, coefficient_2)

        return GF256Polynomial(resulting_coefficients)

    def __mod__(self, divisor: GF256Polynomial) -> GF256Polynomial:
        if self.degree < divisor.degree:
            return self

        quotient_deg: int = self.degree - divisor.degree
        quotient_factor: int = g256_div(self.coefficients[0], divisor.coefficients[0])
        quotient: GF256Polynomial = GF256Polynomial.monomial(quotient_factor, quotient_deg)
        rem: GF256Polynomial = self - quotient * divisor
        return rem % divisor

    @staticmethod
    def monomial(coefficient: int, degree: int):
        if not 0 < coefficient < 256 or degree < 0:
            raise OutOfFieldError(f'at least one of coefficient: {coefficient} or degree: {degree} is invalid')

        return GF256Polynomial([coefficient] + [0] * degree)

    @property
    def degree(self) -> int:
        return len(self.__coefficients) - 1

    @property
    def coefficients(self) -> list[int]:
        return self.__coefficients

    def _remove_trailing_zeros(self) -> None:
        for i, coefficient in enumerate(self.__coefficients):
            if coefficient != 0:
                self.__coefficients = self.__coefficients[i:]
                return
        self.__coefficients = [0]

    def copy(self) -> GF256Polynomial:
        return GF256Polynomial(self.coefficients)


if __name__ == '__main__':
    p = GF256Polynomial([0, 0, 2, 3, 0, 4, 0, 1, 0, 2, 1])
    print(p.degree)
    print(p.coefficients)
    print(p)
    print(p - GF256Polynomial([1, 2, 3]))
    print(GF256Polynomial([1, 1]) * GF256Polynomial([1, 1]))
