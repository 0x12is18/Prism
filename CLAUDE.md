# Prism

## Delivering generated media (video/audio/images)

When producing a media file for the user (e.g. a generated video), do not
rely on embedding it as a data URI in an Artifact page — mobile browsers
(especially iOS Safari) don't support the `download` attribute at all, and
Chrome ignores it on `data:` URIs, so those links silently fail to
download on phones.

Instead: commit the file to a `media/` directory on the current branch,
push it, and give the user the raw GitHub URL
(`https://raw.githubusercontent.com/<owner>/<repo>/<branch>/media/<file>`).
That's a real HTTP resource, so tapping it on any device (including
Android Chrome) triggers a normal file download with no JavaScript
workarounds needed.

Keep individual committed files under GitHub's 100MB hard limit.
