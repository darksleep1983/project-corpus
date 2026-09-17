# GitHub governance plan

**Status: recommendation only. No GitHub settings are changed by this file.**

## Current observation

At review time, `main` is the default branch; Issues are enabled; Discussions,
Pages, environments, and rulesets are absent. Anonymous API access cannot read
branch protection or Actions-permission settings, so the owner should verify
those settings in the repository UI before applying a ruleset.

Suggested issue labels to create only when the owner enables the new forms:
`bug`, `enhancement`, `documentation`, and `security`. The security label is
for non-sensitive documentation references, never vulnerability disclosure.

## A. Solo maintainer

Use a `main` ruleset with these settings:

- Target: default branch `main`.
- Block force pushes: enabled.
- Block branch deletion: enabled.
- Require pull request before merging: enabled for external contributors; allow
  the repository owner to bypass after reviewing their own change.
- Required status checks: `test (ubuntu-latest, 3.11)`,
  `test (ubuntu-latest, 3.12)`, `test (windows-latest, 3.11)`,
  `test (windows-latest, 3.12)`, `test (macos-latest, 3.11)`, and
  `test (macos-latest, 3.12)`.
- Require the branch to be up to date before merge: enabled when status checks
  are required.
- Required approvals: zero. Do not require a second reviewer for a solo owner.
- Restrict bypass: repository owner only; audit bypasses.

## B. Future multi-maintainer

Start from the solo model, then:

- Require one approving review for ordinary pull requests.
- Dismiss stale approvals when new commits are pushed.
- Require Code Owner review for Runtime, Protocol, workflows, and security docs
  after a CODEOWNERS policy is deliberately established.
- Keep repository administrators as the only bypass actors, or remove bypass
  entirely once release ownership is shared and documented.
- Consider a separate protected release branch only when there is a real release
  maintenance need.

## Merge strategy

- Normal documentation and small feature pull requests: squash merge for a
  concise `main` history.
- Large architectural branches: normal merge commit to preserve the reviewed
  sequence of logical commits and qualification evidence.
- Release branches: normal merge commit when the branch represents a frozen,
  auditable release preparation sequence; never rewrite released history.

Disable rebase merge unless the maintainer later adopts a documented reason for
it. Do not delete feature branches automatically until the owner has decided
whether their evidence history remains useful.
