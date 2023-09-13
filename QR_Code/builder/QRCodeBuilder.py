from __future__ import annotations
import sys
from QR_Code.processing.Sequencing import (get_smallest_version_and_ec, get_smallest_version_from_ec, get_encoding_mode, Encoder,
                                           int_to_bit)
from QR_Code.error_correction.Reed_Solomon import get_error_correction_words, get_total_codewords
from QR_Code.error_correction.Polynomial import GF256Polynomial
from QR_Code.display import Image
from QR_Code.builder.Masking import Masker
from QR_Code.utils.Exceptions import CannotDrawPatternError
from QR_Code.utils.Classes import ECCode

sys.setrecursionlimit(5000)

BLACK = True
WHITE = False

ALIGNMENT_PATTERN_POSITION_TABLE = [
    [],
    [6, 18],
    [6, 22],
    [6, 26],
    [6, 30],
    [6, 34],
    [6, 22, 38],
    [6, 24, 42],
    [6, 26, 46],
    [6, 28, 50],
    [6, 30, 54],
    [6, 32, 58],
    [6, 34, 62],
    [6, 26, 46, 66],
    [6, 26, 48, 70],
    [6, 26, 50, 74],
    [6, 30, 54, 78],
    [6, 30, 56, 82],
    [6, 30, 58, 86],
    [6, 34, 62, 90],
    [6, 28, 50, 72, 94],
    [6, 26, 50, 74, 98],
    [6, 30, 54, 78, 102],
    [6, 28, 54, 80, 106],
    [6, 32, 58, 84, 110],
    [6, 30, 58, 86, 114],
    [6, 34, 62, 90, 118],
    [6, 26, 50, 74, 98, 122],
    [6, 30, 54, 78, 102, 126],
    [6, 26, 52, 78, 104, 130],
    [6, 30, 56, 82, 108, 134],
    [6, 34, 60, 86, 112, 138],
    [6, 30, 58, 86, 114, 142],
    [6, 34, 62, 90, 118, 146],
    [6, 30, 54, 78, 102, 126, 150],
    [6, 24, 50, 76, 102, 128, 154],
    [6, 28, 54, 80, 106, 132, 158],
    [6, 32, 58, 84, 110, 136, 162],
    [6, 26, 54, 82, 110, 138, 166],
    [6, 30, 58, 86, 114, 142, 170]
]

EC_FORMATTING_DICT = {
    ECCode.L: [WHITE, BLACK],
    ECCode.M: [WHITE, WHITE],
    ECCode.Q: [BLACK, WHITE],
    ECCode.H: [BLACK, BLACK]
}


def get_size_info(version: int) -> int:
    return version * 4 + 17


