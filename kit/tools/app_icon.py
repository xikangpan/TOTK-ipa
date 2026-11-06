"""Generate a self-contained PNG app icon and register it in Info.plist.

Uses only Python's standard library; no Mac, Pillow, or game data required.
"""
import math
import plistlib
import struct
import zlib
from pathlib import Path


def _png(width, height, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    scanlines = b''.join(b'\\x00' + bytes(pixels[y * width * 3:(y + 1) * width * 3]) for y in range(height))
    return (b'\\x89PNG\\r\\n\\x1a\\n' +
            chunk(b'IHDR', struct.pack('>2I5B', width, height, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(scanlines, 9)) + chunk(b'IEND', b''))


def _render(size):
    pixels = bytearray(size * size * 3)
    for y in range(size):
        for x in range(size):
            u, v = x / size, y / size
            r = math.hypot(u - .5, v - .48)
            base = max(0, 1 - r * .65)
            color = (int(12 + 20 * base), int(26 + 24 * base), int(28 + 22 * base))
            # Gold triangular crest; deliberately original artwork.
            top = .16
            halfwidth = (v - top) * .62
            outer = top <= v <= .75 and abs(u - .5) <= halfwidth
            inner = .34 <= v <= .61 and abs(u - .5) < (.61 - v) * .55
            if outer and not inner:
                edge = min(1, (v - top) * 1.5)
                color = (int(197 + 40 * edge), int(151 + 33 * edge), int(63 + 25 * edge))
            # Thin ornamental horizontal line beneath the crest.
            if .79 < v < .806 and .19 < u < .81:
                color = (206, 169, 88)
            i = (y * size + x) * 3
            pixels[i:i + 3] = bytes(color)
    return _png(size, size, pixels)


def install_icon(app):
    app = Path(app)
    plist_path = app / 'Info.plist'
    with plist_path.open('rb') as f:
        info = plistlib.load(f)
    # Keep both iPhone and iPad icon declarations, using PNG files in the app root.
    for suffix in ('', '~ipad'):
        key = 'CFBundleIcons' + suffix
        icons = info.get(key)
        if not isinstance(icons, dict):
            icons = {}
        primary = icons.get('CFBundlePrimaryIcon')
        if not isinstance(primary, dict):
            primary = {}
        primary.pop('CFBundleIconName', None)  # Avoid a missing asset-catalog name taking precedence.
        primary['CFBundleIconFiles'] = ['TOTKAppIcon']
        icons['CFBundlePrimaryIcon'] = primary
        info[key] = icons
    info['CFBundleIconFile'] = 'TOTKAppIcon'
    # All supported scales use a full-resolution source.
    (app / 'TOTKAppIcon.png').write_bytes(_render(1024))
    with plist_path.open('wb') as f:
        plistlib.dump(info, f, fmt=plistlib.FMT_BINARY)
