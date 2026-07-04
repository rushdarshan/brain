## ADDED Requirements

### Requirement: README embeds brag.mp4 as hero video
The README SHALL embed brag.mp4 at the top (between the subtitle and the architecture section) using a `<video>` tag or GitHub-flavored markdown that renders inline. The video SHALL autoplay, loop, and be muted. The source SHALL reference the raw GitHub URL so it renders on the repo page.

#### Scenario: Embed renders on GitHub repo page
- **WHEN** a visitor opens the GitHub repo page
- **THEN** the brag.mp4 video plays inline below the project subtitle, showing the 21-second cinematic clip

### Requirement: README has real YouTube submission link
The README SHALL replace the placeholder `https://youtube.com` link with the actual YouTube URL of the submission walkthrough video.

#### Scenario: Demo link is clickable
- **WHEN** a judge clicks the demo video link in the README
- **THEN** it navigates to the actual YouTube submission video

### Requirement: README distinguishes teaser from walkthrough
The README SHALL clearly separate the hero MP4 teaser from the submission demo video section, so visitors understand one is a cinematic hook and the other is the full walkthrough.

#### Scenario: Two distinct video sections visible
- **WHEN** a visitor reads the README
- **THEN** they see an inline hero MP4 at the top AND a separate "Submission demo" section with the YouTube link
