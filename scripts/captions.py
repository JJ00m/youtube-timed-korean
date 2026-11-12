#!/usr/bin/env python3
"""Caption evidence utilities. Summaries are authored by the calling agent."""
import argparse
from datetime import datetime, timezone
import html
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlparse


def video_id(value):
    if not isinstance(value, str):
        raise ValueError('Video URL or ID must be a string')
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', value):
        return value
    url = urlparse(value)
    if url.scheme not in ('https', 'http'):
        raise ValueError('Expected a YouTube URL or an 11-character video ID')
    parts = url.path.strip('/').split('/')
    if url.hostname in ('youtu.be', 'www.youtu.be') and len(parts) == 1:
        candidate = parts[0]
    elif url.hostname in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
        if url.path == '/watch':
            candidate = parse_qs(url.query).get('v', [''])[0]
        elif len(parts) == 2 and parts[0] in ('shorts', 'live', 'embed'):
            candidate = parts[1]
        else:
            candidate = ''
    else:
        candidate = ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', candidate):
        raise ValueError('Invalid YouTube video URL or ID')
    return candidate


def milliseconds(value, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Timestamps must be finite numbers in milliseconds')
    if not math.isfinite(value) or value < 0 or (positive and value <= 0):
        raise ValueError('Invalid timestamp or duration')
    result = round(value)
    if positive and result <= 0:
        raise ValueError('Duration must be at least one millisecond')
    return result


def normalize(raw, provider):
    if not isinstance(raw, dict):
        raise ValueError('Expected a caption JSON object')
    if raw.get('error') or raw.get('success') is False:
        raise ValueError('Provider error: ' + str(raw.get('error', 'request failed')))
    if isinstance(raw.get('data'), dict) and 'alexandria' in raw['data']:
        entries = raw['data']['alexandria']
        if not isinstance(entries, list) or len(entries) != 1:
            raise ValueError('Import exactly one transcript result at a time')
        entry = entries[0]
        if entry.get('error'):
            raise ValueError('Provider error: ' + str(entry['error']))
        raw = entry.get('data', {})
        return normalize(raw, provider)
    if raw.get('schema_version') == 1:
        inspect(raw)
        return raw
    if raw.get('has_transcript') is False or not raw.get('segments'):
        raise ValueError('No timed transcript available; do not infer timing from metadata')
    if 'segment_count' in raw and raw['segment_count'] != len(raw['segments']):
        raise ValueError('Segment count mismatch: possible partial response')
    vid = video_id(raw.get('video_id', ''))
    doc = {'schema_version': 1, 'video_id': vid,
           'source_url': f'https://www.youtube.com/watch?v={vid}',
           'title': raw.get('title', vid), 'language': raw.get('language_code', 'unknown'),
           'kind': raw.get('kind', 'unknown'), 'provider': provider,
           'retrieved_at': datetime.now(timezone.utc).isoformat(), 'segments': []}
    for i, item in enumerate(raw['segments'], 1):
        if not isinstance(item, dict):
            raise ValueError('Each segment must be an object')
        text = item.get('text')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Caption text is missing')
        doc['segments'].append({'id': f's{i:04d}',
                                'start_ms': milliseconds(item.get('start_ms')),
                                'duration_ms': milliseconds(item.get('duration_ms'), True),
                                'text': text})
    inspect(doc)
    return doc


def inspect(doc):
    if not isinstance(doc, dict) or doc.get('schema_version') != 1:
        raise ValueError('Expected normalized schema_version 1')
    vid = doc.get('video_id', '')
    if video_id(vid) != vid:
        raise ValueError('Normalized video_id must be a canonical 11-character ID')
    segments = doc.get('segments')
    if not isinstance(segments, list) or not segments:
        raise ValueError('No caption segments')
    seen, previous_start, furthest_end, overlaps, largest_gap = set(), -1, 0, 0, 0
    for seg in segments:
        if not isinstance(seg, dict):
            raise ValueError('Each segment must be an object')
        sid = seg.get('id')
        if not isinstance(sid, str) or not re.fullmatch(r's[0-9]+', sid) or sid in seen:
            raise ValueError('Missing or duplicate segment ID')
        if not isinstance(seg.get('text'), str) or not seg['text'].strip():
            raise ValueError('Empty caption text')
        start = milliseconds(seg.get('start_ms'))
        duration = milliseconds(seg.get('duration_ms'), True)
        if start < previous_start:
            raise ValueError('Caption starts are not monotonic; inspect the source')
        if seen and start < furthest_end:
            overlaps += 1
        if seen:
            largest_gap = max(largest_gap, start - furthest_end)
        furthest_end = max(furthest_end, start + duration)
        previous_start = start
        seen.add(sid)
    return {'video_id': doc['video_id'], 'segment_count': len(segments),
            'first_start_ms': segments[0]['start_ms'], 'last_end_ms': furthest_end,
            'overlap_count': overlaps, 'largest_gap_ms': largest_gap,
            'timing_metadata_valid': True, 'audio_alignment_verified': False,
            'note': 'Overlap is preserved. Gaps do not prove missing captions. Metadata validity does not prove full-video coverage or ASR accuracy.'}


def timestamp(value):
    total = milliseconds(value)
    seconds, ms = divmod(total, 1000)
    minutes, sec = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    return (f'{hours:02d}:' if hours else '') + f'{minute:02d}:{sec:02d}.{ms:03d}'


def safe_text(value):
    text = html.escape(str(value)).replace('|', '&#124;').replace('\n', ' ').replace('\r', ' ')
    # Source text must remain text, never become Markdown links or remote images.
    return re.sub(r'([\\`*_{}\[\]()#!])', r'\\\1', text)


def render(doc, summary):
    inspect(doc)
    if not isinstance(summary, dict) or summary.get('mode') != 'summary':
        raise ValueError('This release renders topic summaries only; use mode=summary')
    items = summary.get('items')
    if not isinstance(items, list) or not items:
        raise ValueError('Summary items must be a nonempty list')
    by_id = {seg['id']: seg for seg in doc['segments']}
    url = f'https://www.youtube.com/watch?v={doc["video_id"]}'
    rows = [f'# {safe_text(doc.get("title", doc["video_id"]))} — 한국어 요약', '',
            f'출처: [{doc["video_id"]}]({url})',
            f'자막: {safe_text(doc.get("language", "unknown"))} / {safe_text(doc.get("kind", "unknown"))}. 시간은 자막 메타데이터 기준이며 음성과 별도 대조하지 않았습니다.', '',
            '| 시간 | 내용 | 근거 자막 ID |', '|---|---|---|']
    last_start = -1
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Summary item must be an object')
        ids, text = item.get('source_ids'), item.get('text')
        if not isinstance(ids, list) or not ids or any(not isinstance(sid, str) for sid in ids):
            raise ValueError('Each summary item needs source_ids')
        if len(set(ids)) != len(ids) or any(sid not in by_id for sid in ids):
            raise ValueError('Unknown or duplicate source reference')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Summary text is empty')
        start = min(by_id[sid]['start_ms'] for sid in ids)
        end = max(by_id[sid]['start_ms'] + by_id[sid]['duration_ms'] for sid in ids)
        if start < last_start:
            raise ValueError('Summary topics must be chronological')
        last_start = start
        label = f'{timestamp(start)}–{timestamp(end)}'
        rows.append(f'| [{label}]({url}&t={start // 1000}s) | {safe_text(text)} | {", ".join(ids)} |')
    rows.extend(['', '요약문은 작성자의 해석입니다. 근거 ID와 시간 검사는 내용의 정확성을 자동 보증하지 않습니다.', ''])
    return '\n'.join(rows)


def fetch(value, languages):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:
        raise ValueError('Install optional fetch dependency: python -m pip install -r requirements.txt') from exc
    vid = video_id(value)
    # A specific language list means explicit preference. Without one, prefer manual.
    tracks = list(YouTubeTranscriptApi().list(vid))
    if languages:
        selected = next((t for lang in languages for t in sorted(tracks, key=lambda t: t.is_generated)
                         if t.language_code == lang), None)
    else:
        selected = next(iter(sorted(tracks, key=lambda t: t.is_generated)), None)
    if selected is None:
        raise ValueError('No matching caption track. Available: ' + ', '.join(t.language_code for t in tracks))
    fetched = selected.fetch()
    raw = {'video_id': vid, 'language_code': fetched.language_code,
           'kind': 'asr' if fetched.is_generated else 'manual', 'segments': [
               {'start_ms': round(s.start * 1000), 'duration_ms': round(s.duration * 1000), 'text': s.text}
               for s in fetched]}
    return normalize(raw, 'youtube-transcript-api')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, content):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Refuse overwrites: a failed/repeated run must not silently replace evidence.
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    fetch_p = commands.add_parser('fetch', help='Fetch existing YouTube captions')
    fetch_p.add_argument('url')
    fetch_p.add_argument('--languages', nargs='+')
    fetch_p.add_argument('--out', required=True)
    imp = commands.add_parser('import', help='Normalize timed provider JSON')
    imp.add_argument('input')
    imp.add_argument('--provider', required=True)
    imp.add_argument('--out', required=True)
    check = commands.add_parser('inspect', help='Validate timing metadata')
    check.add_argument('input')
    rend = commands.add_parser('render', help='Render agent-written Korean topic notes')
    rend.add_argument('input')
    rend.add_argument('summary')
    rend.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        if getattr(args, 'out', None) and Path(args.out).exists():
            raise ValueError('Output already exists; choose a new path')
        if args.command == 'fetch':
            result = fetch(args.url, args.languages)
        elif args.command == 'import':
            result = normalize(read_json(args.input), args.provider)
        elif args.command == 'inspect':
            print(json.dumps(inspect(read_json(args.input)), ensure_ascii=False, indent=2))
            return 0
        else:
            write(args.out, render(read_json(args.input), read_json(args.summary)))
            print('Wrote ' + args.out)
            return 0
        write(args.out, json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(inspect(result), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        # Preserve error class (e.g. IpBlocked) rather than claim there are no captions.
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
