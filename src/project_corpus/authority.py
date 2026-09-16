from __future__ import annotations

from dataclasses import dataclass

from .policy import ProjectPolicy
from .trust import TrustGrant


RUNTIME_HARD_LIMITS = frozenset({
    "corpus.read", "corpus.stat", "corpus.validate", "migration.plan",
    "migration.apply", "state.update", "task.create", "report.create",
    "audit.read", "mcp.stdio", "git.status", "git.diff",
})
DIAGNOSTIC_CAPABILITIES = frozenset({"corpus.validate"})
READ_ONLY_CAPABILITIES = frozenset({
    "corpus.read", "corpus.stat", "corpus.validate", "migration.plan",
    "audit.read", "git.status", "git.diff",
})


@dataclass(frozen=True)
class AuthorityDecision:
    effective: frozenset[str]
    denied: frozenset[str]
    policy_drift: bool
    root_identity_match: bool
    transport_allowed: bool
    reasons: tuple[str, ...]

    def permits(self, capability: str) -> bool:
        return capability in self.effective


def evaluate_authority(
    *,
    trust: TrustGrant,
    policy: ProjectPolicy,
    session_capabilities: set[str] | frozenset[str],
    observed_root_identity: str,
    transport: str,
    runtime_hard_limits: frozenset[str] = RUNTIME_HARD_LIMITS,
) -> AuthorityDecision:
    requested = frozenset(session_capabilities)
    reasons: list[str] = []
    policy_drift = trust.policy_sha256 != policy.digest
    root_match = trust.root_identity == observed_root_identity
    transport_allowed = transport in trust.transports
    if trust.project_id != policy.project_id:
        return AuthorityDecision(
            frozenset(), requested, policy_drift, root_match,
            transport_allowed, ("PROJECT_ID_MISMATCH",),
        )

    effective = (
        runtime_hard_limits & trust.capability_ceiling & policy.capabilities & requested
    )
    if policy_drift:
        effective &= READ_ONLY_CAPABILITIES
        reasons.append("POLICY_DRIFT")
    if not root_match:
        effective &= DIAGNOSTIC_CAPABILITIES
        reasons.append("ROOT_IDENTITY_MISMATCH")
    if not transport_allowed:
        effective = frozenset()
        reasons.append("TRANSPORT_NOT_GRANTED")
    if requested - runtime_hard_limits:
        reasons.append("RUNTIME_HARD_LIMIT")
    if requested - trust.capability_ceiling:
        reasons.append("OWNER_GRANT_LIMIT")
    if requested - policy.capabilities:
        reasons.append("PROJECT_POLICY_LIMIT")
    return AuthorityDecision(
        frozenset(effective), frozenset(requested - effective), policy_drift,
        root_match, transport_allowed, tuple(dict.fromkeys(reasons)),
    )
