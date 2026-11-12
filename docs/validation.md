# Validation record

Date: 2026-11-12 (Asia/Seoul).

## Live source

- Video: [MOONBOY — HOW TO HYPERPOP](https://www.youtube.com/watch?v=Y4Elqi6U8LM).
- Track: English automatic captions (`asr`).
- Connected path: Firecrawl `youtube-com/videos/video_transcript`, imported through the CLI.
- Standalone path: `youtube-transcript-api` 1.2.5, fetched through the CLI on Windows.
- Both paths returned identical normalized segment arrays: 255 cues, first start 0 ms, final end 681800 ms.
- 189 overlapping cues were preserved; largest uncovered interval between cues was 16975 ms. Overlap is valid rolling-caption behavior, and a gap alone does not establish missing speech.
- The agent-authored Korean summary contains 12 topics. Its evidence references account for all 255 cue IDs. Each rendered timestamp comes from referenced captions.
- Raw captions and the generated case output remain local and are excluded from this repository. This repository does not license or redistribute the video's transcript.

## What this proves

The fetch/import/inspect/render pipeline worked on the specified video in this environment. The two retrieval paths agree on timing and text. This does not prove that the underlying ASR is accurate, establish word-level audio alignment, or guarantee that future YouTube requests will succeed. No video/audio alignment verification was performed. Unclear specialist terms were marked in the Korean notes; screen-only settings were not inferred.

## Automated and behavioral checks

The synthetic test suite covers URL host validation, timing fields, invalid and missing captions, mismatched counts, provider errors, chronological ordering, overlaps, duplicate and missing source IDs, summary-only rendering, long timestamps, end-to-end CLI output, and refusal to overwrite an existing file.

Run it without network or optional packages:

```sh
python -m unittest discover -s tests -v
```

The Codex skill-creator frontmatter validator was also run successfully. Schema validation is not semantic quality validation.

A baseline agent handled overlap and rate-limit errors honestly but emitted cue-by-cue notes when topic grouping was requested. With the skill, independent forward-testing grouped the two related instructions into one topic, preserved the music-only section and distinguished metadata checks from audio alignment.

Independent code review identified Markdown image injection through a provider-supplied title. A failing regression test reproduced it; Markdown escaping fixed it. Canonical video and cue IDs are also validated so evidence links and ID cells cannot contain arbitrary markup. The final local suite contains 17 passing tests, including CLI round trips and these regressions.

The independent reviewer reran all 17 tests and confirmed the targeted fixes.
