"""Build static/data/cambodia.json (provinces, districts and communes) from the pumi gazetteer YAML files.

Usage: python build_locations.py PATH_TO_PUMI_DATA  (a folder with provinces.yml, districts.yml and communes.yml from
https://github.com/dwilkie/pumi, MIT licence). Needs PyYAML, which is in requirements-dev.txt.
"""
import json
import sys
from pathlib import Path

import yaml

OUT = Path(__file__).parent / 'static' / 'data' / 'cambodia.json'


def load(folder, name):
    return yaml.safe_load((folder / f'{name}.yml').read_text(encoding='utf-8'))[name]


def entry(code, item):
    # [code, Khmer name, Latin name, Khmer unit word such as ស្រុក or សង្កាត់]
    return [code, item['name']['km'], item['name']['latin'], item['administrative_unit']['km']]


def main(folder):
    folder = Path(folder)
    data = {'provinces': [entry(code, item) for code, item in load(folder, 'provinces').items()], 'districts': {}, 'communes': {}}
    for kind, parent_length in (('districts', 2), ('communes', 4)):
        for code, item in load(folder, kind).items():
            data[kind].setdefault(code[:parent_length], []).append(entry(code, item))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    counts = len(data['provinces']), sum(map(len, data['districts'].values())), sum(map(len, data['communes'].values()))
    print('Wrote %d provinces, %d districts and %d communes to %s' % (*counts, OUT))


if __name__ == '__main__':
    main(sys.argv[1])
