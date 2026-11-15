#!/usr/bin/env python3
"""Build a private, attributed snapshot of public channel-ID lists. Stdlib only."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent
ID = re.compile(r'UC[\w-]{22}', re.ASCII)
SOURCE_BITS = {'aislist': 1, 'sloptube': 2, 'minimaltube': 4, 'religion': 8}


def text_ids(text):
    return {line.strip() for line in text.splitlines() if ID.fullmatch(line.strip())}


def blocktube_channels(text):
    data = json.loads(text)['filterData']['channelId']
    result = {}
    name = ''
    for line in data:
        match = re.fullmatch(r'// Blocked by context menu \((.*)\)', line.strip())
        if match:
            name = match.group(1)
        elif ID.fullmatch(line.strip()):
            result[line.strip()] = name
            name = ''
        elif line.strip() and not line.strip().startswith('//'):
            name = ''  # Never execute a pattern or carry a label across one.
    return result


def smarttube_entries(text):
    result = {}
    for entry in text.split('%OB%')[0].strip().split('%AR%'):
        channel, sep, name = entry.partition('&vi;')
        if not sep or not name.strip():
            raise ValueError('Malformed SmartTube channel entry')
        key = 'id:' + channel if ID.fullmatch(channel) else 'name:' + name.strip().lower()
        result[key] = name.strip()
    return result


def build(fetch=False, personal=None, selected_sources=None, output=None):
    sources = json.loads((ROOT / 'sources.json').read_text())
    if selected_sources is not None:
        if not selected_sources or set(selected_sources) - set(sources):
            raise ValueError('Choose known, nonempty source names')
        sources = {name: spec for name, spec in sources.items() if name in selected_sources}
    out = Path(output) if output else ROOT / 'data'
    out.mkdir(parents=True, exist_ok=True)
    cache = ROOT / 'data' / 'sources'
    cache.mkdir(parents=True, exist_ok=True)
    records = {}
    counts = {}
    evidence = {}
    for source, spec in sources.items():
        if spec.get('kind') == 'local-curated' and not (ROOT / spec['file']).exists():
            print(f'Skipping optional curation: {source}', file=sys.stderr)
            continue
        files = {}
        hashes = {}
        for name in spec.get('files', []):
            path = cache / (source + '-' + name.replace('/', '_'))
            url = f"https://raw.githubusercontent.com/{spec['repository']}/{spec['commit']}/{name}"
            if fetch:
                request = urllib.request.Request(url, headers={'User-Agent': 'channel-blocklist-builder'})
                with urllib.request.urlopen(request, timeout=60) as response:
                    content = response.read(10_000_001)
                if len(content) > 10_000_000:
                    raise ValueError('Unexpectedly large source')
                path.write_bytes(content)
            content = path.read_bytes()
            hashes[name] = hashlib.sha256(content).hexdigest()
            files[name] = content.decode('utf8')
        if spec.get('kind') == 'local-curated':
            path = ROOT / spec['file']
            content = path.read_bytes()
            entries = json.loads(content)
            channels = {}
            for entry in entries:
                if entry.get('approved') is not True:
                    continue
                if not ID.fullmatch(entry['id']) or not entry.get('source_url'):
                    raise ValueError('Curated channel missing ID/evidence URL')
                channels[entry['id']] = entry['name']
            hashes[spec['file']] = hashlib.sha256(content).hexdigest()
        elif source == 'aislist':
            channels = {channel: '' for channel in text_ids(files['lists/aislist_blocklist_ids.txt'])}
            for line in files['lists/aislist_blocklist_channels.tsv'].splitlines():
                channel, sep, name = line.partition('\t')
                if channel in channels and sep:
                    channels[channel] = name.strip()
        elif source == 'minimaltube':
            channels = blocktube_channels(files['blocktube_backup.json'])
        else:
            channels = {channel: '' for content in files.values() for channel in text_ids(content)}
        if not channels:
            raise ValueError(f'Empty channel list: {source}')
        counts[source] = len(channels)
        evidence[source] = {**spec, 'sha256': hashes, 'channel_count': len(channels)}
        for channel, name in channels.items():
            record = records.setdefault(channel, ['', 0])
            if not record[0] and name:
                record[0] = name.strip()
            record[1] |= SOURCE_BITS[source]

    # Explicit, reviewed exceptions affect community lists only; personal blocks win.
    allowed_path = ROOT / 'allowlist.txt'
    allowed = text_ids(allowed_path.read_text()) if allowed_path.exists() else set()
    for channel in allowed:
        records.pop(channel, None)
    rows = [[channel, name, mask] for channel, (name, mask) in sorted(records.items())]
    payload = {'version': 1, 'sources': SOURCE_BITS, 'channels': rows}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
    packed = base64.b64encode(gzip.compress(encoded, mtime=0))
    # Keep headroom below Chromium's 5 MiB localStorage quota (UTF-16 accounting).
    if len(packed) * 2 > 4_700_000:
        raise ValueError('Snapshot exceeds TV storage budget; do not install')
    previous = out / 'summary.json'
    if previous.exists():
        previous_count = json.loads(previous.read_text())['community_channels']
        if len(rows) < previous_count / 2:
            raise ValueError('Source shrank by over 50%; review before replacing the last good snapshot')
    manual = smarttube_entries(Path(personal).read_text()) if personal else {}
    manual_ids = {key[3:] for key in manual if key.startswith('id:')}
    summary = {'source_counts': counts, 'community_channels': len(rows),
               'community_allowlisted': len(allowed), 'personal_entries': len(manual),
               'unique_ids_including_personal': len(set(records) | manual_ids),
               'personal_name_aliases': sum(key.startswith('name:') for key in manual),
               'packed_utf16_bytes': len(packed) * 2,
               'payload_sha256': hashlib.sha256(encoded).hexdigest()}
    (out / 'community.json').write_bytes(encoded)
    (out / 'community.gz.b64').write_bytes(packed)
    (out / 'provenance.json').write_text(json.dumps(evidence, indent=2) + '\n')
    (out / 'personal.json').write_text(json.dumps(manual, ensure_ascii=False, indent=2) + '\n')
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Fetch the pinned source snapshots')
    parser.add_argument('--personal', help='Optional private SmartTube blocked_channel_data file')
    parser.add_argument('--sources', nargs='+', choices=SOURCE_BITS,
                        help='Build only selected sources; use a separate --output for a small subset')
    parser.add_argument('--output', type=Path, help='Output directory (default: ignored data/)')
    args = parser.parse_args()
    build(args.fetch, args.personal, args.sources, args.output)
