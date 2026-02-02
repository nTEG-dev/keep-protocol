# ClawHub Publishing Guide

How to update the `keep-protocol` skill listing on [ClawHub](https://www.clawhub.ai/skills/keep-protocol) after code changes.

## Prerequisites

- Node.js / npm (for `npx`)
- Authenticated ClawHub session (see Login below)

## Login

The CLI has a bug where it resets the registry URL on every invocation. **Always** prefix commands with the env var override:

```bash
CLAWHUB_REGISTRY=https://auth.clawdhub.com npx clawhub login
```

Complete the browser auth flow. Verify it worked:

```bash
CLAWHUB_REGISTRY=https://auth.clawdhub.com npx clawhub whoami
```

Should print `nTEG-dev`.

**Token storage:** `~/Library/Application Support/clawhub/config.json`

## Publishing a New Version

After committing and pushing code changes:

```bash
# 1. Bump version (semver)
CLAWHUB_REGISTRY=https://auth.clawdhub.com npx clawhub publish . \
  --version <NEW_VERSION> \
  --changelog "Description of changes" \
  --tags "agent-coordination,protobuf,tcp,ed25519,moltbot,openclaw,swarm,intent,signing,decentralized,latest"
```

Example:

```bash
CLAWHUB_REGISTRY=https://auth.clawdhub.com npx clawhub publish . \
  --version 1.0.2 \
  --changelog "Add relay support and improved error handling" \
  --tags "agent-coordination,protobuf,tcp,ed25519,moltbot,openclaw,swarm,intent,signing,decentralized,latest"
```

## Verify

```bash
CLAWHUB_REGISTRY=https://auth.clawdhub.com npx clawhub inspect keep-protocol --json
```

Check that `summary`, `tags`, and `latestVersion` are correct.

Or visit: https://www.clawhub.ai/skills/keep-protocol

## What Gets Published

The CLI publishes the **SKILL.md** file (and any supporting files in the directory). ClawHub reads:

- **YAML frontmatter** in `SKILL.md` → name, description, emoji, tags
- **Markdown body** → the skill instructions agents see when installed

If you change the description, emoji, or tags, update the frontmatter in `SKILL.md` first, commit, then publish.

## SKILL.md Frontmatter Reference

```yaml
---
name: keep-protocol
description: One-liner that powers search and discovery (max 1024 chars).
metadata: {"openclaw":{"emoji":"🦀","tags":["tag1","tag2"]}}
---
```

Allowed frontmatter keys: `name`, `description`, `license`, `allowed-tools`, `metadata`.

## Full Update Checklist

```
☐ Code changes committed and pushed to CLCrawford-dev/keep-protocol
☐ SKILL.md updated if description/tags/instructions changed
☐ Both repos synced (origin + nteg remote)
☐ ClawHub publish with bumped version
☐ Verified on clawhub.ai/skills/keep-protocol
```

## Push to Both Repos

The repo has two remotes:

```bash
git push origin main   # CLCrawford-dev (primary)
git push nteg main     # nTEG-dev (mirror/fork)
```

## Version History

| Version | Date       | Changes |
|---------|------------|---------|
| 1.0.0   | 2026-02-02 | Initial publish (missing description/tags) |
| 1.0.1   | 2026-02-02 | Added YAML frontmatter: description, 🦀 emoji, discovery tags |

## Troubleshooting

**`Unauthorized` on every command:**
The CLI resets the registry URL. Always use `CLAWHUB_REGISTRY=https://auth.clawdhub.com`.

**`--version must be valid semver`:**
Pass `--version X.Y.Z` explicitly. The CLI doesn't auto-detect from SKILL.md.

**Token expired:**
Re-run `CLAWHUB_REGISTRY=https://auth.clawdhub.com npx clawhub login` and complete browser flow.

---

🦀 claw-to-claw.
