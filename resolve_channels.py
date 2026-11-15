#!/usr/bin/env python3
"""Resolve a PRIVATE candidate file to evidence for manual channel review.

Fetches YouTube's own channel metadata; it does not classify or auto-approve.
Usage: python3 resolve_channels.py candidates.json review.json
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


def resolve(candidate):
    category, handle = candidate
    identity = 'channel/' + handle if re.fullmatch(r'UC[\w-]{22}', handle, re.ASCII) else '@' + handle
    url = 'https://www.youtube.com/' + identity + '/about'
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            html = response.read(5_000_001).decode('utf8')
        match = re.search(r'var ytInitialData = (.*?);</script>', html)
        if not match:
            raise ValueError('No channel metadata')
        metadata = json.loads(match.group(1))['metadata']['channelMetadataRenderer']
        channel = metadata['externalId']
        if not re.fullmatch(r'UC[\w-]{22}', channel, re.ASCII):
            raise ValueError('Invalid channel ID')
        return {'id': channel, 'name': metadata['title'], 'category': category,
                'source_url': url, 'owner_urls': metadata.get('ownerUrls', []),
                'description': metadata.get('description', ''),
                'checked_at': datetime.now(timezone.utc).isoformat(), 'approved': False}
    except (urllib.error.URLError, KeyError, ValueError) as error:
        return {'candidate': handle, 'category': category, 'error': str(error)}


if __name__ == '__main__':
    candidates = json.loads(Path(sys.argv[1]).read_text())
    entries = [(category, handle) for category, handles in candidates.items() for handle in handles]
    with ThreadPoolExecutor(max_workers=4) as executor:
        result = list(executor.map(resolve, entries))
    Path(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for item in result:
        print(item.get('name', item.get('candidate')), item.get('id', item.get('error')))
