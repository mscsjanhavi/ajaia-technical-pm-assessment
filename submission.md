# Ajaia LLC — Technical Project Manager Assessment

**Candidate:** Janhavi Sahasrabudhe  
**Email:** mscsjanhavi@gmail.com  
**Case:** Corrigan Peak Logistics — Dispatch Exception Triage  
**Target go-live in case:** September 8

## Task 1 — Triage

| Priority | Item | This week | Rationale and action |
|---|---|---|---|
| P1 | **B — Routing duplicate risk** | **Work** | A successful queue push followed by a failed database update, or overlapping poll cycles, could route one exception twice. Treat as a release risk. Ask Priya to design an idempotent delivery/consumer contract and safe concurrent claim; test crash-after-push, retries, and overlapping polls before sign-off. |
| P2 | **C — Terminal 3 EDI mismatch (DET-121)** | **Work** | Null urgency scores undermine prioritization and may hide time-critical exceptions. Escalate the stale ticket, request exact field definitions and samples from Corrigan Peak IT today, measure affected volume, and budget the estimated two engineering days **after** IT responds. Route unscorable exceptions to explicit manual review, not a low-urgency default. |
| P3 | **D — Terminal lead review (DET-118)** | **Work** | Routing logic cannot be considered operationally accepted without terminal input. Contact all three leads now, schedule reviews this week, record approvals/disagreements, and reserve time for rule corrections and retest. |
| P4 | **A — Automatic backup-carrier reassignment** | **Defer** | This is a new write-back automation, not a small triage enhancement. It requires eligibility rules, authority to reassign, FreightWorks integration, audit trail, rollback, and safety testing. Offer a post-launch discovery/estimate rather than promise it for September 8. |
| P5 | **E — Blue UI shade** | **Defer** | **Noise.** Cosmetic preference without evidence of accessibility or operational impact; log for later UI polish, not the release-critical path. |

**Launch gate:** Keep September 8 as the committed target, but do not call it guaranteed. Require evidence of duplicate-safe routing, valid scoring or a formally accepted safe fallback for Terminal 3, and signed-off terminal routing rules. Escalate promptly if the gates cannot be met.

**Execution sequence:** Today, pair with Priya on routing failure modes, send Corrigan Peak IT the Terminal 3 field request, and invite the terminal leads. Midweek, inspect test evidence and repaired EDI mapping, conduct rule reviews, and update the risk register daily. Before the release decision, run end-to-end regression with representatives of all three terminals, confirm monitoring/manual fallback, and present a go/no-go recommendation with owners and residual risks.

## Task 2 — Working normalization script

**Files:** `normalize_exceptions.py` (script), `exceptions_raw.csv` (source sample), `cleaned_exceptions.csv` (output), and `test_normalize.py` (automated test).

**Run:**

```bash
python normalize_exceptions.py exceptions_raw.csv --output cleaned_exceptions.csv
python -m unittest -v test_normalize.py
```

**Observed output:**

```text
Processed 5 records
Exceptions by event type:
  carrier_substitution: 1
  doc_mismatch: 2
  missed_pickup: 2
Records needing review: 1
  CPX-88216: Missing carrier code; cannot infer safely
Automated test: OK (1 test)
```

**What it does and how I checked it:** The Python standard-library script reads the five-row export, normalizes `T3` and `Terminal 3` to `Terminal 3`, uppercases carrier codes, and formats parseable timestamps consistently in ISO 8601 style. It preserves explicit UTC (`Z`) and retains the original wall-clock time for timestamps without a timezone, rather than inventing an offset. It counts exceptions by event type and writes review notes to the cleaned CSV. I executed the script against the provided data, inspected the output, and ran automated assertions checking row count, all three event counts, terminal and carrier normalization, explicit UTC preservation, and the missing-carrier flag. The test passed. **CPX-88216 cannot be fully cleaned** because its carrier code is blank; the script does not guess. The timezone of four naive timestamps is also unknown, and that uncertainty is recorded. This sample cleanup does **not** prove that the production FreightWorks EDI-to-urgency-score defect is fixed.

### Script (`normalize_exceptions.py`)

```python
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
```

## Task 3 — Client status update

**To:** Dana Okafor, VP Operations, Corrigan Peak Logistics  
**Subject:** Dispatch Exception Triage — September 8 readiness and decisions needed

Hi Dana,

I want to correct the impression left by last Friday's green update. Our current status is **AMBER**. September 8 remains the target, but we have identified two technical risks that need resolution and verification before I can recommend release.

First, our engineering review identified a duplicate-routing scenario: if a dispatcher-queue push succeeds but its database status update fails, a retry may send the same exception again; overlapping polling cycles create a similar risk. Priya is prioritizing a concurrency-safe, idempotent approach and failure-path testing this week. We will not mark this ready based on a happy-path demo alone.

Second, Terminal 3's EDI field mismatch is producing null urgency scores for some exceptions. This is more significant than the “minor data validation” item described last week. **We need a Corrigan Peak IT owner to confirm the fields Terminal 3 actually transmits and provide representative records as soon as possible.** Engineering currently estimates approximately two additional days once that answer arrives. Until the mapping is validated, affected exceptions must be visible for manual triage rather than silently treated as low urgency.

We are also reaching out to all three terminal leads this week to schedule routing-rules reviews and obtain operational sign-off. I will track unresolved decisions and retest any rules changed as a result.

On the COO's request to automatically reassign missed pickups to a backup carrier: I see the value, but that introduces a new operational action requiring carrier-eligibility rules, permissions, FreightWorks write-back behavior, and failure recovery. My recommendation is to **keep automatic reassignment outside the September 8 scope** and schedule a focused discovery session to define a safe follow-on release. The September 8 tool will flag and route those exceptions for a dispatcher to decide, as originally scoped.

**Next checkpoint:** I will share an updated risk and milestone view after the engineering investigation and IT field confirmation, including test results, terminal review progress, and any date implications. If the release gates cannot be met, I will bring you options and trade-offs early rather than waiting until launch week. I know September 8 is a board-level commitment, and we will manage it with that visibility while protecting dispatch operations.

Best,  
Janhavi Sahasrabudhe  
Technical Project Manager, Ajaia (assessment scenario)

## Task 4 — AI workflow note

I used AI to help structure the triage, draft and edit the client update, and generate an initial Python script and test. I retained the human decisions about launch gates, what to defer, and what evidence would justify sign-off; I also reviewed the code's assumptions and ran the script and automated test rather than trusting generated text. A specific assumption I chose **not** to make was converting timestamps without timezone data to UTC: that would produce precise-looking but unsupported timestamps. I also refused to infer the missing carrier code for CPX-88216. The cleaned sample is evidence of normalization, not evidence that the upstream EDI scoring issue has been repaired.

## Video submission

**Recording:** [Add the video link or upload reference after recording.]

Suggested 5–10 minute walkthrough: (1) introduce the project and launch gates; (2) walk through P1–P5 and explain the scope boundary; (3) run the Python script and unit test on screen, then inspect CPX-88216; (4) present the amber client update and dependencies; (5) close with your own background, why Ajaia, and your salary expectation **without disclosing current compensation**.
