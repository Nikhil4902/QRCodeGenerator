from __future__ import annotations
from PIL import Image


def show(matrix: list[list[bool | tuple | None]]):
    s: int = len(matrix)
    img = Image.new('RGB', (s, s), 'grey')
    pixels = img.load()
    for i in range(s):
        for j in range(s):
            if matrix[i][j] is None:
                continue
            elif isinstance(matrix[i][j], tuple):
                pixels[i, j] = matrix[i][j]
            else:
                if matrix[i][j]:
                    pixels[i, j] = (0, 0, 0)
                else:
                    pixels[i, j] = (255, 255, 255)
    img = img.resize((1000, 1000), Image.NEAREST)
    img.show()


if __name__ == '__main__':
    show([[True, True, True, True], [False, False, True, True], [True, True, False, False], [False, False, False,
                                                                                             False]])
