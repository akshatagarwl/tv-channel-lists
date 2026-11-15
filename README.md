# TV Channel Lists

Open code and a small, independently curated YouTube channel-preference list for TizenTube. Python 3.10+, standard library only. **Nothing here connects to or modifies a TV.**

These are optional preference filters, **not authoritative media-bias, misinformation, factual-accuracy or creator-quality ratings**. Being listed does not establish dishonesty or that every video is AI-generated. The lists are non-exhaustive and can produce false positives, especially when a TV card omits its channel ID and matching falls back to a name.

## Public lists

| File | Purpose | License |
| --- | --- | --- |
| [`lists/religion-spirituality.json`](lists/religion-spirituality.json) | 49 manually reviewed channels: devotional/religious teaching, spiritual teachers, new-age/manifestation/astrology and selected re-uploaders | CC0-1.0 for our curation/annotations |

Public records contain only channel IDs, names, categories, evidence URLs, review timestamps and manual approval. Publisher biographies, contact details, raw review files, account information and personal SmartTube exports are not published. Names/trademarks remain their owners'; CC0 does not grant endorsement or rights over third-party content. Full dedication: [`lists/LICENSE`](lists/LICENSE).

## Try just our public list, offline

```sh
python3 -m unittest discover -s tests -v
python3 combine.py --sources religion --output data/curated
```

A separate output directory avoids comparing a small source subset against the full combined snapshot's shrink guard. All generated files stay under ignored `data/`. A community-only build has no personal entries.

## Optional external sources — private local builds only

[`sources.json`](sources.json) pins immutable source commits and preserves source credits/terms:

- **[AiSList](https://github.com/Override92/AiSList)**, via [theSiegs/aislist-channel-ids](https://github.com/theSiegs/aislist-channel-ids): high-confidence blocklist only, **not** its warnlist. List data: **CC BY-NC 4.0**; credit AiSList contributors and the channel-ID conversion by theSiegs. Not covered by this project's MIT/CC0 licenses.
- **[SlopTube](https://github.com/zoomzoom707/SlopTube)**: selected military, geopolitics, Warhammer, reviews and other lists. Upstream says maintenance has stopped. **Redistribution license unconfirmed; no fetched data is republished here.**
- **[MinimalTube](https://github.com/iansquenet/minimaltube-list)**: exact `channelId` entries only. An intentionally broad entertainment/distraction list including mainstream creators, **not a vetted misinformation list**. No imported title keywords, regexes, JavaScript, video IDs or extension options. **Redistribution license unconfirmed; no fetched data is republished here.**
- An optional **private SmartTube export**, kept separate from all community data.

[Free Press India](https://github.com/iamdeepanshugarg/freest-press-india) is **not** used as a block source: it is a discovery directory, not a blacklist; its red-flags data was empty when reviewed.

```sh
python3 combine.py --fetch
# Optional, local only:
python3 combine.py --personal /private/path/to/blocked_channel_data
```

Fetching an external source locally is not permission to redistribute it. Do not upload combined snapshots or fetched files under this repository's licenses. Review source changes before updating pins; there are no automatic list updates.

## Outputs and exceptions

Generated files are ignored/private:

- `community.json`: `[channel ID, display name, source-bitmask]` records.
- `community.gz.b64`: compressed payload for the companion TizenTube build.
- `provenance.json`: source commits, licensing notes, exact file hashes and source counts.
- `personal.json`: private SmartTube entries, never folded into the public curation.
- `summary.json`: counts, overlaps and storage footprint.

Local exceptions belong in ignored `allowlist.txt`, one exact channel ID per line. They are private preferences, not part of the published list. Personal blocks still win. A >50% shrink or excessive packed storage footprint aborts before replacing the last good output. The storage guard leaves headroom below Chromium's 5 MiB localStorage quota; do not bypass it or silently truncate channels.

## Review workflow

```sh
python3 resolve_channels.py candidates.json review.json
```

Candidate JSON maps categories to handle/channel-ID arrays. The resolver fetches YouTube identity metadata but **never auto-approves**; handles can resolve to unrelated people. Keep candidates, descriptions and review evidence under ignored `data/`.

After manual identity/preference/licensing review, explicitly export only minimal public facts:

```sh
python3 export_curated.py data/review.json lists/religion-spirituality.json \
  --confirm-reviewed-publication
```

Review the diff and run tests before publishing. The exporter excludes descriptions/contact details and accepts only boolean-approved entries. Public review is distinct from approving a private list for your own TV.

## Companion projects

- [TizenTube channel-filter fork](https://github.com/akshatagarwl/TizenTube/tree/feat/pr720-channel-block): exact-ID/name indexes, compressed snapshots and independent source switches.
- [Android/iPhone setup preview](https://github.com/akshatagarwl/tv-setup): consent-first installation; list import is **not yet integrated**.
- [Google voice-search handoff](https://github.com/akshatagarwl/tv-search-handoff): retains Google recognition without remote-key filtering.

The TizenTube branch reads localStorage key `tizentube.communityBlocklist.v1` containing the compressed payload. Settings → TizenTube Settings → User Interface Settings → Community lists controls each source independently. Personal Blocked Channels remains separate; history/library/explicit playlist exemptions remain upstream behavior, not an access-control guarantee.

TV import is a **separate, disruptive operation requiring permission**: back up fresh app data, preserve existing preferences, check quota, stop the app before editing storage, then verify blocked/allowed results and real playback. Do not clear app data or replace an entire account profile. Editing/publishing these source lists does **not** update any already-installed TV snapshot.

## License

Builder/resolver/exporter/tests: **MIT**, [`LICENSE`](LICENSE). Our public list curation: **CC0-1.0**, [`lists/LICENSE`](lists/LICENSE). External source data retains its own terms. Personal exports, fetched sources, combined snapshots, account profiles and signing keys are not part of this publication.
