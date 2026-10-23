#!/usr/bin/env python3
"""Normalize Corrigan Peak exception CSV; flag records needing review."""
import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TERMINALS = {'terminal 3': 'Terminal 3', 't3': 'Terminal 3'}
FORMATS = ('%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M')


def normalize(row):
    result = dict(row)
    notes = []
    terminal = (row.get('terminal') or '').strip().lower()
    result['terminal'] = TERMINALS.get(terminal, (row.get('terminal') or '').strip())
    if terminal not in TERMINALS:
        notes.append('Unrecognized terminal label')
    carrier = (row.get('carrier_code') or '').strip().upper()
    result['carrier_code'] = carrier
    if not carrier:
        notes.append('Missing carrier code; cannot infer safely')
    raw = (row.get('event_ts') or '').strip()
    dt = None
    try:
        if raw.endswith('Z'):
            dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        else:
            for fmt in FORMATS:
                try:
                    dt = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    pass
    except ValueError:
        pass
    if dt is None:
        notes.append('Unparseable timestamp')
        result['event_ts'] = raw
    elif dt.tzinfo is None:
        # Source does not specify timezone: preserve local wall-clock, do not invent UTC.
        result['event_ts'] = dt.isoformat(timespec='seconds')
        notes.append('Timezone unspecified; local wall-clock preserved')
    else:
        result['event_ts'] = dt.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    result['review_notes'] = '; '.join(notes)
    result['needs_review'] = 'yes' if any('Missing' in n or 'Unrecognized' in n or 'Unparseable' in n for n in notes) else 'no'
    return result


def process(input_path, output_path):
    with open(input_path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    cleaned = [normalize(row) for row in rows]
    fields = ['exception_id', 'terminal', 'event_type', 'carrier_code', 'event_ts', 'needs_review', 'review_notes']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(cleaned)
    counts = Counter(r['event_type'] for r in cleaned)
    print(f'Processed {len(cleaned)} records; saved {output_path}')
    print('Exceptions by event type:')
    for event, count in sorted(counts.items()):
        print(f'  {event}: {count}')
    print(f'Records needing review: {sum(r["needs_review"] == "yes" for r in cleaned)}')
    for r in cleaned:
        if r['needs_review'] == 'yes':
            print(f'  {r["exception_id"]}: {r["review_notes"]}')
    print('Note: naive timestamps remain timezone-unspecified; no timezone conversion was assumed.')
    return cleaned, counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, default=Path('cleaned_exceptions.csv'))
    args = parser.parse_args()
    process(args.input, args.output)
