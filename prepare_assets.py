"""Download and optimize redistributable presentation assets; run once."""
import io
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
from fontTools.ttLib import TTFont

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


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:
        print(list(pool.map(download, ASSETS.items())))
    font_url = 'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.7.2/'
    for source, target in [('css/all.min.css', 'static/css/fontawesome.min.css'), ('webfonts/fa-solid-900.woff2', 'static/webfonts/fa-solid-900.woff2'), ('webfonts/fa-brands-400.woff2', 'static/webfonts/fa-brands-400.woff2'), ('webfonts/fa-regular-400.woff2', 'static/webfonts/fa-regular-400.woff2'), ('LICENSE.txt', 'static/fonts/FONT-AWESOME-LICENSE.txt')]:
        path = ROOT / target
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(font_url + source, path)
    fonts = {
        'inter.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf',
        'display.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf',
        'body.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/dmsans/DMSans%5Bopsz,wght%5D.ttf',
        'khmer.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskhmer/NotoSansKhmer%5Bwdth,wght%5D.ttf',
    }
    for name, url in fonts.items():
        urllib.request.urlretrieve(url, ROOT / 'static/fonts' / name)
        font = TTFont(ROOT / 'static/fonts' / name)
        font.flavor = 'woff2'
        font.save(ROOT / 'static/fonts' / name.replace('.ttf', '.woff2'))
    for folder in ('inter', 'cormorantgaramond', 'dmsans', 'notosanskhmer'):
        urllib.request.urlretrieve(f'https://raw.githubusercontent.com/google/fonts/main/ofl/{folder}/OFL.txt', ROOT / 'static/fonts' / f'{folder}-OFL.txt')
