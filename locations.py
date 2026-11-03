"""Cambodian provinces, districts and communes for delivery addresses (data from build_locations.py)."""
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / 'static' / 'data' / 'cambodia.json'
PHNOM_PENH = '12'


@lru_cache(maxsize=1)
def data():
    raw = json.loads(DATA.read_text(encoding='utf-8'))
    return {'provinces': {row[0]: row for row in raw['provinces']},
            'districts': raw['districts'], 'communes': raw['communes']}


def provinces(lang):
    """Provinces sorted by name in the visitor's language, with Phnom Penh first."""
    rows = data()['provinces'].values()
    return sorted(rows, key=lambda row: (row[0] != PHNOM_PENH, name(row, lang)))


def children(kind, parent, lang):
    return sorted(data()[kind].get(parent or '', []), key=lambda row: name(row, lang))


def name(row, lang):
    return row[1] if lang == 'km' else row[2]


def find(province, district, commune):
    """Return the (province, district, commune) rows if the codes belong together, otherwise None."""
    found = data()['provinces'].get(province or '')
    district_row = next((row for row in data()['districts'].get(province or '', []) if row[0] == district), None)
    commune_row = next((row for row in data()['communes'].get(district or '', []) if row[0] == commune), None)
    return (found, district_row, commune_row) if found and district_row and commune_row else None


def describe(rows, street, lang):
    """The address as delivery staff read it: street, commune and district; the province is stored as the city."""
    province, district, commune = rows
    if lang == 'km':
        return ', '.join([street, commune[3] + commune[1], district[3] + district[1]]), province[1]
    return ', '.join([street, commune[2], district[2]]), province[2]
