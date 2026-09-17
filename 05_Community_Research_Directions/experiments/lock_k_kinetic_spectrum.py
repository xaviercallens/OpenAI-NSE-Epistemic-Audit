"""
Lock K: what kind of drain does kinetic theory supply at k ~ 1/lambda?

The v5.2.0 paper says the lock operating where the continuum ends is dissipative
and supplied by kinetic theory. This script asks what that drain looks like as a
function of wavenumber, by computing the exact shear-mode spectrum of the
linearized BGK equation and setting it against the three candidates already in
the programme: plain viscosity, the hyperviscous barrier, and the transport gate.

Outcome (recorded 2026-09-17): the v5.2.0 premise quoted above did not survive. The spectrum shows
kinetic theory is not a stronger drain -- damping is below viscous, capped at 1/tau, and the shear mode
ends at k lambda = sqrt(pi/2) -- so v5.3.0 withdrew "dissipative, supplied by kinetic theory"; the
nonlinear test (kinetic_lock_rs) then found no arrest there either (v5.4.0).

Model and derivation
--------------------
Linearized BGK, units v_th = sqrt(kT/m) = 1, collision time tau, so the kinematic
viscosity is nu = v_th^2 tau = tau and the mean free path lambda = v_th tau = tau;
the dimensionless wavenumber is q = k lambda.

    d_t f + v . grad f = -(f - f_eq)/tau,     f = f0(v)(1 + phi).

Take the wavevector along x and perturb only the transverse velocity u_y. The
shear mode decouples from density and temperature: those enter phi_eq through
moments even in v_y, while u_y enters through v_y u_y, which is odd. So
phi_eq = v_y u_y, u_y = <v_y phi>, and with phi ~ exp(i k x + s t):

    (s + i k v_x + 1/tau) phi = v_y u_y / tau.

Multiply by v_y and average; v_y is independent of v_x and <v_y^2> = 1, so with
sigma = s + 1/tau

    D(s, k) = 1 - (1/tau) < 1/(sigma + i k v) >_{v ~ N(0,1)} = 0.

Evaluation. For Re sigma > 0,
    <1/(sigma + i k v)> = (1/(i k)) (1/sqrt 2) Z(i sigma/(sqrt 2 k)),
with Z(z) = i sqrt(pi) w(z) the plasma dispersion function. (Write
sigma + i k v = i k (v - zeta0), zeta0 = i sigma/k, substitute v = sqrt2 t; Im of
the Z argument is Re sigma/(sqrt2 k) > 0 as the integral form requires.) The
identity is checked against direct quadrature before it is used.

Two results follow in closed form and are checked numerically below.

 (1) Burnett-order correction. Expanding <1/(sigma + i k v)> in k gives
     tau s = -q^2 + q^4 + O(q^6), i.e. damping rate
         Gamma = nu k^2 (1 - (k lambda)^2 + ...).
     The k^4 term REDUCES damping -- the opposite sign to a hyperviscous barrier.
     Truncating there gives s = -nu k^2 (1 - q^2) > 0 for q > 1: the truncated
     (Burnett-order) equation is unstable at short wavelength, which is the
     instability Bobylev (1982) found for the Burnett equations, here derived for
     this mode. The full kinetic mode is not unstable (see (3)).

 (2) Termination. For real s the imaginary part of <.> vanishes by symmetry, so
     the hydrodynamic root is real. D(0) = 1 - <1/(1+k^2 v^2)> > 0, while as
     sigma -> 0+ the kernel sigma/(sigma^2 + k^2 v^2) -> (pi/k) delta(v), so
     D -> 1 - sqrt(pi/2)/(k tau). A real root with Re s > -1/tau therefore exists
     iff q < q_c = sqrt(pi/2) = 1.2533: at q_c the mode reaches the edge of the
     continuous spectrum Re s = -1/tau and stops being an eigenvalue.

 (3) Stability bound. In the weighted inner product <psi, chi>_w = sum w psi* chi
     the discrete-velocity operator is M = -ik diag(v) - (1/tau)(I - P), with the
     advection term skew-adjoint and P = 1 w^T an orthogonal projection. So every
     eigenvalue satisfies -1/tau <= Re s <= 0: the damping of ANY mode is bounded
     by the collision rate. (This is the spectral twin of the H-theorem proved for
     the discrete BGK step in LatticeBGKEntropy.lean.)

Comparisons
-----------
    NSE      Gamma = nu k^2
    barrier  Gamma = nu k^2 max(1, alpha' k^2),  sqrt(alpha') = lambda
    gate     Gamma = nu k^2  -- Leray-alpha and LANS-alpha differ from NSE only
             in the NONLINEAR transport term; linearized about rest the advective
             term vanishes and the viscous symbol is unchanged (for LANS-alpha the
             Helmholtz operator commutes with the Laplacian, so u and v share the
             symbol -nu k^2). A gate adds no linear damping at any k.

Usage:  python3 lock_k_kinetic_spectrum.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import integrate, optimize
from scipy.special import wofz

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

Q_CRIT_ANALYTIC = float(np.sqrt(np.pi / 2.0))


# ---------------------------------------------------------------------------
# Continuous-velocity BGK (method M1)
# ---------------------------------------------------------------------------

def plasma_Z(z):
    """Plasma dispersion function Z(z) = i sqrt(pi) w(z) (analytic continuation of the integral form)."""
    return 1j * np.sqrt(np.pi) * wofz(z)


def mean_resolvent_Z(sigma, k):
    """<1/(sigma + i k v)> for v ~ N(0,1), via Z. Exact for Re sigma > 0."""
    return (1.0 / (1j * k)) * (1.0 / np.sqrt(2.0)) * plasma_Z(1j * sigma / (np.sqrt(2.0) * k))


def mean_resolvent_quad(sigma, k):
    """<1/(sigma + i k v)> by direct quadrature (reference for the Z identity)."""
    def integrand(v, part):
        val = np.exp(-0.5 * v * v) / np.sqrt(2.0 * np.pi) / (sigma + 1j * k * v)
        return val.real if part == "re" else val.imag
    re = integrate.quad(integrand, -np.inf, np.inf, args=("re",), limit=500, epsabs=1e-13, epsrel=1e-12)[0]
    im = integrate.quad(integrand, -np.inf, np.inf, args=("im",), limit=500, epsabs=1e-13, epsrel=1e-12)[0]
    return re + 1j * im


def dispersion(s, k, tau=1.0):
    """D(s, k) = 1 - (1/tau) <1/(s + 1/tau + i k v)>."""
    return 1.0 - mean_resolvent_Z(s + 1.0 / tau, k) / tau


def hydrodynamic_root_M1(k, tau=1.0, n_scan=4000):
    """
    Least-damped real root of D in (-1/tau, 0), or None if the mode does not exist.

    D is real for real s (the odd part of the kernel averages to zero). Scan for
    sign changes, then refine the one closest to zero with brentq.
    """
    s_lo = -1.0 / tau * (1.0 - 1e-12)
    grid = np.linspace(s_lo, 0.0, n_scan)
    vals = dispersion(grid, k, tau).real
    changes = np.nonzero(np.sign(vals[:-1]) * np.sign(vals[1:]) < 0)[0]
    if len(changes) == 0:
        return None
    i = changes[-1]  # least damped
    f = lambda s: dispersion(s, k, tau).real
    return float(optimize.brentq(f, grid[i], grid[i + 1], xtol=1e-15, rtol=1e-14, maxiter=500))


def landau_continued_root(k, tau=1.0, n_scan=4000):
    """
    For q > q_c, the real zero of the analytically continued D below Re s = -1/tau.
    This is a second-sheet RESONANCE (governing a transient decay), not an
    eigenvalue of the operator. Reported for context only.
    """
    grid = np.linspace(-6.0 / tau, -1.0 / tau * (1.0 + 1e-9), n_scan)
    vals = dispersion(grid, k, tau).real
    changes = np.nonzero(np.sign(vals[:-1]) * np.sign(vals[1:]) < 0)[0]
    if len(changes) == 0:
        return None
    i = changes[-1]
    f = lambda s: dispersion(s, k, tau).real
    return float(optimize.brentq(f, grid[i], grid[i + 1], xtol=1e-15, rtol=1e-14, maxiter=500))


def critical_q_M1(tau=1.0):
    """Bisect for the largest q at which the hydrodynamic root still exists."""
    lo, hi = 0.5, 3.0
    assert hydrodynamic_root_M1(lo / tau, tau) is not None
    assert hydrodynamic_root_M1(hi / tau, tau) is None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if hydrodynamic_root_M1(mid / tau, tau) is None:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Discrete-velocity BGK (method M2)
# ---------------------------------------------------------------------------

def gauss_hermite(n):
    """Nodes and probability weights for v ~ N(0,1) (weights sum to 1)."""
    x, w = np.polynomial.hermite_e.hermegauss(n)
    return x, w / np.sqrt(2.0 * np.pi)


def shear_operator(k, n, tau=1.0):
    """M = -ik diag(v) - I/tau + (1/tau) 1 w^T on the reduced shear variable."""
    v, w = gauss_hermite(n)
    return -1j * k * np.diag(v) - np.eye(n) / tau + np.outer(np.ones(n), w) / tau


def hydrodynamic_eig_M2(k, n, tau=1.0, im_tol=1e-8):
    """
    Least-damped REAL eigenvalue of M, or None.

    The hydrodynamic mode is real (symmetric node set, even n so no node at v = 0);
    the discretized continuum eigenvalues carry Im s ~ k v_j != 0. For q > q_c no
    real eigenvalue survives and only spurious continuum eigenvalues remain.
    """
    ev = np.linalg.eigvals(shear_operator(k, n, tau))
    real = ev[np.abs(ev.imag) < im_tol * max(1.0, k)]
    if len(real) == 0:
        return None, ev
    return float(real.real.max()), ev


def critical_q_M2(n, tau=1.0):
    lo, hi = 0.5, 3.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if hydrodynamic_eig_M2(mid / tau, n, tau)[0] is None:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Comparison models
# ---------------------------------------------------------------------------

def gamma_nse(k, tau=1.0):
    return tau * k**2                          # nu = tau


def gamma_barrier(k, tau=1.0):
    lam = tau                                   # sqrt(alpha') = lambda
    return tau * k**2 * np.maximum(1.0, (lam * k) ** 2)


def gamma_gate(k, tau=1.0):
    return tau * k**2                           # linear damping unchanged


def gamma_burnett_truncated(k, tau=1.0):
    q = k * tau
    return tau * k**2 * (1.0 - q**2)            # negative for q > 1 -> unstable


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    tau = 1.0
    q = np.logspace(-2, 1, 241)
    k = q / tau

    # -- Z identity check
    z_checks = []
    for sig, kk in ((1.0, 0.1), (0.3, 1.0), (1.2, 3.0), (0.05, 0.7), (2.0, 10.0)):
        a, b = mean_resolvent_Z(sig, kk), mean_resolvent_quad(sig, kk)
        z_checks.append({"sigma": sig, "k": kk, "rel_err": float(abs(a - b) / abs(b))})

    # -- M1
    g_m1 = np.array([np.nan if (r := hydrodynamic_root_M1(kk, tau)) is None else -r for kk in k])
    q_c_m1 = critical_q_M1(tau)

    # -- M2 for three N
    m2 = {}
    for n in (40, 80, 160):
        g = np.array([np.nan if (e := hydrodynamic_eig_M2(kk, n, tau)[0]) is None else -e for kk in k])
        spur = []
        for qq in (2.0, 3.0, 5.0):
            ev = np.linalg.eigvals(shear_operator(qq / tau, n, tau))
            spur.append({"q": qq, "least_damped_rate_tau": float(-ev.real.max() * tau),
                         "max_re_eig": float(ev.real.max()), "min_re_eig": float(ev.real.min())})
        m2[n] = {"gamma": g, "q_c": critical_q_M2(n, tau), "spurious_above_qc": spur}

    # -- (a) small-k agreement and Burnett coefficient
    # Gamma/(nu k^2) = 1 - c q^2 + d q^4 - ... (asymptotic; coefficients grow). A
    # windowed polynomial fit is contaminated by the q^4 term (it returned c ~ 0.96
    # over q in [0.01, 0.1]), so estimate c pointwise, c(q) = -(Gamma/nu k^2 - 1)/q^2,
    # and Richardson-extrapolate c(q) = c0 - d q^2 from two small q.
    def c_of(qq):
        r = hydrodynamic_root_M1(qq / tau, tau)
        return -((-r) / gamma_nse(qq / tau, tau) - 1.0) / qq**2
    q1, q2 = 0.01, 0.02
    c1, c2 = c_of(q1), c_of(q2)
    burnett_c = float((c1 * q2**2 - c2 * q1**2) / (q2**2 - q1**2))
    next_coeff_d = float((c1 - c2) / (q2**2 - q1**2))
    rel_small = float(abs(g_m1[0] - gamma_nse(k[0], tau)) / gamma_nse(k[0], tau))
    exist = np.isfinite(g_m1)
    below_nse = bool(np.all(g_m1[exist & (q > 0.02)] < gamma_nse(k[exist & (q > 0.02)], tau)))

    # -- (b) maximum damping and ratio to 1/tau
    max_grid = float(np.nanmax(g_m1) * tau)
    r_near = hydrodynamic_root_M1(Q_CRIT_ANALYTIC * (1 - 1e-6) / tau, tau)
    max_near_qc = float(-r_near * tau) if r_near is not None else None
    bound_ok_m1 = bool(np.all(g_m1[exist] * tau <= 1.0 + 1e-12))

    # -- (d) barrier vs kinetic at q = 1 and 3
    def kin_at(qq):
        r = hydrodynamic_root_M1(qq / tau, tau)
        return (None if r is None else -r)
    d = {}
    for qq in (1.0, 3.0):
        kin = kin_at(qq)
        bar = float(gamma_barrier(qq / tau, tau))
        if kin is None:
            d[str(qq)] = {"barrier_rate": bar, "kinetic_mode": None,
                          "barrier_over_kinetic_lower_bound": bar / (1.0 / tau),
                          "note": "no hydrodynamic mode; ratio bounded below using the collision-rate cap 1/tau"}
        else:
            d[str(qq)] = {"barrier_rate": bar, "kinetic_rate": kin, "barrier_over_kinetic": bar / kin}

    # -- M1 vs M2 agreement for q <= 0.5
    sel = (q <= 0.5) & exist
    m1m2 = float(np.max(np.abs(m2[160]["gamma"][sel] - g_m1[sel]) / g_m1[sel]))

    # -- global stability of discrete operator
    stab = []
    for n in (40, 80, 160):
        for qq in (0.1, 1.0, 1.25, 3.0, 10.0):
            ev = np.linalg.eigvals(shear_operator(qq / tau, n, tau))
            stab.append((float(ev.real.max()), float(ev.real.min())))
    max_re = max(a for a, _ in stab)
    min_re = min(b for _, b in stab)

    # -- Landau-continued resonance beyond q_c (context)
    landau = []
    for qq in (1.5, 2.0, 3.0):
        r = landau_continued_root(qq / tau, tau)
        landau.append({"q": qq, "resonance_rate_tau": None if r is None else float(-r * tau)})

    # -- verdicts, computed
    hypothesis = {
        "small_k_matches_nse": rel_small < 1e-3,
        "burnett_term_reduces_damping": burnett_c > 0,
        "damping_below_nse_throughout": below_nse,
        "saturates_at_collision_rate": bool(max_near_qc is not None and abs(max_near_qc - 1.0) < 1e-3 and bound_ok_m1),
        "mode_terminates_at_order_one_q": bool(0.3 < q_c_m1 < 3.0),
        "q_c_matches_sqrt_pi_over_2": bool(abs(q_c_m1 - Q_CRIT_ANALYTIC) < 1e-6),
        "not_barrier_like": bool(burnett_c > 0 and below_nse),
    }
    hypothesis["held"] = all(hypothesis[key] for key in
                             ("small_k_matches_nse", "saturates_at_collision_rate",
                              "mode_terminates_at_order_one_q", "not_barrier_like"))

    out = {
        "units": "v_th = 1, nu = tau, lambda = tau, q = k lambda; rates reported as Gamma*tau",
        "z_identity_checks": z_checks,
        "a_small_k": {"rel_err_vs_nse_at_q_0.01": rel_small,
                      "burnett_coefficient_c": burnett_c,
                      "burnett_expected_from_expansion": 1.0,
                      "pointwise_c_at_q": {str(q1): float(c1), str(q2): float(c2)},
                      "next_coefficient_d_fitted_not_derived": next_coeff_d,
                      "sign": "reduces damping (opposite to a hyperviscous barrier)",
                      "truncated_burnett_unstable_for_q_gt": 1.0},
        "b_max_damping": {"max_on_grid_Gamma_tau": max_grid,
                          "Gamma_tau_at_q_c_minus_1e-6": max_near_qc,
                          "bounded_by_collision_rate_everywhere": bound_ok_m1},
        "c_critical_q": {"M1_bisection": q_c_m1, "analytic_sqrt_pi_over_2": Q_CRIT_ANALYTIC,
                         "M2": {str(n): m2[n]["q_c"] for n in m2}},
        "d_barrier_vs_kinetic": d,
        "M1_M2_max_rel_diff_q_le_0.5": m1m2,
        "discrete_operator_spectrum_bounds": {"max_re": max_re, "min_re": min_re,
                                              "within_[-1/tau,0]": bool(max_re <= 1e-12 and min_re >= -1.0 / tau - 1e-12)},
        "M2_spurious_above_qc": {str(n): m2[n]["spurious_above_qc"] for n in m2},
        "landau_continued_resonance_context_only": landau,
        "hypothesis": hypothesis,
        "series": {"q": q.tolist(), "gamma_tau_M1": [None if not np.isfinite(x) else float(x) for x in g_m1],
                   **{f"gamma_tau_M2_N{n}": [None if not np.isfinite(x) else float(x) for x in m2[n]["gamma"]] for n in m2},
                   "gamma_tau_nse": gamma_nse(k, tau).tolist(),
                   "gamma_tau_barrier": gamma_barrier(k, tau).tolist()},
    }
    (OUT / "lock_k_kinetic_spectrum.json").write_text(json.dumps(out, indent=2))

    # -- figure
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8.2, 5.6))
        ax.loglog(q, gamma_nse(k, tau), "k-", lw=1.8, label=r"Navier–Stokes $\nu k^2$")
        ax.loglog(q, gamma_gate(k, tau) * 1.12, ":", color="#2ca02c", lw=2,
                  label=r"transport gate (Leray-/LANS-$\alpha$): $\nu k^2$, unchanged (offset for visibility)")
        ax.loglog(q, gamma_barrier(k, tau), "-", color="#d62728", lw=1.8,
                  label=r"barrier $\nu k^2\max(1,\alpha'k^2)$, $\sqrt{\alpha'}=\lambda$")
        pos = q < 1.0
        ax.loglog(q[pos], gamma_burnett_truncated(k[pos], tau), "--", color="#9467bd", lw=1.2,
                  label=r"Burnett-truncated $\nu k^2(1-k^2\lambda^2)$ (unstable for $k\lambda>1$)")
        ax.loglog(q, g_m1, "-", color="#1f77b4", lw=2.6, label="kinetic BGK, exact root (M1)")
        idx = np.arange(0, len(q), 8)
        ax.loglog(q[idx], m2[160]["gamma"][idx], "o", ms=4, mfc="none", color="#1f77b4",
                  label="kinetic BGK, discrete velocities N=160 (M2)")
        ax.axhline(1.0 / tau, color="gray", ls="--", lw=1, label=r"collision rate $1/\tau$")
        ax.axvline(q_c_m1, color="#1f77b4", ls=":", lw=1.2,
                   label=rf"mode terminates, $k\lambda=\sqrt{{\pi/2}}={q_c_m1:.4f}$")
        ax.set_xlabel(r"$k\lambda$")
        ax.set_ylabel(r"shear-mode damping rate $\Gamma\tau$")
        ax.set_ylim(1e-4, 1e3)
        ax.set_title("Lock K: the kinetic shear mode saturates at the collision rate and terminates;\n"
                     "it is neither a barrier (stronger drain) nor a gate (no linear effect)", fontsize=10)
        ax.legend(fontsize=7.2, loc="upper left")
        ax.grid(alpha=0.3, which="both")
        fig.tight_layout()
        fig.savefig(OUT / "lock_k_kinetic_spectrum.png", dpi=180)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover
        print(f"(figure skipped: {exc})")

    # -- report
    print("=" * 76)
    print(" LOCK K: linearized BGK shear-mode spectrum vs NSE / barrier / gate")
    print("=" * 76)
    print(f" Z identity vs quadrature: max rel err {max(c['rel_err'] for c in z_checks):.2e}")
    print(f" (a) q=0.01: rel err vs nu k^2 = {rel_small:.2e};  Burnett coefficient c = {burnett_c:+.6f}"
          f" (expansion: +1; pointwise {c1:.5f} at q={q1}) -> Gamma = nu k^2 (1 - c (k lambda)^2 + d (k lambda)^4),"
          f" d = {next_coeff_d:+.3f} (fitted): the k^4 term reduces damping")
    print(f"     damping below NSE for all 0.02 < q < q_c: {below_nse}")
    print(f" (b) max Gamma*tau on grid {max_grid:.4f}; at q_c(1-1e-6): {max_near_qc:.6f};"
          f" bounded by 1/tau everywhere: {bound_ok_m1}")
    print(f" (c) q_c: M1 {q_c_m1:.10f}  analytic sqrt(pi/2) {Q_CRIT_ANALYTIC:.10f};"
          f"  M2 " + ", ".join(f"N={n}: {m2[n]['q_c']:.4f}" for n in m2))
    for qq, v in d.items():
        if "barrier_over_kinetic" in v:
            print(f" (d) q={qq}: barrier/kinetic = {v['barrier_over_kinetic']:.3f}")
        else:
            print(f" (d) q={qq}: no kinetic mode; barrier/(1/tau) >= {v['barrier_over_kinetic_lower_bound']:.1f}")
    print(f" M1 vs M2(N=160), q <= 0.5: max rel diff {m1m2:.2e}")
    print(f" discrete operator: Re eig in [{min_re:.6f}, {max_re:.2e}]  (bound [-1/tau, 0])")
    for n in m2:
        sp = m2[n]["spurious_above_qc"]
        print(f" M2 N={n}: least-damped spurious rate at q=2,3,5: "
              + ", ".join(f"{s['least_damped_rate_tau']:.4f}" for s in sp))
    print(f" Landau-continued resonance (context, not an eigenvalue): "
          + ", ".join(f"q={r['q']}: {r['resonance_rate_tau']}" for r in landau))
    print(f" HYPOTHESIS HELD: {hypothesis['held']}   {hypothesis}")


if __name__ == "__main__":
    main()
