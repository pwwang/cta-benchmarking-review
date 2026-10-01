"""Minimal aggregator core used by the analysis scripts in ``analysis/``.

This is **not** a general-purpose library. It is the smallest set of symbols the re-analysis
scripts in this package actually call, extracted from the authors' agreement-based aggregator --
the aggregation method evaluated in the review's re-analysis -- so that the deposit is
self-contained:

    Vocabulary         raw label string -> integer code
    fit                the failure-state EM fit, with every helper it calls
    membership_matrix  the (K x G) group-membership matrix

Names, signatures and logic are unchanged from the original implementation: only the modules it
lived in (label vocabulary / emission tables / model / resource graph) were merged into this one
file, and everything the analysis does not call was dropped. Nothing here is imported by the
audit scripts or the figure scripts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # annotation-only import: `membership_matrix` takes a polars DataFrame
    import polars as pl

EPS = 1e-12


# ---------------------------------------------------------------------------
# label vocabulary: truth types plus ABSTAIN / OTHER sentinel categories
# ---------------------------------------------------------------------------

MISSING = -1
ABSTAIN = 0
_ABSTAIN_STRINGS = {"unknown", "<unknown>"}


class Vocabulary:
    """Maps raw label strings to integer codes.

    Codes: -1 missing, 0 abstain, 1..T types (sorted), T+1 other.
    """

    def __init__(self, types: list[str]):
        self.types: list[str] = sorted(types)
        self.T = len(self.types)
        self.type_codes = {t: i + 1 for i, t in enumerate(self.types)}
        self.code_to_type = {i + 1: t for i, t in enumerate(self.types)}

    @property
    def OTHER(self) -> int:
        return self.T + 1

    def code(self, raw) -> int:
        if raw is None:
            return MISSING
        s = str(raw).strip()
        if s.lower() in _ABSTAIN_STRINGS:
            return ABSTAIN
        return self.type_codes.get(s, self.OTHER)


# ---------------------------------------------------------------------------
# emission probability tables
# ---------------------------------------------------------------------------

def normal_log_table(a: np.ndarray, s: np.ndarray, o: np.ndarray, T: int) -> np.ndarray:
    """log P(y | z=t, normal) as a (K, T, T+2) array; column index = code."""
    K = a.size
    tbl = np.full((K, T, T + 2), -np.inf)
    for k in range(K):
        commit = max(1.0 - s[k] - o[k], EPS)
        tbl[k, :, 0] = np.log(max(s[k], EPS))          # ABSTAIN
        tbl[k, :, T + 1] = np.log(max(o[k], EPS))      # OTHER
        for t in range(T):
            tbl[k, t, t + 1] = np.log(commit * max(a[k], EPS))
            for j in range(1, T + 1):
                if j != t + 1:
                    tbl[k, t, j] = np.log(commit * max(1.0 - a[k], EPS) / (T - 1))
    return tbl


def state_log_tables(p, members: np.ndarray, T: int) -> np.ndarray:
    """(G+1, K, T, T+2) log tables; state 0 = normal, state g+1 = group g failed."""
    G = p.rho.size
    base = normal_log_table(p.a, p.s, p.o, T)
    tables = np.tile(base, (G + 1, 1, 1, 1))
    diag = np.arange(T)
    blocked = np.zeros((T, T + 2), dtype=bool)
    blocked[diag, diag + 1] = True              # column of the *correct* type for each truth t
    for g in range(G):
        members_g = members[:, g]
        # A failed resource does not track the truth, so it must not emit the correct type more
        # confidently than chance (1/T): p.m[g]'s correct-type column is capped there and the
        # removed mass goes to the other columns in proportion to their existing share. The cap
        # is what stops a failure state from reproducing healthy behaviour, which would make
        # "failure" a free substitute for "correct": a group that never fails could then be
        # explained into a failure state at no likelihood cost. Measured on the negative control
        # (independent annotators, no failure anywhere): with p.m[g] unconstrained the fit blamed
        # each group on exactly the clusters whose truth equalled that group's emission peak, and
        # lost 4 accuracy points. Wrong-type mass is untouched (only the correct-type column is
        # capped), so a failed resource keeps its own signature -- the thing the model exists to
        # find (e.g. everything -> one wrong type, or everything -> ABSTAIN/OTHER).
        prob = np.tile(np.asarray(p.m[g], dtype=float), (T, 1))     # (T, T+2), row = truth t
        excess = np.maximum(prob[diag, diag + 1] - 1.0 / T, 0.0)
        prob[diag, diag + 1] -= excess
        share = prob.copy()
        share[diag, diag + 1] = 0.0                                 # never back onto the truth
        tot = share.sum(axis=1, keepdims=True)
        # a resource whose whole signature is "always type X" has nothing but the correct column
        # on truth-X clusters; spread the excess uniformly over what it may still emit, so the
        # row stays a distribution instead of dividing by zero
        deg = tot[:, 0] <= 0.0
        if deg.any():
            share[deg] = (~blocked[deg]).astype(float)
            tot = share.sum(axis=1, keepdims=True)
        mlog = np.log(np.maximum(prob + excess[:, None] * share / tot, EPS))
        tables[g + 1, members_g, :, :] = mlog[None, :, :]
    return tables


# ---------------------------------------------------------------------------
# the EM fit: dependency-aware Dawid-Skene with per-cluster failure states
# ---------------------------------------------------------------------------

# Dirichlet prior over the G+1 cluster states, in units of *clusters* of evidence (see m_step's
# rho): the no-failure state gets RHO_PRIOR_CLUSTERS, and the G failure states share
# RHO_FAIL_CLUSTERS between them. The split matters: the failure block's prior weight must not
# grow with G, or on a grid with many groups and few clusters (pbmc3k's `base_source,family` has
# G=21, C=9) the prior alone forces ~1 cluster's worth of failure mass -- measured: rho summed to
# 0.96 and the fit's loglik was 120k nats worse than the Dawid-Skene baseline it nests.
RHO_PRIOR_CLUSTERS = 1.0
RHO_FAIL_CLUSTERS = 0.1
# Initial total failure mass, spread evenly over the G groups. It is a *total*, not a per-group
# rate, for the same reason as RHO_FAIL_CLUSTERS: 0.05 per group is a valid starting point at
# G=2 but sums to 1.05 at G=21, and `1 - rho.sum()` then goes negative, so `log_prior` hands the
# no-failure state log(1e-12) -- the fit starts with the healthy state banned and every cluster
# assigned to a failure. Measured: that alone drove `base_source,family` to a loglik 120k nats
# below the Dawid-Skene baseline it nests, on a path EM never came back from.
RHO_INIT_TOTAL = 0.1


@dataclass
class Params:
    a: np.ndarray                 # (K,) accuracy when committed & normal
    s: np.ndarray                 # (K,) abstain rate (normal state)
    o: np.ndarray                 # (K,) other/junk rate (normal state)
    rho: np.ndarray               # (G,) failure priors
    m: np.ndarray                 # (G, T+2) failed-state emission


@dataclass
class FitResult:
    params: Params
    q: np.ndarray                 # (C, G+1) cluster state posteriors
    gamma: np.ndarray             # (N, T) reconciled per-unit posteriors
    loglik: list[float] = field(default_factory=list)
    n_iter: int = 0
    # True when `fit` returned the Dawid-Skene fallback instead of a free fit with failure states
    # (see `fit`'s contract). `rho` is all zeros and `q[:, 1:]` all zeros then, so the shapes are
    # the free fit's but the failure columns carry no information: consumers that would report a
    # number derived from them (a suspect group, a failure mass, a rho hurdle) must report "no
    # failure states" instead. False on a plain G=0 DS fit, which never claimed failure states.
    no_failure_states: bool = False


def logsumexp(x: np.ndarray, axis: int) -> np.ndarray:
    m = np.max(x, axis=axis, keepdims=True)
    out = m + np.log(np.sum(np.exp(x - m), axis=axis, keepdims=True))
    return np.squeeze(out, axis=axis)


def softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x))
    return e / e.sum()


def check_weights(W: np.ndarray | None, y: np.ndarray) -> None:
    """Validate a vote-weight matrix against the vote matrix it weights.

    A weight matrix of the wrong shape silently broadcasts (or raises deep inside the hot loop),
    and a negative one maximises something that is not a likelihood -- both are caught here rather
    than in a fit that returns a plausible-looking trace.
    """
    if W is None:
        return
    W = np.asarray(W)
    if W.ndim != 2 or W.shape != y.shape:
        raise ValueError(f"W must be (N, K) = {y.shape} like y, got {W.shape}")
    if not np.all(np.isfinite(W)) or np.any(W < 0):
        raise ValueError("W must be finite and non-negative")


def majority_votes(y: np.ndarray, T: int, W: np.ndarray | None = None) -> np.ndarray:
    """(N,) plurality vote over each unit's committed codes; 0 where no arm committed.

    Codes are 0 = ABSTAIN, 1..T = types, T+1 = OTHER, -1 = MISSING (a missing vote is no vote).
    `W` (N, K, optional) weights arm k's vote at unit i, so the plurality is the one a roster of
    equally weighted opinions gives instead of one that counts a cluster-level arm's single call
    once per cell of its cluster. `W=None` is the unweighted plurality, bit-for-bit.
    """
    N = y.shape[0]
    committed = (y > 0) & (y != T + 1)
    maj = np.zeros(N, dtype=int)
    for i in range(N):
        vals = y[i][committed[i]]
        if vals.size:
            if W is None:
                maj[i] = np.bincount(vals, minlength=T + 2).argmax()
            else:
                maj[i] = np.bincount(vals, weights=W[i][committed[i]], minlength=T + 2).argmax()
    return maj


def init_params(y: np.ndarray, T: int, G: int, W: np.ndarray | None = None) -> Params:
    """Starting point for EM, from the plurality majority vote (`majority_votes`).

    `W` weights that majority vote as well. Without it the majority counts a cluster-level arm's
    one call per cluster `n_c` times and each byte-identical copy of a vote as its own witness, so
    EM starts from the correlated majority the weights exist to correct; with it EM starts from
    the majority of the weighted roster. `W=None` stays bit-identical to the unweighted path.
    """
    N, K = y.shape
    committed = (y > 0) & (y != T + 1)
    maj = majority_votes(y, T, W)
    a = np.empty(K)
    for k in range(K):
        sel = committed[:, k] & (maj > 0)
        a[k] = (y[sel, k] == maj[sel]).mean() if sel.any() else 0.5
    s = np.clip((y == 0).mean(axis=0), 1e-3, 0.999)
    o = np.clip((y == T + 1).mean(axis=0), 1e-6, 0.5)
    return Params(
        a=np.clip(a, 0.05, 0.99),
        s=s,
        o=o,
        rho=np.full(G, RHO_INIT_TOTAL / max(G, 1)),
        m=np.full((G, T + 2), 1.0 / (T + 2)),
    )


def e_step(y, clusters, tables, rho, T, W=None):
    """Return (q (C,G+1), gamma (N,T), gamma_state (N,T,G+1), loglik).

    `W` (N, K) is a per-(unit, arm) non-negative vote weight, `None` = all ones. With `W` the
    returned `loglik` is the *weighted* log-likelihood ``sum_{i,k} W[i,k] log P(y_i | state)``;
    with `None` it is the plain one. `m_step` must maximise whichever objective is passed here, or
    EM walks downhill.

    Orientation (checked on a tiny array, not assumed): `contrib` below is (K, n, T) -- arm x
    unit-in-cluster x truth, because the two advanced indices (arm, code) are separated by the
    truth slice, so their broadcast shape (K, n) leads. The cluster block of the weights is
    therefore `W[idx].T[:, :, None]` = (K, n, 1) and broadcasts along the truth axis.
    """
    N, K = y.shape
    S = rho.size + 1
    log_prior = np.log(np.concatenate([[max(1.0 - rho.sum(), EPS)], np.maximum(rho, EPS)]))
    gamma = np.zeros((N, T))
    gamma_state = np.zeros((N, T, S))
    q = np.zeros((int(clusters.max()) + 1, S))
    loglik = 0.0
    logT = np.log(T)
    for c in np.unique(clusters):
        idx = np.where(clusters == c)[0]
        wc = None if W is None else W[idx]            # (n, K) weight block of this cluster
        yc = y[idx]                                   # (n, K)
        ll = np.zeros((idx.size, T, S))
        present = (yc >= 0).T                             # (K, n) False where the vote is MISSING
        codes = np.maximum(yc, 0).T                       # (K, n) MISSING (-1) must not wrap to the last
        for s_i in range(S):                              # column, which is OTHER
            # sum_k W_ik * log P(y_ik | t, s_i): index annotator + emitted code together,
            # then reduce over annotators -> (n, T). (The plan's
            # `tables[s_i][:, :, yc.T].sum(axis=0).T` gives (n, K, T); the plan's
            # own note asked for this line to be verified on a tiny array.)
            # A missing vote is *no* vote: it contributes nothing to the sum, rather than
            # whatever the code it wrapped to would have contributed.
            contrib = tables[s_i][np.arange(K)[:, None], :, codes]
            contrib = contrib * present[:, :, None]
            if wc is not None:
                # (K, n, 1): weight arm k's vote at unit i, broadcast over the truth axis
                contrib = contrib * wc.T[:, :, None]
            ll[:, :, s_i] = contrib.sum(axis=0)
        lz = logsumexp(ll - logT, axis=1)             # (n, S)
        llc = log_prior + lz.sum(axis=0)              # (S,)
        qc = softmax(llc)
        q[c] = qc
        loglik += float(logsumexp(llc, axis=0))
        gs = np.exp(ll - logT - lz[:, None, :])       # (n, T, S)
        gamma_state[idx] = gs
        gamma[idx] = gs @ qc
    return q, gamma, gamma_state, loglik


def m_step(y, clusters, q, gamma_state, members, T, W=None):
    """One M-step. `W` (N, K) is the same vote weight `e_step` scored the likelihood with.

    With `W` every statistic that counts arm k's emission at unit i carries W[i,k], so this step
    still maximises the weighted objective `e_step` reports. Weighting only some statistics (the
    classic failure) maximises a different function and EM walks downhill, which `fit` reports as
    a refused step -- a silently truncated run rather than an error, so it must not happen.
    `W=None` reproduces the unweighted statistics exactly.
    """
    N, K = y.shape
    G = members.shape[1]
    q_c = q[clusters]                       # (N, G+1)
    committed = (y > 0) & (y != T + 1)
    # a, s and o are the *normal* table's parameters, but that table is not only state 0's:
    # `state_log_tables` starts every failure state from the normal table and overwrites only the
    # failing group's *member* arms, so arm k emits with a/s/o under every failure state of a
    # group k is not in. Their sufficient statistics must carry those responsibilities too.
    # Weighting them by q0 alone (the no-failure posterior) maximises a different function than the
    # one e_step scores, so the M-step is not a maximiser and EM walks downhill: (measured) the
    # held-out k=12 fit dropped 393 nats on its first step and converged 1107 nats *below* the DS
    # fit it nests; the vote-derived k=12 partition dropped 2.6 nats.
    #   u[i,k,t] = P(truth = t and arm k emits with the normal table | unit i)
    gsq = gamma_state * q_c[:, None, :]             # (N, T, G+1) joint over (truth t, state s)
    allow = np.ones((G + 1, K))
    for g in range(G):
        allow[g + 1, members[:, g]] = 0.0           # state g+1 scores member arms with m_g
    u = np.einsum("its,sk->ikt", gsq, allow)        # (N, K, T)
    if W is not None:
        # Every statistic from here down counts arm k's emission at unit i, so one multiplication
        # weights them all: wn = u.sum(t) (hence the s/o denominator n_present and the s/o
        # numerators) and, through `hit`/`den`, the a numerator and denominator.
        u = u * W[:, :, None]
    wn = u.sum(axis=2)                              # (N, K) weight on arm k's normal table
    # s and o are per-arm distributions over the codes that arm actually emitted, so the
    # denominator is the arm's *present* votes only. e_step's fix made a MISSING vote (-1)
    # contribute nothing to the likelihood; counting it here anyway would inflate the denominator
    # and bias s and o toward zero in proportion to the arm's missingness -- a suboptimal M-step,
    # and (measured) the thing that lets EM walk 40k nats downhill at G=21.
    present = (y >= 0)
    n_present = (wn * present).sum(axis=0)          # (K,)
    s = ((y == 0) * wn).sum(axis=0) / np.maximum(n_present, EPS)
    o = ((y == T + 1) * wn).sum(axis=0) / np.maximum(n_present, EPS)
    # a: correct-vs-wrong split of the mass that was committed, with each vote scored under the
    # truth it was committed *to* -- y_ik = t+1 contributes at t of u.
    hit = np.take_along_axis(u, np.clip(y - 1, 0, T - 1)[:, :, None], axis=2)[:, :, 0]  # (N, K)
    den = (wn * committed).sum(axis=0)
    num = (hit * committed).sum(axis=0)
    a = np.where(den > EPS, num / np.maximum(den, EPS), 0.5)
    # Dirichlet posterior mean over the S = G+1 cluster states, with a prior worth
    # RHO_PRIOR_CLUSTERS clusters of evidence on "no failure" and RHO_FAIL_CLUSTERS (shared) on
    # "some failure":
    #     rho_g = (sum_c q[c,g+1] + f) / (C + k*C + G*f),   f = RHO_FAIL_CLUSTERS * C / G
    # Why not `q[:, 1:].mean(axis=0)` clipped to [1e-3, 0.95]: that was a one-way door. A state
    # whose posterior support fell to the floor could never be re-estimated upward, because the
    # evidence that would raise it is exactly the evidence the floor had already suppressed. The
    # prior leaves every state a floor of RHO_FAIL_CLUSTERS/(G*(1+k+f)) that no amount of
    # non-support can push below, the estimate is soft (no clip), it sums to 1 by construction,
    # and it is bounded above by (C + f)/(C(1+k+f)) < 1 -- so rho cannot saturate either.
    if G:
        C = q.shape[0]
        f = RHO_FAIL_CLUSTERS * C / G
        rho = (q[:, 1:].sum(axis=0) + f) / (C * (1.0 + RHO_PRIOR_CLUSTERS) + G * f)
    else:
        rho = np.zeros(0)
    # Global code prior pi over the T+2 emission columns: the pooled empirical distribution of
    # every non-MISSING vote in the data. (y = -1 is MISSING, which is not an emission and is
    # dropped; `codes = y + 1` shifts the remaining codes onto 1..T+2 for bincount.)
    codes = y + 1
    glob = np.bincount(codes.ravel(), minlength=T + 3)[1:].astype(float)
    pi = glob / max(glob.sum(), 1.0)
    # m_g is the normalised vote histogram of group g's members over the clusters that blame it.
    # Two things it must not do. (1) Fall to all-zero when the state's support vanishes: that is
    # not a distribution, and `state_log_tables` reads it as "every code has probability EPS", so
    # the state scores ~K*log(EPS) worse than any rival and can never win support back -- a
    # one-way door. (2) Lose its *shape* when support is merely small: `num / max(num.sum(), EPS)`
    # did that too, because once num.sum() drops below EPS the numerator is flattened along with
    # the denominator. Normalising by the true sum is scale-free, so a state with very little
    # support still keeps a sharp emission and can recover. Only a state with no support at all
    # falls back -- to the global code prior pi, a proper distribution tied to the data.
    m = np.zeros((G, T + 2))
    for g in range(G):
        ks = np.where(members[:, g])[0]
        num = np.zeros(T + 2)
        for c in np.unique(clusters):
            idx = np.where(clusters == c)[0]
            w = q[c, g + 1]
            sub = y[np.ix_(idx, ks)]
            if W is None:
                for j in range(T + 2):
                    num[j] += w * float((sub == j).sum())
            else:
                # Each observation in this histogram is arm k's emission at unit i, so it carries
                # the same W[i,k] as the a/s/o statistics above; the normaliser is then the
                # weighted total, which is what keeps one cluster-level call worth one observation.
                ww = W[np.ix_(idx, ks)]
                for j in range(T + 2):
                    num[j] += w * float(((sub == j) * ww).sum())
        # The histogram MLE puts exactly 0 on a code the group never emitted (or on every code, if
        # the group has no support at all), but the emission table e_step scores is
        # log(max(m, EPS)) -- so a raw histogram means the table being scored is not the one this
        # step maximised, and the M-step loses its monotonicity (measured: the G=21 fit walked 40k
        # nats downhill in a single step). Flooring the *normalised* histogram at EPS puts both on
        # the same strictly-positive simplex and rescales nothing: every value is exactly what
        # e_step already saw, so the fit is untouched and only the bookkeeping is fixed. (Adding
        # EPS to the counts instead would be scale-dependent: while a group's support is still
        # tiny, EPS/sum is a *large* smoothing that flattens the emission and costs the recovery --
        # measured: it broke scenario C1.) `pi` stays as the fallback for a group with no data at
        # all, where the objective is flat in m and any distribution is a maximiser.
        tot = num.sum()
        m[g] = np.maximum(num / tot if tot > 0 else pi, EPS)
    return Params(
        a=np.clip(a, 1e-3, 0.999),
        s=np.clip(s, 1e-3, 0.999),
        o=np.clip(o, 1e-6, 0.5),
        rho=rho,
        m=m,
    )


def cluster_seed_m(y, clusters, members, T, c) -> np.ndarray:
    """(G, T+2) emission seed: every group's vote histogram *inside cluster c*.

    The plateau escape (see `fit`). `m_g` is a single emission shared by every cluster that blames
    group g, and `m_step` estimates it from the q-weighted votes only -- so at a solution that
    blames one cluster it *is* that cluster's histogram, and no second cluster can ever prefer it.
    Seeding `m_g` from cluster c's own votes gives the first E-step a localised emission to score,
    which is the only way a state stuck at one-cluster support can be re-shaped. MISSING (-1) is
    not an emission and is dropped, as in `m_step`.

    Deliberately *unweighted*: this is a searching heuristic (a starting point for a restart), not
    a sufficient statistic of the objective, and `fit` keeps only a restart that raises the
    weighted log-likelihood -- so an unweighted seed can cost a wasted restart but can never move
    the number the fit reports.
    """
    idx = np.where(clusters == c)[0]
    m = np.empty((members.shape[1], T + 2))
    for g in range(members.shape[1]):
        sub = y[np.ix_(idx, np.where(members[:, g])[0])]
        num = np.bincount((sub + 1).ravel(), minlength=T + 3)[1:].astype(float)
        tot = num.sum()
        m[g] = np.maximum(num / tot if tot > 0 else np.full(T + 2, 1.0 / (T + 2)), EPS)
    return m


def _em(y, clusters, members, T, p, max_iter, tol, W=None):
    """One monotone EM run from `p`, maximising the objective `e_step` scores under weight `W`.

    Returns (p, q, gamma, trace).
    """
    trace: list[float] = []
    it = 0
    for it in range(max_iter):
        tables = state_log_tables(p, members, T)
        q, gamma, gamma_state, ll = e_step(y, clusters, tables, p.rho, T, W)
        trace.append(ll)
        p_new = m_step(y, clusters, q, gamma_state, members, T, W)
        # Score the candidate on the *same* objective e_step reports before accepting it; a step
        # that does not increase it is refused and the fit stops on the previous parameters. This
        # is the invariant itself, not a heuristic: the M-step is not an exact maximiser
        # everywhere (rho is a Dirichlet-floored posterior mean, the cap in `state_log_tables`
        # redistributes m's excess, a/s/o are clipped), so refusals are possible even with the
        # sufficient statistics above fixed.
        q_new, gamma_new, gs_new, ll_new = e_step(
            y, clusters, state_log_tables(p_new, members, T), p_new.rho, T, W)
        if ll_new < ll:
            break
        p, q, gamma, gamma_state = p_new, q_new, gamma_new, gs_new
        if it > 0 and abs(trace[-1] - trace[-2]) < tol * (1.0 + abs(trace[-1])):
            break
    # Re-score the returned parameters exactly as before, so every number this function reports
    # (and `n_iter`, and the trace's length) is unchanged wherever no step was refused.
    tables = state_log_tables(p, members, T)
    q, gamma, _, ll = e_step(y, clusters, tables, p.rho, T, W)
    trace.append(ll)
    return p, q, gamma, trace


def fit(y, clusters, members, T, max_iter=300, tol=1e-6, W=None):
    """EM fit. members: (K, G) bool. G=0 reduces to plain Dawid-Skene.

    `W` (N, K, optional) is a per-(unit, arm) non-negative vote weight: the fit maximises the
    weighted log-likelihood ``sum_{i,k} W[i,k] log P(y_i | ...)`` instead of the plain one, with
    the same weight applied to the initialisation's majority vote (`init_params`) and to every
    sufficient statistic (`m_step`). `W=None` means all-ones and is bit-identical to the fit
    without this argument. Two constructions matter in practice: `W[i,k] = 1/n_{c(i)}` for an arm
    that annotates *clusters* (one call expanded to every cell of the cluster, so one independent
    observation per cluster rather than `n_c`), and a per-arm constant that splits a duplicated or
    shared-resource group's total weight of 1 between its members.

    Monotone by construction: each M-step is scored on the same objective `e_step` reports, and a
    step that does not increase it is refused (the returned parameters stay those of the previous,
    better, step). The M-step is not an exact maximiser everywhere even after the sufficient-
    statistics fix above -- `rho` is a Dirichlet-floored posterior mean rather than the argmax, the
    cap in `state_log_tables` redistributes `m`'s excess off the raw histogram, and a/s/o/o are
    clipped -- so a refusal is possible, and refusing is what keeps `loglik` non-decreasing.

    Monotone is not optimal, so the fit is restarted once per cluster from a cluster-localised
    `m` seed (`cluster_seed_m`) and the best run wins. The free EM parks on a plateau that no
    refusal explains: the M-step there is a fixed point to machine precision (measured on the
    vote-derived k=12 partition: max|delta| 8e-9 on `a`, 3e-14 on `rho`, and the candidate scores
    -0.000000 nats), so there is no step to damp or to re-score -- the trap is that `m_g` was
    shaped by the one cluster that won the initial competition and no other cluster can then
    prefer it (measured: the free fit's own lz gap is +63.84 nats on that cluster and -3506.98 on
    a cluster that *is* failing). Re-localising `m_g` at cluster c crosses that barrier: on
    vote-k12 it reaches -135372.380, +904.77 nats over the free fit and +747.59 over the best pinned constrained fit
    the free optimum was measured against (the "+252.40" that stood here came from a delegated
    run's report and does not survive the arithmetic: -135372.380 - (-136119.967) = 747.587,
    which is what the plateau verification log records). The restarts are deterministic (no
    RNG), cost C extra EM runs, and can only raise the objective -- a run that does not beat the
    incumbent is discarded, so the trace returned is the winning run's own (non-decreasing) trace
    and `n_iter` is that run's iteration count.

    Contract on the DS fallback: the returned `FitResult` is always *shape-consistent with the free
    fit*, so "no failure states" is a readable outcome rather than a zero-size array. When the guard
    fires, `params.rho` is (G,) all zeros, `params.m` is the (G, T+2) uniform filler (rho gives it
    no prior mass, so it is never scored), `q` is (C, G+1) with all mass on state 0, and
    `a`/`s`/`o`/`gamma`/`loglik` are the DS fit's. `no_failure_states` on the result says which case
    this is; a consumer that would report a number derived from the failure states (a suspect group,
    a failure mass, a rho hurdle) reports "no failure states" instead.
    """
    check_weights(W, y)
    G = members.shape[1]
    p0 = init_params(y, T, G, W)
    p, q, gamma, trace = _em(y, clusters, members, T, p0, max_iter, tol, W)
    for c in range(int(clusters.max()) + 1) if G else ():
        seed = Params(a=p0.a, s=p0.s, o=p0.o, rho=p0.rho,
                      m=cluster_seed_m(y, clusters, members, T, c))
        p_c, q_c, gamma_c, trace_c = _em(y, clusters, members, T, seed, max_iter, tol, W)
        if trace_c[-1] > trace[-1]:
            p, q, gamma, trace = p_c, q_c, gamma_c, trace_c
    if G:
        # The free fit nests Dawid-Skene (rho = 0, G = 0), so a free fit *below* it is a fit that
        # has not reached even its own special case: the nested model is a feasible point, and the
        # honest answer is the better of the two. Never worse than DS by construction. On
        # `base_source` G=9 (canonical and every res* partition) this guard fires: the free fit
        # converges 0.35-0.73 nats *below* the DS fit it nests -- no accuracy change, but no gain
        # either (see the report). Under `W` the nested fit is the *weighted* DS fit (same W), so
        # the comparison stays inside one objective.
        ds = fit(y, clusters, members[:, :0], T, max_iter=max_iter, tol=tol, W=W)
        if ds.loglik[-1] > trace[-1]:
            G, C = members.shape[1], ds.q.shape[0]
            return FitResult(
                params=Params(a=ds.params.a, s=ds.params.s, o=ds.params.o,
                              rho=np.zeros(G), m=np.full((G, T + 2), 1.0 / (T + 2))),
                q=np.concatenate([np.ones((C, 1)), np.zeros((C, G))], axis=1),
                gamma=ds.gamma, loglik=ds.loglik, n_iter=ds.n_iter, no_failure_states=True)
    return FitResult(params=p, q=q, gamma=gamma, loglik=trace, n_iter=len(trace) - 1)


# ---------------------------------------------------------------------------
# group membership: which shared resource each annotator consumes
# ---------------------------------------------------------------------------
# `meta` is a polars DataFrame (arm -> tool/family/base_source/...); the annotation stays a
# string at run time (see `from __future__ import annotations` above), so polars is not imported
# here -- the analysis scripts own that dependency and pass their own frame in.

def membership_matrix(meta: pl.DataFrame, axes: tuple[str, ...] = ("base_source",)):
    """Boolean (K x G) membership + group names, built from the given axes.

    Every annotator belongs to exactly one group per axis-value combination
    (v0: one group per base source). Extra groups can later be added by
    extending `axes` to e.g. ("base_source", "tool").
    """
    import numpy as np

    records = meta.to_dicts()
    keys = [tuple(str(rec[a]) for a in axes) for rec in records]
    gnames = sorted(set(keys))
    index = {g: i for i, g in enumerate(gnames)}
    members = np.zeros((len(records), len(gnames)), dtype=bool)
    for k, key in enumerate(keys):
        members[k, index[key]] = True
    return members, gnames
