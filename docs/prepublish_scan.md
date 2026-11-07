# Pre-publish scan (Phase 5 prep)

Run 7 Nov 2026 (overnight, automated) at commit 048924e. Nothing was published; repo visibility unchanged (private).

Command: `python3 ~/.claude/skills/hackathon/scripts/prepublish_scan.py ~/Projects/hack-future-health`

Result (verbatim):
```
scanned 38 commits, 1 real secret values
CLEAN
```
Exit code 0. The scan checks the whole history of every branch for real key values (Keychain and env files), key-shaped
strings, promo or credit codes, private workspace links, and the deny-list of names. "1 real secret values" is the number of
real key values it compared against, not a finding.

Extra checks run by hand:
- `data/` raw and interim files are not tracked (`git ls-files data` is empty); the OSHA raw file stays local, as the README says.
- No Notion, Google Drive or personal-email strings in any tracked file.
- Repo size 2.6 MB of history, 66 tracked files.

Needs Ahmed before G5 (no fix applied):
- 36 of 38 commits carry the author email `[author email, removed before publishing]`. Once the repo is public, that email is visible in the
  commit history. This is not a secret, but if he prefers the GitHub noreply address, it must be decided **before** going public
  (changing it means rewriting history and, per the playbook, recreating the remote). Otherwise no action.
- Re-run this scan right before making the repo public: commits made after 048924e are not covered.
