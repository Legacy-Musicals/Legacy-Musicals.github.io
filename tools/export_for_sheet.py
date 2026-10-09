"""Write the site's current content as CSV files shaped like the Google Sheet's tabs.

    python tools/export_for_sheet.py

Writes tools/sheet-export/calendar.csv, announcements.csv and cast.csv, each with
the tab's heading row, its row-2 hints and then the content from data/. Load one
into the Sheet with File > Import > Upload, "Replace current sheet", comma
separated, with that tab open. The files carry a byte-order mark so Excel also
reads them as UTF-8; without it Excel shows curly quotes as mojibake.

Once a tab holds rows, the Sheet is in charge of that part of the site, so the
file has to carry everything the tab should show, not just what is new.
"""
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / 'sheet-export'
OUT.mkdir(exist_ok=True)
load = lambda name: json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))

CAL_HEAD = ['Date', 'End date', 'Section', 'Title', 'Performance', 'Track',
            'Time 1', 'What 1', 'Time 2', 'What 2', 'Time 3', 'What 3', 'Notes', 'Cast needed',
            'Study hall time', 'Study hall volunteer', 'Study hall students', 'Study hall note',
            'Link', 'Link label']
CAL_HINT = ['Type like 2026-11-04', 'Only for a run of dates, like tech week',
            'Which heading it sits under', 'Shown in bold',
            'Yes = coral show date, also listed on the Shows page',
            'Only if double cast: a track name from the website settings', 'e.g. 3:30-5:30pm',
            'Who or what', 'Optional', 'Optional', 'Optional', 'Optional',
            'One per line (Ctrl+Enter). A line that is just a time, like 2:00-3:30pm, becomes a heading',
            'Role numbers, e.g. Role #s 1, 4, 11-16. Or ALL CAST, or NO CAST CALLED. Blank = not posted yet',
            'Blank = no helper line', "A parent's name. Or Needed for a sign-up link. Blank = no helper line",
            'Not shown.', 'Small print under the helper line', 'Optional web address', 'Text for the link']


def calendar_rows():
    rows = []
    for cal in load('calendar.json')['calendars']:
        for ev in cal['events']:
            blocks = ev.get('blocks', [])[:3] + [{}] * 3
            helpers = ev.get('helpers') or ev.get('studyHall') or {}
            rows.append([
                ev['date'], ev.get('endDate', ''), cal['heading'], ev['title'],
                'Yes' if ev.get('performance') else '', ev.get('track', ''),
                blocks[0].get('time', ''), blocks[0].get('what', ''),
                blocks[1].get('time', ''), blocks[1].get('what', ''),
                blocks[2].get('time', ''), blocks[2].get('what', ''),
                '\n'.join(ev.get('notes', [])), ev.get('cast', ''),
                helpers.get('time', ''), helpers.get('volunteer', ''),
                helpers.get('students', ''), helpers.get('note', ''),
                ev.get('titleUrl', ''), ev.get('titleUrlLabel', ''),
            ])
    rows.sort(key=lambda r: r[0])
    return rows


def announcement_rows():
    return [['', a.get('date', ''), a.get('icon', ''), a['title'], a.get('detail', ''), a.get('url', '')]
            for a in load('site.json')['announcements']['items']]


def cast_rows():
    return [[m['role'], (m.get('student') or '')] for m in load('cast.json')['members']]


def write(name, head, hint, rows):
    path = OUT / (name + '.csv')
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerow(hint)
        w.writerows(rows)
    print(f'{path.name}: {len(rows)} rows')


write('calendar', CAL_HEAD, CAL_HINT, calendar_rows())
write('announcements',
      ['Show', 'Date', 'Icon', 'Title', 'Detail', 'Link'],
      ['No hides it without deleting', 'Optional, printed above the title', 'One emoji',
       'Shown in bold', 'The line under the title', 'Optional. cast.html links to the Cast page'],
      announcement_rows())
write('cast', ['Role #', 'Student'],
      ['The role number from the Role IDs list (1-35)', 'Their name, once cast. Leave blank until then'],
      cast_rows())
