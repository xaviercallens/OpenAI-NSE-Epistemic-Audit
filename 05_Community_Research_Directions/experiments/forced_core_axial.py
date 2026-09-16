"""
Direction 1, stage 2: a forced core WITH axial structure, so the transport gates act.

On the z-invariant swirl column of forced_core.py every alpha-model nonlinearity
is a pure gradient and projects to zero (verified ~1e-7), so that bed tests only
the dissipative barrier. The OpenAI core has an axial scale and an axial
velocity; the swirl-axial coupling makes N(U) != 0, and then Leray-alpha and
LANS-alpha have something to gate.

Target (h = 0)
--------------
Swirl column exactly as ForcedCore (vorticity Gaussian, l_r^2 = nu tau, fixed
Gamma so Re_core = 1), PLUS an axisymmetric meridional cell from a Stokes
streamfunction, solenoidal by construction:

    Psi(r,z,t) = W(t) r^2 exp(-r^2/l^2) sin(k_z z),
    u_r = -(1/r) d_z Psi = -W k_z r e^{-r^2/l^2} cos(k_z z),
    u_z =  (1/r) d_r Psi =  2 W e^{-r^2/l^2} (1 - r^2/l^2) sin(k_z z),

with l(t) = sqrt(nu tau) and W = nu/(2 l) so that u_z,max = nu/l (axial Re = 1).

LIMITATION, stated plainly: k_z = 1 is one wavelength in the 2pi box, so the
AXIAL scale does not collapse -- only the radial one does. A collapsing l_z
needs a localized axial envelope (or a shrinking box) and is left as follow-up.

Forcing: the residual of the target under plain Navier-Stokes, with d_t U by a
central finite difference in time of the analytic target (checked against a
second step). The SAME forcing is applied to every model.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from spectral3d import PseudoSpectralNavierStokes3D
from forced_core import ForcedCore

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)


class AxialForcedCore:
    """Swirl column + meridional cell, and the forcing that sustains both."""

    def __init__(self, solver: PseudoSpectralNavierStokes3D, nu: float, l0: float,
                 k_z: int = 1, axial_re: float = 1.0, fd_frac: float = 1e-4):
        self.s = solver
        self.nu, self.l0, self.k_z, self.axial_re = nu, l0, k_z, axial_re
        self.fd_frac = fd_frac
        self.swirl = ForcedCore(solver, nu, l0)
        self.T = self.swirl.T
        self.gamma = self.swirl.gamma
        x, y, z = solver.grid()
        self.xp, self.yp, self.z = x - np.pi, y - np.pi, z
        self.r2 = self.xp**2 + self.yp**2
        self.ref = self.swirl.ref
        self._fcache: dict = {}

    # -- target -------------------------------------------------------------
    def ell(self, t: float) -> float:
        return self.swirl.ell(t)

    def meridional(self, t: float) -> np.ndarray:
        l = self.ell(t)
        W = self.axial_re * self.nu / (2.0 * l)
        e = np.exp(-self.r2 / l**2)
        c, s_ = np.cos(self.k_z * self.z), np.sin(self.k_z * self.z)
        ur_over_r = -W * self.k_z * e * c
        ux, uy = ur_over_r * self.xp, ur_over_r * self.yp
        uz = 2.0 * W * e * (1.0 - self.r2 / l**2) * s_
        return np.stack([ux, uy, uz])

    def target_unprojected(self, t: float) -> np.ndarray:
        u_hat = self.swirl.target(t)
        m = self.meridional(t)
        return u_hat + np.stack([np.fft.fftn(m[i]) for i in range(3)])

    def target(self, t: float) -> np.ndarray:
        return self.s.project_leray(self.target_unprojected(t))

    def target_dt(self, t: float, frac: float | None = None) -> np.ndarray:
        d = (frac if frac is not None else self.fd_frac) * (self.T - t)
        return (self.target(t + d) - self.target(t - d)) / (2.0 * d)

    def forcing(self, t: float) -> np.ndarray:
        key = round(float(t), 12)
        if key in self._fcache:
            return self._fcache[key]
        U = self.target(t)
        f = self.ref.project_leray(self.target_dt(t) - self.ref.nonlinear(U) - self.ref.diss_symbol * U)
        if len(self._fcache) > 64:
            self._fcache.clear()
        self._fcache[key] = f
        return f

    # -- diagnostics --------------------------------------------------------
    def ell_from_moment(self, u_hat: np.ndarray, nslices: int = 4) -> float:
        """Enstrophy-weighted swirl-core radius, averaged over z slices."""
        s = self.s
        wz = np.fft.ifftn(1j * (s.kx * u_hat[1] - s.ky * u_hat[0])).real
        wz = wz + self.gamma / (4.0 * np.pi**2)
        r2 = self.r2[:, :, 0]
        vals = []
        for iz in np.linspace(0, s.n - 1, nslices).astype(int):
            w2 = wz[:, :, iz] ** 2
            den = float(np.sum(w2))
            if den > 0:
                vals.append(np.sqrt(2.0 * np.sum(w2 * r2) / den))
        return float(np.mean(vals)) if vals else float("inf")

    def energy_split(self, u_hat: np.ndarray) -> tuple[float, float]:
        """(swirl energy, meridional energy) per unit volume."""
        u = np.stack([np.fft.ifftn(u_hat[i]).real for i in range(3)])
        r = np.sqrt(np.maximum(self.r2, 1e-30))
        ut = (-self.yp * u[0] + self.xp * u[1]) / r
        ur = (self.xp * u[0] + self.yp * u[1]) / r
        n3 = self.s.n**3
        return 0.5 * float(np.sum(ut**2)) / n3, 0.5 * float(np.sum(ur**2 + u[2] ** 2)) / n3

    def rel_l2_error(self, u_hat: np.ndarray, t: float) -> float:
        U = self.target(t)
        return float(np.sqrt(np.sum(np.abs(u_hat - U) ** 2) / np.sum(np.abs(U) ** 2)))


def make_solver(n: int, nu: float, model: str, alpha: float | None) -> PseudoSpectralNavierStokes3D:
    if model == "nse":
        return PseudoSpectralNavierStokes3D(n_grid=n, nu=nu)
    if model in ("leray", "lans"):
        return PseudoSpectralNavierStokes3D(n_grid=n, nu=nu, leray_alpha=alpha, alpha_model=model)
    if model == "barrier":
        return PseudoSpectralNavierStokes3D(n_grid=n, nu=nu, alpha_prime=alpha**2, dissipation="barrier")
    raise ValueError(model)


def nonlinearity_check(n: int, nu: float, l0: float, alpha: float = 0.3, t_frac: float = 0.3) -> dict:
    base = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu)
    core = AxialForcedCore(base, nu, l0)
    t = t_frac * core.T
    U = core.target(t)
    scale = float(np.sqrt(np.sum(np.abs(U) ** 2)) * np.sqrt(np.max(base.k_sq)))
    out = {"nse_nonlinear_rel": float(np.sqrt(np.sum(np.abs(base.nonlinear(U)) ** 2)) / scale)}
    for m in ("leray", "lans"):
        s = make_solver(n, nu, m, alpha)
        out[f"{m}_nonlinear_rel"] = float(np.sqrt(np.sum(np.abs(s.nonlinear_term(U)) ** 2)) / scale)
    out["div_rel_before_projection"] = base.divergence_report(core.target_unprojected(t))["div_l2_relative"]
    out["div_rel_after_projection"] = base.divergence_report(U)["div_l2_relative"]
    d1, d2 = core.target_dt(t, 1e-4), core.target_dt(t, 5e-5)
    out["fd_consistency_rel"] = float(np.sqrt(np.sum(np.abs(d1 - d2) ** 2) / np.sum(np.abs(d1) ** 2)))
    out["not_inert"] = bool(min(out["leray_nonlinear_rel"], out["lans_nonlinear_rel"]) > 1e-5)
    return out


def run_axial(n: int, nu: float, l0: float, model: str, alpha: float | None,
              l_min_cells: float = 3.0, cfl: float = 0.4, tau_frac: float = 0.02) -> dict:
    s = make_solver(n, nu, model, alpha)
    core = AxialForcedCore(s, nu, l0)
    l_min = l_min_cells * 2.0 * np.pi / n
    t_end = core.T - l_min**2 / nu
    rec = {k: [] for k in ("t", "tau", "ell_meas", "ell_target", "u_max", "u_target",
                           "rel_l2_error", "E_swirl", "E_merid", "E_swirl_target", "E_merid_target")}
    u = core.target(0.0)
    t, step, t0 = 0.0, 0, time.time()
    while t < t_end:
        tau = core.T - t
        h = min(s.cfl_dt(u, cfl), tau_frac * tau, t_end - t)
        u = s.ifrk4_step(u, h, t=t, forcing=core.forcing)
        t += h
        step += 1
        if step % 2 == 0 or t >= t_end:
            es, em = core.energy_split(u)
            Ut = core.target(t)
            ets, etm = core.energy_split(Ut)
            rec["t"].append(t); rec["tau"].append(core.T - t)
            rec["ell_meas"].append(core.ell_from_moment(u)); rec["ell_target"].append(core.ell(t))
            rec["u_max"].append(s.max_velocity(u)); rec["u_target"].append(s.max_velocity(Ut))
            rec["rel_l2_error"].append(core.rel_l2_error(u, t))
            rec["E_swirl"].append(es); rec["E_merid"].append(em)
            rec["E_swirl_target"].append(ets); rec["E_merid_target"].append(etm)
            if not np.isfinite(rec["u_max"][-1]):
                raise FloatingPointError("diverged")
    R = {k: np.asarray(v) for k, v in rec.items()}
    dl = np.gradient(R["ell_meas"], R["t"]) if len(R["t"]) > 2 else np.array([np.nan])
    i_min = int(np.argmin(R["ell_meas"]))
    return {
        "model": model, "alpha": alpha, "n": n, "nu": nu, "l0": l0, "T": core.T,
        "steps": step, "wall_s": round(time.time() - t0, 1), "l_min_target": l_min,
        "max_rel_l2_error": float(np.max(R["rel_l2_error"])),
        "final_rel_l2_error": float(R["rel_l2_error"][-1]),
        "lag_at_end": float(R["ell_meas"][-1] / R["ell_target"][-1] - 1.0),
        "ell_min": float(R["ell_meas"][i_min]),
        "ell_min_before_end": bool(i_min < len(R["t"]) - 1),
        "dl_dt_end_over_target": float(dl[-1] / np.gradient(R["ell_target"], R["t"])[-1]) if len(R["t"]) > 2 else float("nan"),
        "u_max_end": float(R["u_max"][-1]), "u_target_end": float(R["u_target"][-1]),
        "u_ratio_end": float(R["u_max"][-1] / R["u_target"][-1]),
        "merid_fraction_end": float(R["E_merid"][-1] / (R["E_merid"][-1] + R["E_swirl"][-1])),
        "merid_fraction_target_end": float(R["E_merid_target"][-1] / (R["E_merid_target"][-1] + R["E_swirl_target"][-1])),
        "series": {k: v.tolist() for k, v in R.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=32)
    ap.add_argument("--nu", type=float, default=0.01)
    ap.add_argument("--l0", type=float, default=1.0)
    ap.add_argument("--alphas", type=float, nargs="+", default=[0.25, 0.35, 0.5])
    ap.add_argument("--l-min-cells", type=float, default=3.0)
    args = ap.parse_args()
    l_min = args.l_min_cells * 2 * np.pi / args.n

    print("=" * 78)
    print(" FORCED CORE WITH AXIAL STRUCTURE (stage 2): gates vs drain on the same target")
    print("=" * 78)
    print(f" n={args.n}^3 nu={args.nu} l0={args.l0} T={args.l0**2/args.nu:.0f} window l in ({l_min:.3f}, {args.l0})"
          f"  k_z=1 (axial scale NOT collapsing -- stated limitation)")

    print("\n[0] nonlinearity / solenoidality / finite-difference checks (n=24)")
    chk = nonlinearity_check(24, args.nu, args.l0)
    for k, v in chk.items():
        print(f"    {k}: {v:.3e}" if isinstance(v, float) else f"    {k}: {v}")

    print("\n[1] CONTROL (plain NSE, same forcing)")
    ctrl = run_axial(args.n, args.nu, args.l0, "nse", None, l_min_cells=args.l_min_cells)
    print(f"    max rel L2 error {ctrl['max_rel_l2_error']:.3e} (final {ctrl['final_rel_l2_error']:.3e}),"
          f" {ctrl['steps']} steps, {ctrl['wall_s']}s  -> {'PASS' if ctrl['max_rel_l2_error'] < 1e-3 else 'FAIL'} (<1e-3)")

    print("\n[2] GATES (Leray-a, LANS-a) and DRAIN (barrier, sqrt(a')=a) on the SAME target/forcing")
    print(f" {'model':<8}{'alpha':>6}{'lag_end':>9}{'l_min':>7}{'l_tgt':>7}{'stall':>7}{'u/u_tgt':>9}"
          f"{'merid%':>8}{'tgt%':>6}{'L2err':>9}{'s':>5}")
    runs = []
    for model in ("leray", "lans", "barrier"):
        for a in args.alphas:
            r = run_axial(args.n, args.nu, args.l0, model, a, l_min_cells=args.l_min_cells)
            runs.append(r)
            print(f" {model:<8}{a:>6.2f}{100*r['lag_at_end']:>8.1f}%{r['ell_min']:>7.3f}{r['l_min_target']:>7.3f}"
                  f"{r['dl_dt_end_over_target']:>7.2f}{r['u_ratio_end']:>9.3f}"
                  f"{100*r['merid_fraction_end']:>7.1f}%{100*r['merid_fraction_target_end']:>5.1f}%"
                  f"{r['max_rel_l2_error']:>9.2e}{r['wall_s']:>5.0f}")

    # computed conclusions
    def series(model):
        return [r for r in runs if r["model"] == model]
    concl = {}
    for m in ("leray", "lans", "barrier"):
        rs = series(m)
        lags = [r["lag_at_end"] for r in rs]
        concl[m] = {
            "lag_positive_all": bool(all(x > 0 for x in lags)),
            "lag_increases_with_alpha": bool(all(np.diff(lags) > 0)),
            "any_arrest_in_window": bool(any(r["ell_min_before_end"] for r in rs)),
            "stall_ratio_end": [r["dl_dt_end_over_target"] for r in rs],
            "merid_fraction_end": [r["merid_fraction_end"] for r in rs],
        }
    print("\n computed conclusions:")
    for m, c in concl.items():
        print(f"  {m:<8} lag>0 all: {c['lag_positive_all']}  lag grows with alpha: {c['lag_increases_with_alpha']}"
              f"  arrest in window: {c['any_arrest_in_window']}  dl/dt / target at end: {['%.2f' % x for x in c['stall_ratio_end']]}")
    print(f"  window floor l_min={l_min:.3f} vs largest alpha {max(args.alphas)}: "
          f"{'arrest scale l~alpha lies INSIDE the window' if max(args.alphas) > l_min else 'arrest scale l~alpha lies BELOW the window floor -- arrest cannot be observed at this n'}")

    out = {"config": vars(args), "checks": chk,
           "control": {k: v for k, v in ctrl.items() if k != "series"},
           "runs": [{k: v for k, v in r.items() if k != "series"} for r in runs],
           "series": {"nse": ctrl["series"], **{f"{r['model']}_{r['alpha']}": r["series"] for r in runs}},
           "conclusions": concl}
    path = OUT / f"forced_core_axial_{args.n}.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\n written to {path}")


if __name__ == "__main__":
    main()
