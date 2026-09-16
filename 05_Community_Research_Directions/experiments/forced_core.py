"""
Direction 1: the forced-core test bed.

Every earlier test of the cutoff law failed for the same reason: generic data
never produces a Re ~ 1 collapsing core, so the law's premise was never met.
This script manufactures that core and sustains it with a forcing, so the four
predictions can be tested as a dynamical question for the first time.

The target
----------
A time-reversed Lamb-Oseen column, z-invariant, with fixed circulation Gamma and
a core radius that SHRINKS on the diffusive scaling:

    omega_z(r, t) = Gamma/(pi l^2) exp(-r^2/l^2),     l(t)^2 = nu * tau,   tau = T - t.

Fixed Gamma with l = sqrt(nu tau) gives u_max * l / nu = 0.638 Gamma/(2 pi nu);
choosing Gamma = 2 pi nu / 0.638 makes Re_core = 1 exactly -- the premise of the
cutoff law, satisfied by construction. Peak vorticity is then Gamma/(pi nu tau),
i.e. ~1/tau, and peak velocity ~sqrt(nu/tau): the construction's own scalings.

The forcing
-----------
The residual of the target under plain Navier-Stokes,
    f = d_t U - N(U) - nu Lap U,
computed numerically with the solver's own operators (so the alpha'=0 run
reproduces the target to discretization accuracy -- the control). For an
axisymmetric column N(U) is a pure gradient and projects to zero, so
f = d_t U - nu Lap U. With l^2 = nu tau the Gaussian obeys d_t omega = -(nu/4) Lap omega
(the paper's convention is a factor 4 tighter than Lamb-Oseen's l^2 = 4 nu tau),
so f = -(5/4) nu Lap U: time-reversed diffusion needs anti-diffusion.

Why arrest is a clean event here
--------------------------------
The SAME forcing is applied with the barrier on. The barrier's extra dissipation
at the core wavenumber k ~ 1/l is nu alpha' k^4 u ~ alpha' / (sqrt(nu) tau^{5/2}),
while the forcing is ~ sqrt(nu)/tau^{3/2}. Their ratio is  B/F = C alpha'/(nu tau)
with C an O(1) prefactor the scaling argument does not fix (it depends on how much
of the Gaussian's spectrum lies above k_alpha). It crosses unity at

    tau_c = C alpha'/nu,   l = sqrt(C alpha')   (P1, P4),

and there u_max = nu/sqrt(C alpha') (P2), omega_max ~ nu/(C alpha') (P3). The
EXPONENTS are C-independent; C is measured from the pooled B/F series. On this
bed the predictions are a dynamical competition between forcing and barrier, not
a kinematic identity, and "arrest" is defined as the B/F = 1 crossing.

What this bed cannot test
-------------------------
The transport gates (Leray-alpha, LANS-alpha). For a z-invariant axisymmetric
column every alpha-model nonlinearity is a pure gradient and projects to zero,
so those models are INERT here -- verified numerically below. Testing them needs
axial structure (the construction's l_z, u_z). That is stage 2.

Usage:  python3 forced_core.py --n 64 --nu 0.01 --l0 0.8 --points 5
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from spectral3d import PseudoSpectralNavierStokes3D
from sweep_cutoff_law import fit_power_law

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

LAMB_OSEEN_PEAK_FACTOR = 0.63817  # u_max = factor * Gamma/(2 pi l) at r = 1.1209 l


class ForcedCore:
    """Manufactured Re=1 collapsing column and the forcing that sustains it."""

    def __init__(self, solver: PseudoSpectralNavierStokes3D, nu: float, l0: float,
                 re_core: float = 1.0):
        self.s = solver
        self.nu = nu
        self.l0 = l0
        self.T = l0**2 / nu                         # blow-up time: l(T) = 0
        self.gamma = 2.0 * np.pi * nu * re_core / LAMB_OSEEN_PEAK_FACTOR
        x, y, _ = solver.grid()
        self.r2 = (x - np.pi) ** 2 + (y - np.pi) ** 2
        # reference solver for the residual: plain NSE, same grid
        self.ref = PseudoSpectralNavierStokes3D(n_grid=solver.n, nu=nu)

    # -- analytic target -------------------------------------------------
    def ell(self, t: float) -> float:
        tau = self.T - t
        return float(np.sqrt(self.nu * max(tau, 1e-300)))

    def omega_peak(self, t: float) -> float:
        return self.gamma / (np.pi * self.ell(t) ** 2)

    def u_peak(self, t: float) -> float:
        return LAMB_OSEEN_PEAK_FACTOR * self.gamma / (2.0 * np.pi * self.ell(t))

    def _velocity_from_vorticity(self, w: np.ndarray) -> np.ndarray:
        s = self.s
        w_hat = np.fft.fftn(w)
        w_hat[0, 0, 0] = 0.0                        # periodize: remove mean vorticity
        # u = (-d_y psi, d_x psi) gives omega_z = Lap psi, so Lap psi = omega, i.e.
        # psi_hat = -omega_hat/k^2. (An earlier revision used +omega_hat/k^2, which
        # inverts the vortex sign -- harmless to the dynamics, fatal to any
        # sign-sensitive estimator.)
        psi_hat = -w_hat * s.k_sq_inv
        u_hat = np.stack([-1j * s.ky * psi_hat, 1j * s.kx * psi_hat, np.zeros_like(psi_hat)])
        return s.project_leray(u_hat)

    def vorticity_z_slice(self, u_hat: np.ndarray) -> np.ndarray:
        s = self.s
        wz_hat = 1j * (s.kx * u_hat[1] - s.ky * u_hat[0])
        return np.fft.ifftn(wz_hat).real[:, :, 0]      # z-invariant: any slice

    def target(self, t: float) -> np.ndarray:
        l2 = self.ell(t) ** 2
        w = (self.gamma / (np.pi * l2)) * np.exp(-self.r2 / l2)
        return self._velocity_from_vorticity(w)

    def target_dt(self, t: float) -> np.ndarray:
        """d/dt of the target: d_t omega = (nu omega / l^2)(1 - r^2/l^2)."""
        l2 = self.ell(t) ** 2
        w = (self.gamma / (np.pi * l2)) * np.exp(-self.r2 / l2)
        dw = (self.nu * w / l2) * (1.0 - self.r2 / l2)
        return self._velocity_from_vorticity(dw)

    def forcing(self, t: float) -> np.ndarray:
        """Residual of the target under plain Navier-Stokes (the reference operators)."""
        U = self.target(t)
        return self.ref.project_leray(self.target_dt(t) - self.ref.nonlinear(U)
                                      - self.ref.diss_symbol * U)

    # -- diagnostics ------------------------------------------------------
    def ell_from_peak(self, u_hat: np.ndarray) -> float:
        """
        Gaussian inversion, l = sqrt(Gamma/(pi omega_max)). BIASED once the barrier
        acts: it flattens the peak, so this over-estimates l. Kept for comparison.
        """
        wmax = self.s.max_vorticity(u_hat)
        return float(np.sqrt(self.gamma / (np.pi * wmax))) if wmax > 0 else float("inf")

    def ell_from_moment(self, u_hat: np.ndarray) -> float:
        """
        Enstrophy-weighted second moment: for a Gaussian omega of width l,
        omega^2 has width l/sqrt(2), so  l^2 = 2 * int omega^2 r^2 dA / int omega^2 dA.
        Insensitive to peak shape and to the vortex sign. The uniform
        periodization floor (-Gamma/4pi^2, from removing the mean) is added back
        analytically first; circulation is conserved by both the forcing and the
        barrier, so Gamma is known throughout. (An earlier revision clipped at
        zero, which truncated the Gaussian tail and biased l 12% low at l = 1.)
        """
        wz = self.vorticity_z_slice(u_hat) + self.gamma / (4.0 * np.pi**2)
        r2 = self.r2[:, :, 0]
        w2 = wz * wz
        denom = float(np.sum(w2))
        return float(np.sqrt(2.0 * np.sum(w2 * r2) / denom)) if denom > 0 else float("inf")

    def rel_l2_error(self, u_hat: np.ndarray, t: float) -> float:
        """Whole-field error against the analytic target: unbiased by grid peak sampling."""
        U = self.target(t)
        return float(np.sqrt(np.sum(np.abs(u_hat - U) ** 2) / np.sum(np.abs(U) ** 2)))

    def forcing_power(self, u_hat: np.ndarray, t: float) -> float:
        f = self.forcing(t)
        return float(np.real(np.sum(np.conj(u_hat) * f))) / (self.s.n ** 6)

    def barrier_extra_dissipation(self, u_hat: np.ndarray) -> float:
        """Dissipation from the barrier in excess of plain nu k^2."""
        extra = -(self.s.diss_symbol - self.ref.diss_symbol)
        return float(np.sum(extra * np.abs(u_hat) ** 2)) / (self.s.n ** 6)


def run_core(n: int, nu: float, l0: float, alpha_prime: float | None,
             l_min_cells: float = 3.0, cfl: float = 0.4, tau_frac: float = 0.02,
             dissipation: str = "barrier", **model_kw) -> dict:
    kw = dict(alpha_prime=alpha_prime, dissipation=dissipation) if alpha_prime else {}
    kw.update(model_kw)
    s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu, **kw)
    core = ForcedCore(s, nu, l0)
    dx = 2.0 * np.pi / n
    l_min = l_min_cells * dx
    t_end = core.T - l_min**2 / nu               # stop when the TARGET core reaches l_min

    rec = {"t": [], "tau": [], "omega_max": [], "u_max": [], "ell_meas": [], "ell_peak": [],
           "omega_target": [], "u_target": [], "ell_target": [], "rel_l2_error": [],
           "forcing_power": [], "barrier_extra": []}

    def progress(t, d):
        pass

    u = core.target(0.0)
    t = 0.0
    t0 = time.time()
    # manual loop so we can record target-relative diagnostics at each sample
    step = 0
    while t < t_end:
        tau = core.T - t
        h = min(s.cfl_dt(u, cfl), tau_frac * tau, t_end - t)
        u = s.ifrk4_step(u, h, t=t, forcing=core.forcing)
        t += h
        step += 1
        if step % 2 == 0 or t >= t_end:
            rec["t"].append(t); rec["tau"].append(core.T - t)
            rec["omega_max"].append(s.max_vorticity(u)); rec["u_max"].append(s.max_velocity(u))
            rec["ell_meas"].append(core.ell_from_moment(u))
            rec["ell_peak"].append(core.ell_from_peak(u))
            rec["omega_target"].append(core.omega_peak(t)); rec["u_target"].append(core.u_peak(t))
            rec["ell_target"].append(core.ell(t))
            rec["rel_l2_error"].append(core.rel_l2_error(u, t))
            rec["forcing_power"].append(core.forcing_power(u, t))
            rec["barrier_extra"].append(core.barrier_extra_dissipation(u) if alpha_prime else 0.0)
        if not np.isfinite(rec["omega_max"][-1] if rec["omega_max"] else 0.0):
            raise FloatingPointError("diverged")
    wall = time.time() - t0

    R = {k: np.asarray(v) for k, v in rec.items()}
    rel_err = np.abs(R["omega_max"] - R["omega_target"]) / R["omega_target"]
    out = {
        "alpha_prime": alpha_prime, "n": n, "nu": nu, "l0": l0, "T": core.T,
        "gamma": core.gamma, "steps": step, "wall_s": round(wall, 1),
        "l_min_target": l_min,
        "max_rel_error_omega": float(np.max(rel_err)),
        "final_rel_error_omega": float(rel_err[-1]),
        "max_rel_l2_error": float(np.max(R["rel_l2_error"])),
        "final_rel_l2_error": float(R["rel_l2_error"][-1]),
        "series": {k: v.tolist() for k, v in R.items()},
    }
    if alpha_prime:
        # Arrest = the barrier's extra dissipation overtakes the forcing power
        # (B/F crosses 1). This is the scaling argument's own definition. If the
        # crossing is not reached inside the resolved window, the run reports the
        # last sample and arrested_before_end = False -- it is then usable only
        # for the pooled B/F-slope fit, not for the arrest-point exponents.
        bf = R["barrier_extra"] / np.maximum(np.abs(R["forcing_power"]), 1e-300)
        crossed = np.nonzero(bf >= 1.0)[0]
        i = int(crossed[0]) if len(crossed) else len(bf) - 1
        i_w = int(np.argmax(R["omega_max"]))
        out.update({
            "t_arrest": float(R["t"][i]),
            "tau_at_arrest": float(R["tau"][i]),
            "ell_at_arrest": float(R["ell_meas"][i]),
            "u_at_arrest": float(R["u_max"][i]),
            "omega_at_arrest": float(R["omega_max"][i]),
            "tau_at_omega_peak": float(R["tau"][i_w]),
            "arrested_before_end": bool(len(crossed) > 0),
            "bf_at_end": float(bf[-1]),
            "lag_at_end": float(R["ell_meas"][-1] / R["ell_target"][-1] - 1.0),
            "predicted": {"tau_c": alpha_prime / nu, "ell": float(np.sqrt(alpha_prime)),
                          "u": nu / float(np.sqrt(alpha_prime)),
                          "omega": core.gamma / (np.pi * alpha_prime)},
            "barrier_over_forcing_at_arrest": float(
                R["barrier_extra"][i] / max(abs(R["forcing_power"][i]), 1e-300)),
        })
    return out


def pooled_bf_law(runs: list, nu: float, bf_min: float = 0.02,
                  tau_max_frac: float = 0.7) -> dict:
    """
    The mechanism test, usable even when no run reaches B/F = 1: the scaling
    argument predicts  B/F = C alpha'/(nu tau)  at ALL times, i.e. slope 1 in
    log(B/F) vs log(alpha'/(nu tau)) pooled over runs and samples, with the
    intercept giving C. Samples with tiny B/F are excluded (numerical noise).

    Samples with tau > tau_max_frac * T are also excluded: if k_alpha lies inside
    the INITIAL Gaussian's spectrum the barrier strips that tail at t = 0, which
    shows up as an early hook in B/F (and a transient growth of l) that has
    nothing to do with the collapse. The default band now keeps k_alpha above the
    initial core, but the filter makes the fit robust to a badly chosen band.
    """
    xs, ys = [], []
    for r in runs:
        S = r["series"]
        T = r.get("T", np.inf)
        tau = np.asarray(S["tau"])
        bf = np.asarray(S["barrier_extra"]) / np.maximum(np.abs(np.asarray(S["forcing_power"])), 1e-300)
        x = r["alpha_prime"] / (nu * tau)
        m = (bf > bf_min) & (tau < tau_max_frac * T)
        xs.append(x[m]); ys.append(bf[m])
    x = np.concatenate(xs); y = np.concatenate(ys)
    if len(x) < 4:
        return {"n_samples": int(len(x)), "insufficient": True}
    a, b = np.polyfit(np.log(x), np.log(y), 1)
    resid = np.log(y) - (a * np.log(x) + b)
    r2 = 1.0 - np.sum(resid**2) / np.sum((np.log(y) - np.log(y).mean())**2)

    # COLLAPSE is the load-bearing statement, not the slope. If B/F is a single
    # function of alpha'/(nu tau) -- whatever its shape -- then arrest (B/F = 1)
    # happens at one fixed value x* of that variable, so tau_c = alpha'/(nu x*)
    # and the four predicted EXPONENTS follow with no assumption about the
    # slope; only the prefactor depends on the curve's shape. The shape here is
    # concave in log-log (local slope falls with x), as expected for the
    # erfc-like fraction of a Gaussian forcing spectrum lying above k_alpha.
    # Measured on 32^3: C spread 5% across a 2.6x range of alpha'.
    per_run_C, per_run_slope = [], []
    for xr, yr in zip(xs, ys):
        if len(xr) >= 4:
            ar, br = np.polyfit(np.log(xr), np.log(yr), 1)
            per_run_C.append(float(np.exp(br))); per_run_slope.append(float(ar))
    coll = {}
    if len(per_run_C) >= 2:
        C_arr = np.array(per_run_C)
        coll = {"per_run_C": per_run_C, "per_run_local_slope": per_run_slope,
                "C_spread_rel": float(C_arr.std() / C_arr.mean()),
                "collapses": bool(C_arr.std() / C_arr.mean() < 0.15)}
    return {"n_samples": int(len(x)), "slope": float(a), "predicted_slope": 1.0,
            "prefactor_C": float(np.exp(b)), "r_squared": float(r2),
            "x_range_decades": float(np.log10(x.max() / x.min())), **coll}


def alpha_models_are_inert(n: int, nu: float, l0: float) -> dict:
    """Numerically confirm N_alpha(U) = 0 for the z-invariant axisymmetric target."""
    out = {}
    base = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu)
    core = ForcedCore(base, nu, l0)
    U = core.target(0.3 * core.T)
    scale = float(np.sqrt(np.sum(np.abs(U) ** 2)) * np.sqrt(np.max(base.k_sq)))
    out["nse_nonlinear_rel"] = float(np.sqrt(np.sum(np.abs(base.nonlinear(U)) ** 2)) / scale)
    for model in ("leray", "lans"):
        s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu, leray_alpha=0.3, alpha_model=model)
        out[f"{model}_nonlinear_rel"] = float(np.sqrt(np.sum(np.abs(s.nonlinear_term(U)) ** 2)) / scale)
    # The residual is discretization-level (finite grid + dealiasing of a Gaussian),
    # ~1e-7 against O(1); the identity "pure gradient projects to zero" holds to
    # that accuracy, which is what 'inert' means here.
    out["inert"] = bool(max(v for v in out.values() if isinstance(v, float)) < 1e-5)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--nu", type=float, default=0.01)
    ap.add_argument("--l0", type=float, default=0.8)
    ap.add_argument("--points", type=int, default=5)
    ap.add_argument("--l-min-cells", type=float, default=3.0)
    ap.add_argument("--sqrt-a-lo", type=float, default=None, help="override lower sqrt(alpha')")
    ap.add_argument("--sqrt-a-hi", type=float, default=None, help="override upper sqrt(alpha')")
    ap.add_argument("--tag", default="", help="suffix for the output filename")
    args = ap.parse_args()

    dx = 2 * np.pi / args.n
    l_min = args.l_min_cells * dx
    print("=" * 78)
    print(" FORCED-CORE TEST BED (Direction 1): Re=1 collapse sustained by forcing")
    print("=" * 78)
    print(f" n={args.n}^3  nu={args.nu}  l0={args.l0}  T={args.l0**2/args.nu:.1f}"
          f"  l_min={l_min:.3f} ({args.l_min_cells} cells)  usable arrest band: {l_min:.2f} < sqrt(a') < {args.l0:.2f}")

    print("\n[0] alpha-models inert on this target?")
    inert = alpha_models_are_inert(args.n, args.nu, args.l0)
    for k, v in inert.items():
        print(f"    {k}: {v:.2e}" if isinstance(v, float) else f"    {k}: {v}")

    print("\n[1] CONTROL alpha'=0: forced core must track the target")
    ctrl = run_core(args.n, args.nu, args.l0, None, l_min_cells=args.l_min_cells)
    print(f"    max whole-field rel L2 error vs target: {ctrl['max_rel_l2_error']:.3e}"
          f"   (final {ctrl['final_rel_l2_error']:.3e}, {ctrl['steps']} steps, {ctrl['wall_s']}s)")
    print(f"    max rel error in omega_max (grid-peak-sampling limited): {ctrl['max_rel_error_omega']:.3e}")
    ctrl_ok = ctrl["max_rel_l2_error"] < 0.05
    print(f"    control {'PASS' if ctrl_ok else 'FAIL'} (threshold 5% on the L2 field error)")

    # Barrier sweep: sqrt(alpha') must sit inside the resolved collapse window
    # (l_min, l0) -- and well below l0, so that k_alpha = 1/sqrt(alpha') starts
    # ABOVE the initial core's spectrum and the barrier is inert at t = 0. With
    # sqrt(alpha') = 0.7 l0 the barrier strips the initial Gaussian's tail
    # immediately (seen as an early growth of l and a hook in B/F). The usable
    # dynamic range is set by l0/l_min ~ n, which is why a wide sweep needs a
    # large grid.
    lo = args.sqrt_a_lo if args.sqrt_a_lo else 1.3 * l_min
    hi = args.sqrt_a_hi if args.sqrt_a_hi else 0.35 * args.l0
    if hi > 0.4 * args.l0:
        print(f" WARNING: sqrt(alpha') upper {hi:.3f} > 0.4 l0: barrier engages the initial core at t=0")
    if lo >= hi:
        raise SystemExit(f" sweep band empty: sqrt(alpha') lower {lo:.3f} >= upper {hi:.3f}; "
                         f"raise n or l0, or pass --sqrt-a-lo/--sqrt-a-hi")
    decades = 2.0 * np.log10(hi / lo)
    if decades < 0.3:
        print(f" WARNING: only {decades:.2f} decades in alpha' -- exponents will be poorly constrained")
    alphas = np.logspace(np.log10(lo), np.log10(hi), args.points) ** 2
    print(f"\n[2] BARRIER SWEEP  alpha' in [{alphas.min():.3e}, {alphas.max():.3e}]  ({decades:.2f} decades)")
    print(f" {'alpha_p':>9} {'tau_c meas':>10} {'tau_c pred':>10} {'l meas':>7} {'l pred':>7}"
          f" {'u meas':>8} {'u pred':>8} {'w meas':>8} {'w pred':>8} {'B/F':>6} arrested")
    runs = []
    for a in alphas:
        r = run_core(args.n, args.nu, args.l0, float(a), l_min_cells=args.l_min_cells)
        runs.append(r); p = r["predicted"]
        print(f" {a:>9.3e} {r['tau_at_arrest']:>10.2f} {p['tau_c']:>10.2f} {r['ell_at_arrest']:>7.3f}"
              f" {p['ell']:>7.3f} {r['u_at_arrest']:>8.4f} {p['u']:>8.4f} {r['omega_at_arrest']:>8.3f}"
              f" {p['omega']:>8.3f} {r['barrier_over_forcing_at_arrest']:>6.2f} {r['arrested_before_end']}")

    law = pooled_bf_law(runs, args.nu)
    print(f"\n[3] MECHANISM  B/F = C alpha'/(nu tau) pooled over {law.get('n_samples')} samples"
          f" ({law.get('x_range_decades', 0):.2f} decades):")
    if "slope" in law:
        print(f"    slope {law['slope']:+.3f} (predicted +1.000), R^2 {law['r_squared']:.3f},"
              f" prefactor C = {law['prefactor_C']:.3f}")
        if "C_spread_rel" in law:
            print(f"    COLLAPSE: per-run C spread {100*law['C_spread_rel']:.1f}% -> "
                  f"{'B/F is a function of alpha\'/(nu tau) alone' if law['collapses'] else 'NO collapse'};"
                  f" per-run local slopes {['%.2f' % s for s in law['per_run_local_slope']]}")
        print(f"    => actual crossover tau_c = C alpha'/nu = {law['prefactor_C']:.2f} alpha'/nu;"
              f" for the largest alpha' here that is tau = {law['prefactor_C']*alphas.max()/args.nu:.1f}"
              f" against a window floor of tau_min = {l_min**2/args.nu:.1f}")
    lags = [r["lag_at_end"] for r in runs]
    print(f"    core lag behind target at window end, per alpha': {['%.1f%%' % (100*x) for x in lags]}")

    usable = [r for r in runs if r["arrested_before_end"]]
    fits = {}
    if len(usable) >= 3:
        a_arr = np.array([r["alpha_prime"] for r in usable])
        for key, pred in (("tau_at_arrest", 1.0), ("u_at_arrest", -0.5),
                          ("omega_at_arrest", -1.0), ("ell_at_arrest", 0.5)):
            f = fit_power_law(a_arr, np.array([r[key] for r in usable]))
            f["predicted_exponent"] = pred
            if "ci95" in f:
                f["consistent"] = bool(f["ci95"][0] <= pred <= f["ci95"][1])
            fits[key] = f
        print(f"\n {'quantity':<16}{'fitted':>8}{'pred':>7}{'R^2':>7}  95% CI            consistent")
        for k, f in fits.items():
            if "ci95" in f:
                print(f" {k:<16}{f['exponent']:>+8.3f}{f['predicted_exponent']:>+7.2f}{f['r_squared']:>7.3f}"
                      f"  [{f['ci95'][0]:+.2f}, {f['ci95'][1]:+.2f}]   {f['consistent']}")
    else:
        print(f"\n only {len(usable)} arrested runs; need >= 3 to fit")

    # premise check, now expected to HOLD
    re_core = [r["u_at_arrest"] * r["ell_at_arrest"] / args.nu for r in usable]
    print(f"\n PREMISE  Re_core at arrest: {['%.2f' % x for x in re_core]}  (law assumes ~1)")

    out = {"config": vars(args), "alpha_models_inert": inert, "control": {k: v for k, v in ctrl.items() if k != "series"},
           "control_ok": ctrl_ok, "runs": [{k: v for k, v in r.items() if k != "series"} for r in runs],
           "series": {str(r["alpha_prime"]): r["series"] for r in [ctrl] + runs},
           "mechanism_bf_law": law, "fits": fits, "Re_core_at_arrest": re_core}
    path = OUT / f"forced_core_{args.n}{('_' + args.tag) if args.tag else ''}.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\n written to {path}")


if __name__ == "__main__":
    main()
