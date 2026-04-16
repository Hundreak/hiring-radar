from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def normalize_name(value: str) -> str:
    return " ".join(value.strip().split())


def read_names(path: Path) -> list[str]:
    if path.suffix.lower() == '.json':
        payload = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(payload, list):
            names = []
            for item in payload:
                if isinstance(item, str):
                    names.append(item)
                elif isinstance(item, dict):
                    for key in ('name', 'university', 'university_name', 'universite'):
                        value = item.get(key)
                        if isinstance(value, str) and value.strip():
                            names.append(value)
                            break
            return names
        raise ValueError('JSON beklenen formatta değil.')

    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError('CSV başlık satırı bulunamadı.')
        candidates = ['name', 'university', 'university_name', 'universite', 'Üniversite', 'UNIVERSITY']
        column = next((field for field in reader.fieldnames if field in candidates), None)
        if column is None:
            raise ValueError('Üniversite adını taşıyan sütun bulunamadı.')
        return [row[column] for row in reader if row.get(column)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='YÖK veya temizlenmiş CSV/JSON dosyası')
    parser.add_argument('--output', default='frontend/src/data/turkish-universities.generated.ts')
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    names = sorted({normalize_name(name) for name in read_names(input_path) if normalize_name(name)}, key=lambda value: value.lower())

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "export const GENERATED_TURKISH_UNIVERSITY_NAMES = " + json.dumps(names, ensure_ascii=False, indent=2) + " as const;\n",
        encoding='utf-8',
    )
    print(f'{len(names)} üniversite kaydedildi -> {output_path}')


if __name__ == '__main__':
    main()
