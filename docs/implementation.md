# Implementation and verification plan

## Design
Provide a portable agent skill for source-backed Korean topic summaries of YouTube videos. A small Python CLI fetches or imports captions, checks timing, and renders agent-written summaries with links derived from actual cue IDs. The agent performs semantic summarization; this is not an autonomous translation model or video player.

Existing captions avoid downloading media or running speech models. Support optional youtube-transcript-api for standalone retrieval and a provider-neutral import path for connected tools. Preserve automatic-caption overlap; never infer missing timestamps from a title or word count. Keep raw third-party transcripts outside Git.

## Steps
- [x] Write regression tests for ID parsing, timing validation, provider errors, overlap, source references and rendering; run baseline.
- [x] Implement fetch/import/inspect/render CLI and run the synthetic suite.
- [x] Document skill, installation, limitations and license; validate SKILL.md.
- [x] Run the real video through import, inspection and summary rendering; attempt standalone fetch separately.
- [x] Independently review code and skill behavior, address findings and recheck the fixes.

Publication gate: after these checks, publish the new repository and verify the remote tree and CI results.

## Review focus
Untrusted URLs, nonfinite or boolean timestamps, out-of-order cues, missing/duplicate evidence IDs, error payloads confused with empty captions, rolling-caption overlaps, accidental transcript publication.

## Baseline
Before skill creation, an independent agent given synthetic overlapping ASR cues correctly distinguished timing metadata from audio verification and correctly rejected a rate-limit response as transcript evidence. It rendered each cue separately despite a request for topic summary. Guidance will clarify topic grouping; no new general prohibition is inferred from this single test.
