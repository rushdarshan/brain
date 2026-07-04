## Why

The README has a placeholder YouTube link ("add link after recording") and lacks the cinematic brag.mp4 as a visual hook. For hackathon judges scanning the repo, the README is the first impression — it needs a hero GIF from brag.mp4, a proper YouTube link for the submission video, and a cleaner separation between the two.

## What Changes

- Convert brag.mp4 to README-ready GIF and embed at top of README
- Add proper YouTube video link for submission demo
- Separate README teaser GIF from submission walkthrough video in docs
- Update demo section to reflect two-video strategy (GIF + YouTube walkthrough)

## Capabilities

### New Capabilities

- `readme-hero-gif`: Embed the cinematic brag.mp4 as a GitHub-rendered GIF teaser at the top of README

### Modified Capabilities

- *(none — no existing OpenSpec specs to modify)*

## Impact

- `README.md` — hero GIF, YouTube link, demo section restructured
- `brag.mp4` — will be converted to GIF and/or referenced directly (GitHub renders MP4 inline too)