class QRCodeBuilder:
    def __init__(self, message: str, ec_level: ECCode = None):
        self._message = message
        if ec_level is None:
            self.version, self.ec_level = get_smallest_version_and_ec(len(message), get_encoding_mode(message))
        else:
            self.version, self.ec_level = get_smallest_version_from_ec(len(message), get_encoding_mode(message), ec_level)
        self.size: int = get_size_info(self.version)
        self.matrix: list[list[bool | tuple | None]] = [[None for row in range(self.size)] for col in range(self.size)]
        self.draw_finder_patterns()
        self.draw_timing_patterns()
        self.draw_dark_module()
        self.draw_alignment_patterns()
        self.draw_all_format_info()
        seq = self._get_module_sequence()
        self.fill_data()
        m = Masker(self.size, self.version, self.ec_level)
        self.matrix = m.apply_best_mask(self.matrix, seq)

    def show(self) -> None:
        print(self._message)
        print(self.version)
        print(self.ec_level)
        print(self.size)
        self.add_edge_to_matrix()
        Image.show(self.matrix)

    def fill_data(self) -> None:
        encoder = Encoder(self.version, self.ec_level)
        encoded_data = encoder.encode(self._message)
        ec_data = get_error_correction_words(GF256Polynomial(encoded_data), get_total_codewords(self.version, self.ec_level))
        all_data = encoded_data + ec_data

        data_as_bits = "".join([int_to_bit(byte) for byte in all_data])
        data_as_bits += '0' * (self._get_total_available_bit_space() - len(data_as_bits))
        print(len(self._get_module_sequence()))
        print(self._get_total_available_bit_space())
        for pos, data in zip(self._get_module_sequence(), data_as_bits):
            self.matrix[pos[0]][pos[1]] = BLACK if data == '1' else WHITE

    def _get_total_available_bit_space(self):
        return (self.size ** 2) - (((self.version // 7 + 2) ** 2) - 3) * 25 - 241

    def draw_finder_patterns(self) -> None:
        self._draw_finder_pattern(0, 0)
        self._draw_finder_pattern(0, self.size - 7)
        self._draw_finder_pattern(self.size - 7, 0)
        self._draw_finder_pattern_edges()

    def draw_alignment_patterns(self) -> None:
        alignment_tracks: list[int] = ALIGNMENT_PATTERN_POSITION_TABLE[self.version - 1]
        for row in alignment_tracks:
            for col in alignment_tracks:
                if ((row - 2 <= 7 and col - 2 <= 7) or (row - 2 <= 7 and col + 2 >= self.size - 7)
                        or (row + 2 >= self.size - 7 and col - 2 <= 7)):
                    continue
                else:
                    self._draw_alignment_pattern(row, col)

    def draw_dark_module(self) -> None:
        self.matrix[8][self.size - 8] = BLACK

    def draw_timing_patterns(self) -> None:
        for i in range(self.size - 14):
            if i % 2 != 0:
                self.matrix[6][7 + i] = BLACK
                self.matrix[7 + i][6] = BLACK
            else:
                self.matrix[6][7 + i] = WHITE
                self.matrix[7 + i][6] = WHITE

    def _draw_finder_pattern(self, x: int, y: int) -> None:
        if x > self.size - 7 or y > self.size - 7:
            raise CannotDrawPatternError(f'trying to draw a finder pattern at <{x}, {y}> in a QR Code of size {self.size}')
        self.matrix[x + 0][y: y + 7] = [BLACK for _ in range(7)]
        self.matrix[x + 1][y: y + 7] = [BLACK, WHITE, WHITE, WHITE, WHITE, WHITE, BLACK]
        for i in range(2, 5):
            self.matrix[x + i][y: y + 7] = [BLACK, WHITE, BLACK, BLACK, BLACK, WHITE, BLACK]
        self.matrix[x + 5][y: y + 7] = [BLACK, WHITE, WHITE, WHITE, WHITE, WHITE, BLACK]
        self.matrix[x + 6][y: y + 7] = [BLACK for _ in range(7)]

    def _draw_finder_pattern_edges(self) -> None:
        self.matrix[7][:8] = [WHITE] * 8
        self.matrix[7][-8:] = [WHITE] * 8
        self.matrix[self.size - 8][:8] = [WHITE] * 8
        for i in range(7):
            self.matrix[i][7] = WHITE
            self.matrix[self.size - i - 1][7] = WHITE
            self.matrix[i][self.size - 8] = WHITE

    def _draw_alignment_pattern(self, x: int, y: int) -> None:
        self.matrix[x - 2][y - 2: y + 3] = [BLACK, BLACK, BLACK, BLACK, BLACK]
        self.matrix[x - 1][y - 2: y + 3] = [BLACK, WHITE, WHITE, WHITE, BLACK]
        self.matrix[x][y - 2: y + 3] = [BLACK, WHITE, BLACK, WHITE, BLACK]
        self.matrix[x + 1][y - 2: y + 3] = [BLACK, WHITE, WHITE, WHITE, BLACK]
        self.matrix[x + 2][y - 2: y + 3] = [BLACK, BLACK, BLACK, BLACK, BLACK]

    def add_edge_to_matrix(self) -> None:
        self.matrix.insert(0, [WHITE for _ in range(self.size)])
        self.matrix.append([WHITE for _ in range(self.size)])
        for i in range(self.size + 2):
            self.matrix[i] = [WHITE] + self.matrix[i] + [WHITE]

    def _get_module_sequence(self) -> list[tuple[int, int]]:
        row_step: int = -1
        row = col = self.size - 1
        module_sequence: list[tuple[int, int]] = []
        index: int = 0

        while col >= 0:
            if self.matrix[col][row] != BLACK and self.matrix[col][row] != WHITE:
                module_sequence.append((col, row))

            if index & 1:  # checking if index is odd
                row += row_step
                if row == -1 or row == self.size:
                    row_step = - row_step  # flipping direction if we reach the edge
                    row += row_step
                    col -= 2 if col == 7 else 1
                else:
                    col += 1
            else:
                col -= 1
            index += 1
        return module_sequence

    def draw_all_format_info(self):
        # need to change
        self.matrix[8][:8] = [WHITE] * 6 + [BLACK, WHITE]
        self.matrix[8][-7:] = [WHITE] * 7
        for i in range(9):
            if i != 8:
                self.matrix[self.size - i - 1][8] = WHITE
            if i != 6:
                self.matrix[i][8] = WHITE

    def draw_format_info(self):
        self.matrix[0][8], self.matrix[1][8] = EC_FORMATTING_DICT[self.ec_level]
        self.matrix[8][-1], self.matrix[8][-2] = EC_FORMATTING_DICT[self.ec_level]

    def draw_mask_pattern(self):
        self.matrix[2][8], self.matrix[3][8], self.matrix[4][8] = [WHITE, WHITE, WHITE]
        self.matrix[8][-3], self.matrix[8][-4], self.matrix[8][-5] = [WHITE, WHITE, WHITE]


qr = QRCodeBuilder("nikhilsaigorantla478nikhil", ECCode.H)
qr.show()
# doesn't work when combining nums with other chars
# some issue with error correction or masking(probly ec) need to fix
