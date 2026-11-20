# Needs image: do not merge

`/guides/road-test-automatic-fails/` is ready except for its thumbnail.

## Bank file

- Source, still missing: `/workspace/image-bank/which/learner-driver-wheel.png`
- Copy it to: `assets/images/learner-driver-wheel.png`
- Scene already assigned: a learner driver's hands on a steering wheel, handbook on the passenger seat
- Use: one news-photo thumbnail on the guide. Caption it in plain text as an AI-generated image and link the image to `/image-policy/`.
- Do not generate a replacement. Do not use Higgsfield.

## When the file exists

1. Add the image and the caption link on the guide.
2. Update `/image-policy/` so it no longer says this version has no photographs and no AI-generated images.
3. Re-run `python3 _build/check.py` and `python3 _build/legal_gate.py check --no-queue`.
4. Only then mark this pull request ready and merge it.

PR #4 is a different page and stays open for its own missing thumbnail.
