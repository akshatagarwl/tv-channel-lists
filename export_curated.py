#!/usr/bin/env python3
"""Explicitly export reviewed channel facts, never descriptions or personal exports."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from combine import ID


def public_records(entries):
    result = []
    seen = set()
    for entry in entries:
        if entry.get('approved') is not True:
            continue
        channel = entry['id']
        url = entry['source_url']
        parsed = urlsplit(url)
        if (not ID.fullmatch(channel) or channel in seen or parsed.scheme != 'https'
                or parsed.netloc != 'www.youtube.com' or parsed.query or parsed.fragment):
            raise ValueError('Invalid/duplicate reviewed identity or evidence URL')
        name = entry['name'].strip()
        if not name or any(ord(c) < 32 for c in name):
            raise ValueError('Invalid reviewed channel name')
        seen.add(channel)
        result.append({'id': channel, 'name': name, 'category': entry['category'],
                       'approved': True, 'source_url': url, 'checked_at': entry['checked_at']})
    if not result:
        raise ValueError('No approved channels to publish')
    return sorted(result, key=lambda entry: entry['id'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--confirm-reviewed-publication', action='store_true', required=True,
                        help='Explicitly approve publishing these reviewed IDs/names/categories/evidence URLs')
    args = parser.parse_args()
    records = public_records(json.loads(args.review.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    print(f'Exported {len(records)} reviewed records; no descriptions, contact details or account data.')
