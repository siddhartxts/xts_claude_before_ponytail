---
name: commit-msg
description: Generate a conventional-commit message from staged changes and commit them. Use when the user says "write a commit message", "generate a commit", "commit my changes", or runs /commit-msg.
---

# Commit Message

Generate a Conventional Commits message from the staged changes and create the commit.

## Workflow

1. **Check for staged changes.** Run `git diff --staged`. If nothing is staged, **stop** and tell the user to stage their changes first (e.g. `git add ...`). Do not proceed.

2. **Read the staged diff.** Inspect the output of `git diff --staged` to understand what changed and why.

3. **Generate a commit message** in this format:

   ```
   type(scope): short subject

   - bullet of what changed
   - bullet of why
   ```

   - **type** — one of: `feat`, `fix`, `refactor`, `chore`, `docs`, `style`, `test`.
   - **scope** — optional; the area of the codebase affected.
   - **subject** — under 60 characters, imperative mood, no trailing period.
   - **body bullets** — optional but encouraged; one bullet for *what* changed, one for *why*.

4. **Commit.** Run `git commit` with the generated message.

## Notes

- Pick the `type` that best matches the dominant change in the diff.
- Keep the subject concise and specific; lead with the most important change.
