# Keep-Protocol Release Workflow Template

How to structure Linear issues for any keep-protocol release. This ensures we never skip steps and can always pick up where we left off.

## Philosophy

1. **Every release is a Linear project** with step-by-step issues
2. **Issues are chained with blockers** — can't skip ahead
3. **Staging before production** — always test before going live
4. **Pick up where you left off** — find first unblocked issue

## The Three Remotes

| Remote | Repo | Purpose |
|--------|------|---------|
| `staging` | CLCrawford-dev/keep-protocol-dev | Test here first |
| `origin` | CLCrawford-dev/keep-protocol | Production |
| `nteg` | nTEG-dev/keep-protocol | Public mirror |

**Flow:** staging → origin → nteg

## Release Issue Template

For each release (e.g., v0.3.2), create these issues in order. Each blocks the next.

### Phase 1: Development

```
KP-XX: Implement [feature name]
├── Description: What's being built
├── Acceptance criteria: What "done" looks like
├── Branch: feature/kp-XX-description
└── Push to: STAGING only
```

### Phase 2: Staging Verification

```
KP-XX: Test [feature] on staging
├── Blocked by: Implementation issue
├── Test plan: Unit tests, integration tests, manual tests
├── Branch: Same feature branch on staging
└── Acceptance: All tests pass
```

```
KP-XX: Merge to staging main
├── Blocked by: Test issue
├── Actions: git merge, push staging main
└── Verification: Code on staging/main
```

### Phase 3: Production

```
KP-XX: Push to origin (production)
├── Blocked by: Staging merge
├── Actions: Merge staging/main to origin/main
└── Verification: Code on origin
```

```
KP-XX: Tag vX.Y.Z and verify CI green
├── Blocked by: Origin push
├── Actions: git tag, push tag
├── Wait: ALL CI jobs green
└── Verify: Artifacts exist (PyPI, GHCR)
```

```
KP-XX: Test vX.Y.Z in clean sandbox
├── Blocked by: CI green
├── Actions: Fresh venv, pip install, test
└── Verification: New user experience works
```

### Phase 4: Public Release

```
KP-XX: Publish vX.Y.Z to ClawHub
├── Blocked by: Sandbox test
├── Actions: clawhub publish
└── Verify: clawhub.ai listing updated
```

```
KP-XX: Sync vX.Y.Z to nteg mirror
├── Blocked by: ClawHub publish
├── Actions: git push nteg main, push tag
└── Verification: Public mirror updated
```

## Quick Reference: Issue Chain

```
Implementation
     │
     ▼
Test on Staging ←── YOU ARE HERE (find first unblocked)
     │
     ▼
Merge to Staging Main
     │
     ▼
Push to Origin
     │
     ▼
Tag + CI Green
     │
     ▼
Clean Sandbox Test
     │
     ▼
Publish ClawHub
     │
     ▼
Sync nteg Mirror
     │
     ▼
RELEASE COMPLETE
```

## How to Pick Up Where You Left Off

1. Open Linear → keep-protocol team
2. Find the active release project (e.g., "v0.3.0 — Viral Adoption")
3. Look for the **first issue that is NOT blocked**
4. That's your current step
5. Complete it, mark Done, move to next

## Creating a New Release

When starting a new version release:

### 1. Create or use existing project

```
Project: keep-protocol vX.Y.Z — [Theme]
Example: keep-protocol v0.4.0 — Public Relays
```

### 2. Create issues using this template

Copy the issue structure above. For each feature in the release:
- One implementation issue
- One test issue (blocked by implementation)
- Share the remaining release issues (merge, push, tag, sandbox, clawhub, sync)

### 3. Set up blockers

Each issue should be blocked by the previous one:
```
Implementation → Test → Merge → Push → Tag → Sandbox → ClawHub → Sync
```

### 4. Start work

Begin with the implementation issue. The chain guides you through.

## Example: v0.3.2 Release (ensure_server)

| Issue | Title | Blocked By |
|-------|-------|------------|
| KP-11 | Implement ensure_server() | — |
| KP-16 | Test on staging | KP-11 |
| KP-17 | Merge to staging main | KP-16 |
| KP-18 | Push to origin | KP-17 |
| KP-19 | Tag v0.3.2 + CI | KP-18 |
| KP-20 | Clean sandbox test | KP-19 |
| KP-21 | Publish ClawHub | KP-20 |
| KP-22 | Sync nteg mirror | KP-21 |

## Anti-Patterns (Don't Do These)

| Wrong | Right |
|-------|-------|
| Push feature branch to origin | Push to staging first |
| Skip staging tests | Always test on staging |
| Publish to ClawHub before CI green | Wait for ALL jobs green |
| Forget to sync nteg mirror | Always sync after ClawHub |
| Create issues without blockers | Chain every issue |

## Session Handoff

When ending a session, note in the session close:
- Current issue ID (e.g., "Stopped at KP-16")
- What's done, what's remaining
- Any blockers or questions

When starting a session:
1. Query last session for context
2. Check Linear for current issue
3. Continue from where you left off

---

*Template established: Feb 3, 2026*
*Based on KP-11 release workflow lessons learned*
