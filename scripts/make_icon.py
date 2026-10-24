"""Genera el icono geométrico original con formatos ICO/DIB, sin dependencias."""

import struct
from pathlib import Path


def image(size):
    """Dibuja un escudo azul con una marca clara, en coordenadas normalizadas."""
    pixels = bytearray()
    for y in reversed(range(size)):
        for x in range(size):
            px, py = (x + 0.5) / size, (y + 0.5) / size
            half_width = 0.37 if py < 0.58 else max(0, 0.37 * (0.92 - py) / 0.34)
            inside = 0.08 < py < 0.92 and abs(px - 0.5) < half_width
            check = inside and ((0.30 < px < 0.49 and abs(py - (px + 0.22)) < 0.045)
                                or (0.45 < px < 0.73 and abs(py - (1.15 - px)) < 0.045))
            color = (245, 249, 255, 255) if check else ((33, 96, 163, 255) if inside else (0, 0, 0, 0))
            red, green, blue, alpha = color
            pixels.extend((blue, green, red, alpha))
    # Una máscara AND transparente complementa el canal alfa en lectores antiguos.
    mask_stride = ((size + 31) // 32) * 4
    mask = bytearray(mask_stride * size)
    for row in range(size):
        for column in range(size):
            if pixels[(row * size + column) * 4 + 3] == 0:
                mask[row * mask_stride + column // 8] |= 0x80 >> (column % 8)
    header = struct.pack("<IIIHHIIIIII", 40, size, size * 2, 1, 32, 0, len(pixels), 0, 0, 0, 0)
    return header + pixels + mask


def main():
    sizes = (16, 32, 48, 256)
    images = [image(size) for size in sizes]
    offset = 6 + 16 * len(images)
    directory = bytearray(struct.pack("<HHH", 0, 1, len(images)))
    for size, content in zip(sizes, images):
        directory.extend(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(content), offset))
        offset += len(content)
    target = Path(__file__).resolve().parents[1] / "app.ico"
    target.write_bytes(directory + b"".join(images))
    print(target.name)


if __name__ == "__main__":
    main()
