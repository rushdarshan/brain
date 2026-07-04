## Context

The README currently has:
- A placeholder `[🎥 Demo video](https://youtube.com)` at line 134
- `brag.mp4` (21s cinematic clip) exists at repo root but is not referenced in the README
- No distinction between the README teaser clip and the submission walkthrough video

## Goals / Non-Goals

**Goals:**
- Embed brag.mp4 as a rendered video/GIF at the top of the README for visual impact
- Replace the placeholder YouTube link with the actual submission video URL
- Structure the README so judges see: hero clip → headline → quickstart → features → criteria map

**Non-Goals:**
- No changes to the submission video content (just the link)
- No structural changes to README sections beyond the hero + demo link

## Decisions

- **GitHub renders MP4 inline** — no need to convert brag.mp4 to GIF. Just reference it with `<video>` or a markdown image link pointing to the raw GitHub URL. MP4 is smaller and higher quality than GIF.
- **Two distinct visual assets:**
  1. brag.mp4 → inline at top of README (cinematic hook, auto-loop)
  2. YouTube link → separate "Submission demo" section (walkthrough)
- **No new dependencies** — ffmpeg/gifski conversion adds friction. Direct MP4 embedding is zero-cost.

## Risks / Trade-offs

- **GitHub MP4 rendering is position-dependent** — `<video>` tag works in README but must be raw.githubusercontent.com URL. Will need to push brag.mp4 to repo first.
- **No post-submission changes** — once the form is submitted, README updates won't re-review. Must finalize before submit.
