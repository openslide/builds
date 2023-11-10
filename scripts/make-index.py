#!/usr/bin/python3
#
# Generate directory index for snapshot builds
#
# Copyright (c) 2014, 2022-2023 Benjamin Gilbert
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
CONTAINERS = ('openslide/linux-builder', 'openslide/winbuild-builder')
HTML = 'index.html'
JSON = 'index.json'
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
  td.linux {
    padding-right: 5px;
  }
  tr {
    height: 2em;
  }
  tr:nth-child(2n) {
    background-color: #e8e8e8;
  }
</style>

<title>OpenSlide development builds</title>
<h1>OpenSlide development builds</h1>

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

{% macro builder_link(builder) %}
  {% set builder_short = builder.split('@')[1].split(':')[1][:8] %}
  {% if builder in container_images %}
    <a href="{{ container_images[builder] }}">
      {{ builder_short }}
    </a>
  {% else %}
    {{ builder_short }}
  {% endif %}
{% endmacro %}

{% macro artifact_link(row, suffix, desc) %}
  {% if suffix in row.files %}
    <a href="https://github.com/openslide/builds/releases/download/v{{ row.version }}/openslide-bin-{{ row.version }}{{ suffix }}">
      {{ desc }}
    </a>
  {% endif %}
{% endmacro %}

<table>
  <tr>
    <th>Date</th>
    <th class="repo">openslide</th>
    <th class="repo">openslide-java</th>
    <th class="repo">openslide-bin</th>
    <th class="repo">linux-builder</th>
    <th class="repo">winbuild-builder</th>
    <th></th>
    <th colspan="4">Downloads</th>
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
        {{ revision_link('openslide-bin', row.bin_prev, row.bin_cur) }}
      </td>
      <td class="revision">
        {% if '-linux-x86_64.tar.xz' in row.files %}
          {{ builder_link(row.linux_builder) }}
        {% endif %}
      </td>
      <td class="revision">
        {{ builder_link(row.windows_builder) }}
      </td>
      <td class="spacer"></td>
      <td class="source">
        {{ artifact_link(row, '.tar.gz', 'Source') }}
      </td>
      <td class="win64">
        {{ artifact_link(row, '-windows-x64.zip', 'Windows x64') }}
      </td>
      <td class="macos">
        {{ artifact_link(row, '-macos-arm64-x86_64.tar.xz', 'macOS') }}
      </td>
      <td class="linux">
        {{ artifact_link(row, '-linux-x86_64.tar.xz', 'Linux') }}
      </td>
    </tr>
  {% endfor %}
</table>
''')

def main():
    # Parse command line
    parser = argparse.ArgumentParser(description='Update build index.')
    parser.add_argument('--dir', type=Path,
            default=Path(sys.argv[0]).resolve().parent.parent / 'site',
            help='Website directory')
    parser.add_argument('--version', metavar='VER',
            help='package version')
    parser.add_argument('--files', type=Path, metavar='DIR',
            help='directory containing files for new build')
    parser.add_argument('--linux-builder', metavar='REF',
            help='Linux builder container reference')
    parser.add_argument('--windows-builder', metavar='REF',
            help='Windows builder container reference')
    parser.add_argument('--openslide', metavar='COMMIT',
            help='commit ID for OpenSlide')
    parser.add_argument('--java', metavar='COMMIT',
            help='commit ID for OpenSlide Java')
    parser.add_argument('--bin', metavar='COMMIT',
            help='commit ID for openslide-bin')
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
    if args.version:
        if (
            not args.linux_builder or not args.windows_builder or
            not args.openslide or not args.java or not args.bin or
            not args.files
        ):
            parser.error('New build must be completely specified')
        records.append({
            'version': args.version,
            'date': dateutil.parser.parse(
                args.version.split('+')[1].split('.')[0]
            ).date().isoformat(),
            'files': sorted(
                path.name.split(f'{args.version}')[1]
                for path in args.files.iterdir()
            ),
            'linux-builder': args.linux_builder,
            'windows-builder': args.windows_builder,
            'openslide': args.openslide,
            'openslide-java': args.java,
            'openslide-bin': args.bin,
        })

    # Update records
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}',
    }
    for record in records[:-RETAIN]:
        print(f'Deleting {record["version"]}...')
        resp = requests.get(
            f'https://api.github.com/repos/{REPO}/releases/tags/v{record["version"]}',
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

    # Get builder container image URLs
    container_images = {}
    for container in CONTAINERS:
        container_org, container_name = container.split('/')
        resp = requests.get(
            f'https://api.github.com/orgs/{container_org}/packages/container/{container_name}/versions?per_page=100',
            headers=headers
        )
        resp.raise_for_status()
        for image in resp.json():
            ref = f'ghcr.io/{container_org}/{container_name}@{image["name"]}'
            container_images[ref] = image['html_url']

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
            'version': record['version'],
            'files': record['files'],
            'linux_builder': record['linux-builder'],
            'windows_builder': record['windows-builder'],
            'openslide_prev': prev('openslide'),
            'openslide_cur': record['openslide'],
            'java_prev': prev('openslide-java'),
            'java_cur': record['openslide-java'],
            'bin_prev': prev('openslide-bin'),
            'bin_cur': record['openslide-bin'],
        })
        prev_record = record

    # Write HTML
    with open(args.dir / HTML, 'w') as fh:
        template.stream({
            'container_images': container_images,
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
