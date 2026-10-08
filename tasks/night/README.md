# Night tasks

Work that Cursor background agents do while Teddy sleeps. Only work that **verifies itself** (compiles, tests pass) belongs here. Nothing that needs hardware, measurements or CAD numbers.

## Rules for the agent
- One task file = one agent = one branch `night/<task-id>`. Never work on `dev` or `main` directly.
- Read `.cursor/rules/ar-mini.mdc` first. Then the task file. Then the repo files it names.
- Finish with a **pull request to `dev`** (never merge it). PR description: what was done, what was not, how to verify, open questions.
- Stop when the definition of done is met, or after 3 failed attempts at the same step. Write what blocked you in the PR; do not loop.
- Do not invent pins, thresholds or dimensions. Every physical number lives in a config struct or header with a `// SOURCE:` or `// VERIFY:` comment.
- `bash scripts/check.sh` must pass before the PR.

## Rules for Teddy (morning, 20 min)
1. GitHub → Pull requests. CI green or red?
2. Read the PR description first, then the diff. Questions → paste the diff into the Software Project.
3. Merge into `dev` only what you understand. Otherwise comment what to change and re-run the agent on the same branch.
4. Anything that touches hardware is still a loop (L###) for you, with the tracker and a photo.

## File format
See `_template.md`. Task id: `YYYY-MM-DD_Tn_short-name`.
