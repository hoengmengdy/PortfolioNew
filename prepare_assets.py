"""Download and optimize redistributable presentation assets; run once."""
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).parent
ASSETS = {
    'hero': ('photo-1608571423902-eed4a5ad8108', 1600),
    'botanical': ('photo-1441974231531-c6227db76b6e', 1200),
}


def download(item):
    name, (photo, width) = item
    url = f'https://images.unsplash.com/{photo}?auto=format&fit=crop&w={width}&q=85'
    request = urllib.request.Request(url, headers={'User-Agent': 'EmpressCambodia/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        image = Image.open(io.BytesIO(response.read())).convert('RGB')
    image.save(ROOT / 'static/images' / f'{name}.webp', 'WEBP', quality=82, method=6)
    if name == 'hero':
        image.thumbnail((800, 800))
        image.save(ROOT / 'static/images/hero-small.webp', 'WEBP', quality=80)
    return name


GOOGLE_FONTS = 'https://raw.githubusercontent.com/google/fonts/main/ofl/'
LATIN = [*range(0x20, 0x7F), *range(0xA0, 0x180), 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x20AC, 0x2122]
KHMER = [*range(0x1780, 0x1800), *range(0x19E0, 0x1A00), 0x200B, 0x200C, 0x200D, 0x25CC]
# Output file: (source in Google Fonts, variable range to keep, characters to keep, licence folder).
FONTS = {
    'cormorant.woff2': ('cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf', {'wght': (400, 700)}, LATIN, 'cormorantgaramond'),
    'jost.woff2': ('jost/Jost%5Bwght%5D.ttf', {'wght': (300, 700)}, LATIN, 'jost'),
    'khmer-serif.woff2': ('notoserifkhmer/NotoSerifKhmer%5Bwdth,wght%5D.ttf', {'wdth': 100, 'wght': (400, 700)}, KHMER, 'notoserifkhmer'),
    'khmer-sans.woff2': ('kantumruypro/KantumruyPro%5Bwght%5D.ttf', {'wght': (300, 700)}, KHMER, 'kantumruypro'),
}


def build_fonts():
    """Download the site fonts, keep only the weights and characters used, and save them as small WOFF2 files."""
    folder = ROOT / 'static/fonts'
    for name, (source, limits, characters, licence) in FONTS.items():
        with urllib.request.urlopen(GOOGLE_FONTS + source) as response:
            font = TTFont(io.BytesIO(response.read()))
        options = subset.Options(layout_features=['*'], hinting=False, notdef_outline=True)
        subsetter = subset.Subsetter(options)
        subsetter.populate(unicodes=characters)
        subsetter.subset(font)
        font = instancer.instantiateVariableFont(font, limits)
        font.flavor = 'woff2'
        font.save(folder / name)
        urllib.request.urlretrieve(f'{GOOGLE_FONTS}{licence}/OFL.txt', folder / f'{licence}-OFL.txt')


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:
        print(list(pool.map(download, ASSETS.items())))
    font_url = 'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.7.2/'
    for source, target in [('css/all.min.css', 'static/css/fontawesome.min.css'), ('webfonts/fa-solid-900.woff2', 'static/webfonts/fa-solid-900.woff2'), ('webfonts/fa-brands-400.woff2', 'static/webfonts/fa-brands-400.woff2'), ('webfonts/fa-regular-400.woff2', 'static/webfonts/fa-regular-400.woff2'), ('LICENSE.txt', 'static/fonts/FONT-AWESOME-LICENSE.txt')]:
        path = ROOT / target
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(font_url + source, path)
    build_fonts()
