#!/usr/bin/python3
#
# Generate directory index for Windows snapshot builds
#
# Copyright (c) 2014, 2022 Benjamin Gilbert
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of version 2.1 of the GNU Lesser General Public License
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import argparse
from datetime import datetime
import dateutil.parser
from jinja2 import Template
import json
import os
from pathlib import Path
import requests
import sys

REPO = 'openslide/builds'
HTML = 'windows/index.html'
JSON = 'windows/index.json'
RETAIN = 30

template = Template('''<!doctype html>

<style type="text/css">
  table {
    margin-left: 20px;
    border-collapse: collapse;
  }
  th.repo {
    padding-right: 1em;
  }
  td {
    padding-right: 20px;
  }
  td.date {
    padding-left: 5px;
  }
  td.revision {
    font-family: monospace;
  }
  td.spacer {
    padding-right: 25px;
  }
  td.winbuild {
    padding-right: 5px;
  }
  tr {
    height: 2em;
  }
  tr:nth-child(2n) {
    background-color: #e8e8e8;
  }
</style>

<title>OpenSlide Windows development builds</title>
<h1>OpenSlide Windows development builds</h1>

<p>Here are the {{ retain }} newest successful nightly builds.
Older builds are automatically deleted.
Builds are skipped if nothing has changed.

{% macro revision_link(repo, prev, cur) %}
  {% if prev %}
    <a href="https://github.com/openslide/{{ repo }}/compare/{{ prev[:8] }}...{{ cur[:8] }}">
      {{ cur[:8] }}
    </a>
  {% else %}
    {{ cur[:8] }}
  {% endif %}
{% endmacro %}

<table>
  <tr>
    <th>Date</th>
    <th class="repo">openslide</th>
    <th class="repo">openslide-java</th>
    <th class="repo">openslide-winbuild</th>
    <th></th>
    <th colspan="3">Downloads</th>
  </tr>
  {% for row in rows %}
    <tr>
      <td class="date">{{ row.date }}</td>
      <td class="revision">
        {{ revision_link('openslide', row.openslide_prev, row.openslide_cur) }}
      </td>
      <td class="revision">
        {{ revision_link('openslide-java', row.java_prev, row.java_cur) }}
      </td>
      <td class="revision">
        {{ revision_link('openslide-winbuild', row.winbuild_prev, row.winbuild_cur) }}
      </td>
      <td class="spacer"></td>
      <td class="win32">
        <a href="https://github.com/openslide/builds/releases/download/windows-{{ row.pkgver }}/openslide-win32-{{ row.pkgver }}.zip">
          32-bit
        </a>
      </td>
      <td class="win64">
        <a href="https://github.com/openslide/builds/releases/download/windows-{{ row.pkgver }}/openslide-win64-{{ row.pkgver }}.zip">
          64-bit
        </a>
      </td>
      <td class="winbuild">
        <a href="https://github.com/openslide/builds/releases/download/windows-{{ row.pkgver }}/openslide-winbuild-{{ row.pkgver }}.zip">
          Corresponding sources
        </a>
      </td>
    </tr>
  {% endfor %}
</table>
''')

def main():
    # Parse command line
    parser = argparse.ArgumentParser(description='Update winbuild index.')
    parser.add_argument('--dir', type=Path,
            default=Path(sys.argv[0]).resolve().parent.parent / 'docs',
            help='Website directory')
    parser.add_argument('--pkgver', metavar='VER',
            help='package version')
    parser.add_argument('--openslide', metavar='COMMIT',
            help='commit ID for OpenSlide')
    parser.add_argument('--java', metavar='COMMIT',
            help='commit ID for OpenSlide Java')
    parser.add_argument('--winbuild', metavar='COMMIT',
            help='commit ID for openslide-winbuild')
    args = parser.parse_args()

    # Get token
    token = os.environ['GITHUB_TOKEN']

    # Load records from JSON
    try:
        with open(args.dir / JSON) as fh:
            records = json.load(fh)['builds']
    except IOError:
        records = []

    # Build new record
    if args.pkgver:
        if not args.openslide or not args.java or not args.winbuild:
            parser.error('New build must be completely specified')
        records.append({
            'pkgver': args.pkgver,
            'date': dateutil.parser.parse(args.pkgver.split('-')[0]).
                    date().isoformat(),
            'openslide': args.openslide,
            'openslide-java': args.java,
            'openslide-winbuild': args.winbuild,
        })

    # Update records
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}',
    }
    for record in records[:-RETAIN]:
        print(f'Deleting {record["pkgver"]}...')
        resp = requests.get(
            f'https://api.github.com/repos/{REPO}/releases/tags/windows-{record["pkgver"]}',
            headers=headers
        )
        if resp.status_code == 404:
            print('...already gone')
            continue
        resp.raise_for_status()
        release = resp.json()
        requests.delete(
            f'https://api.github.com/repos/{REPO}/releases/{release["id"]}',
            headers=headers
        ).raise_for_status()
    records = records[-RETAIN:]

    # Generate rows for HTML template
    rows = []
    prev_record = None
    for record in records:
        def prev(key):
            if prev_record and record[key] != prev_record[key]:
                return prev_record[key]
            else:
                return None
        rows.append({
            'date': record['date'],
            'pkgver': record['pkgver'],
            'openslide_prev': prev('openslide'),
            'openslide_cur': record['openslide'],
            'java_prev': prev('openslide-java'),
            'java_cur': record['openslide-java'],
            'winbuild_prev': prev('openslide-winbuild'),
            'winbuild_cur': record['openslide-winbuild'],
        })
        prev_record = record

    # Write HTML
    with open(args.dir / HTML, 'w') as fh:
        template.stream({
            'retain': RETAIN,
            'rows': reversed(rows),
        }).dump(fh)
        fh.write('\n')

    # Write records to JSON
    with open(args.dir / JSON, 'w') as fh:
        out = {
            'builds': records,
            'last_update': int(datetime.now().timestamp()),
        }
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write('\n')


if __name__ == '__main__':
    main()
