# Upstream

This skill is **vendored** from:

- https://github.com/vimkim/dotfiles/tree/main/dot_claude/skills/grill-and-revise

It is reproduced here so that other CUBRID skills in this repo (e.g. `cubrid-grill-and-implement`, `cubrid-loop-pr`) can rely on `/grill-and-revise` being available on any machine that has installed `my-cubrid-skills` — without requiring the user to also install the maintainer's personal dotfiles.

## Sync from upstream

If the upstream copy changes, refresh this directory verbatim and reinstall:

```bash
# from the repo root
rm -rf grill-and-revise
curl -sSL https://github.com/vimkim/dotfiles/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=3 \
      -C grill-and-revise \
      dotfiles-main/dot_claude/skills/grill-and-revise
just install
git add grill-and-revise && git commit -m "chore: sync grill-and-revise from upstream dotfiles"
```

Do not modify `SKILL.md` or `references/` in place — keep this directory diff-clean against upstream so syncs stay trivial.
