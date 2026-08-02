# Customize with Codex

## Beginner workflow

1. Choose one folder in `apps/`.
2. Read that app's `README.md` and `app.json`.
3. Describe one small change to Codex.
4. Ask Codex to run `./scripts/check.sh`.
5. Review the changed files before installing them.
6. Reinstall and test on the Cyberdeck.
7. Commit a working version before attempting the next change.

Good first prompts:

> Change Makan Ninja so the round lasts 45 seconds. Do not change its display
> or touchscreen compatibility. Run the package checks when finished.

> Add a purple brush to Paint. Preserve the existing clear and back controls.

> Make Flappy Bird slightly easier for beginners by changing only gravity and
> pipe spacing. Explain which values you changed.

To start an original project, copy `templates/blank-game` into `apps/`, rename
the folder and update `app.json`. Keep changes small enough to test after each
step.

Do not ask Codex to store passwords, Wi-Fi credentials, SSH keys, private
journal entries or copyrighted ebooks in Git.
