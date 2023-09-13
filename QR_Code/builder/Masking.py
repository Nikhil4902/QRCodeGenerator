from QR_Code.display import Image
from typing import Callable
import copy
from QR_Code.error_correction.Polynomial import GF256Polynomial
from QR_Code.utils.Classes import ECCode


def mask_pattern_0(x, y):
    return (y + x) % 2 == 0


def mask_pattern_1(x, y):
    return y % 2 == 0


def mask_pattern_2(x, y):
    return x % 3 == 0


def mask_pattern_3(x, y):
    return (y + x) % 3 == 0


def mask_pattern_4(x, y):
    return (y // 2 + x // 3) % 2 == 0


def mask_pattern_5(x, y):
    return y * x % 2 + y * x % 3 == 0


def mask_pattern_6(x, y):
    return ((y * x) % 2 + y * x % 3) % 2 == 0


def mask_pattern_7(x, y):
    return ((y + x) % 2 + y * x % 3) % 2 == 0


MASK_DICT: dict[int, Callable[[int, int], bool]] = {
    0: mask_pattern_0,
    1: mask_pattern_1,
    2: mask_pattern_2,
    3: mask_pattern_3,
    4: mask_pattern_4,
    5: mask_pattern_5,
    6: mask_pattern_6,
    7: mask_pattern_7
}

EC_CODES_ORDER = 'LMQH'
FORMAT_DIVISOR = GF256Polynomial([1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1])
FORMAT_MASK = [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0]


class Masker:
    def __init__(self, size: int, version: int, ec_level: ECCode) -> None:
        self.size = size
        self.matrix = [[False for i in range(self.size)] for i in range(self.size)]
        self.version = version
        self.ec_level = ec_level

    def show(self, pattern_no: int = 0) -> None:
        for i in range(self.size):
            for j in range(self.size):
                self.matrix[i][j] = MASK_DICT[pattern_no](i, j)
        Image.show(self.matrix)

    def _add_format_info(self, mask_id: int):
        err_level_idx = EC_CODES_ORDER.index(self.ec_level.name)
        format_poly_coeffs: list[int] = [err_level_idx >> 1, err_level_idx & 1, mask_id >> 2, (mask_id >> 1) & 1, mask_id & 1]
        rem_poly = GF256Polynomial(format_poly_coeffs, 10) % FORMAT_DIVISOR
        if len(rem_poly) < 10:
            format_poly_coeffs.extend([0] * (10 - len(rem_poly)) + rem_poly.coefficients)
        else:
            format_poly_coeffs.extend(rem_poly.coefficients)
        if len(format_poly_coeffs) < 15:
            format_poly_coeffs.extend([1] * (15 - len(format_poly_coeffs)))
        format_poly_coeffs = [bit == 1 for bit in format_poly_coeffs]
        for i in range(6):
            self.matrix[i][8] = self.matrix[8][-(i + 1)] = format_poly_coeffs[i]  # type: ignore
        self.matrix[7][8] = self.matrix[8][-7] = format_poly_coeffs[6]
        self.matrix[8][8] = self.matrix[-8][8] = format_poly_coeffs[7]
        self.matrix[8][7] = self.matrix[-7][8] = format_poly_coeffs[8]

        for i in range(6):
            self.matrix[8][5 - i] = self.matrix[i - 6][8] = format_poly_coeffs[9 + i]

    def apply_mask(self, matrix: list[list[bool]], module_order: list[tuple[int, int]], mask_id: int) -> list[list[bool]]:
        self.matrix = copy.deepcopy(matrix)
        masking_func = MASK_DICT[mask_id]
        for x, y in module_order:
            self.matrix[x][y] = self.matrix[x][y] ^ masking_func(x, y)
        self._add_format_info(mask_id)
        return self.matrix

    def apply_best_mask(self, matrix: list[list[bool]], module_order: list[tuple[int, int]]) -> list[list[bool]]:
        # original_matrix = matrix
        best_mask: int = 0
        best_cost: int = 999999999999999
        for mask_id in range(8):
            self.apply_mask(matrix, module_order, mask_id)
            cost = self._calculate_cost()
            if cost < best_cost:
                best_mask = mask_id
                best_cost = cost
        self.apply_mask(matrix, module_order, best_mask)
        return self.matrix

    def _calculate_cost(self) -> int:
        return self._rule_1() + self._rule_2() + self._rule_3() + self._rule_4()

    def __get_row(self, idx: int) -> list[bool]:
        return [self.matrix[i][idx] for i in range(self.size)]

    def _rule_1(self) -> int:
        def get_penalty_of_line(line: list[bool]) -> int:
            count: int = 0
            current_val: bool = False
            penalty: int = 0
            for val in line:
                if val == current_val:
                    count += 1
                    if count == 5:
                        penalty += 3
                    elif count > 5:
                        penalty += 1
                else:
                    current_val = val
                    count = 1
            return penalty

        net_penalty: int = 0

        for i in range(self.size):
            net_penalty += get_penalty_of_line(self.matrix[i]) + get_penalty_of_line(self.__get_row(i))

        return net_penalty

    def _rule_2(self) -> int:
        def check_square(x: int, y: int) -> bool:
            return (self.matrix[x][y] == self.matrix[x + 1][y] and self.matrix[x + 1][y] == self.matrix[x + 1][y + 1] and
                    self.matrix[x + 1][y + 1] == self.matrix[x][y + 1])

        penalty: int = 0
        for x in range(self.size - 1):
            for y in range(self.size - 1):
                if check_square(x, y):
                    penalty += 3
        return penalty

    def _rule_3(self) -> int:
        R3PATTERN = [True, False, True, True, True, False, True, False, False, False, False]
        REVERSE_R3PATTERN = R3PATTERN[::-1]
        penalty: int = 0
        for i in range(self.size):
            col: list[bool] = self.matrix[i]
            row: list[bool] = self.__get_row(i)
            for j in range(self.size - 11):
                if col[i: i + 11] == R3PATTERN or col[i: i + 11] == REVERSE_R3PATTERN:
                    penalty += 40
                if row[i: i + 11] == R3PATTERN or row[i: i + 11] == REVERSE_R3PATTERN:
                    penalty += 40
        return penalty

    def _rule_4(self) -> int:
        def nearest_5multiple(percent: float) -> int:
            if percent < 50:
                return int(percent // 5 * 5) + 5
            else:
                return int(percent // 5 * 5)

        num_dark_modules = 0
        for x in range(self.size):
            for y in range(self.size):
                num_dark_modules += 1 if self.matrix[x][y] else 0

        rounded_dark_module_percent: int = nearest_5multiple(num_dark_modules / self.size ** 2 * 100)

        return abs(50 - rounded_dark_module_percent) * 2


if __name__ == '__main__':
    m = Masker(25)
    m.show()
