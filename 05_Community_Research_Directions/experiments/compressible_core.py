#!/usr/bin/env python3
"""Compressible / thermal test of the forced collapsing core (Locks C and T).

The forced-core bed (forced_core.py) drives a time-reversed Lamb-Oseen column, l^2 = nu*tau, with
the residual of the *incompressible, constant-viscosity* Navier-Stokes equations -- the analogue of
OpenAI's force, which is likewise built for that model. The kinetic test (kinetic_lock_rs) found that
an isothermal BGK gas with constant collision time does not arrest it. That model has mu ~ rho, so
nu is constant: it excludes by construction the feedback a real gas has, mu independent of density,
hence nu_local = mu/rho rising as the core evacuates, and it has no energy equation at all.

Here the same force is applied to an axisymmetric, z-invariant compressible Navier-Stokes-Fourier
fluid, 1D in radius (fields ln rho, u_r, u_theta, T), and the physics is switched on one piece at a
time:

    mu_law  'rho'    mu = mu_inf rho/rho_inf  (nu constant: the BGK-constant-tau analogue)
            'const'  mu = mu_inf              (gas at fixed temperature: mu independent of rho)
            'T'      mu = mu_inf (T/T_inf)^0.76   (air)
    thermo  'isothermal'   T fixed
            'full'         energy equation: compression work, conduction (Pr = 0.71), viscous heating
            'noheat'       as 'full' with the viscous heating switched off (isolates expansion cooling)
    force   'mass'    prescribed field is an acceleration (force per unit mass)
            'volume'  prescribed field is a force per unit volume at rho_inf

Prediction (quasi-steady, isothermal, mu const, per-mass force). Cyclostrophic balance gives the exact
hole ln(rho_0/rho_inf) = -(ln 2/0.63817^2) Ma^2 = -1.702 Ma^2, Ma the peak swirl Mach number. The
force supplies anti-diffusion -(5/4) nu_inf Lap U against a real diffusion nu_local Lap u, so the net
diffusion at the centre changes sign when nu_local > (5/4) nu_inf, i.e. rho_0 < 0.8 rho_inf:
Ma_c = 0.362, l_c = Re l_star / Ma_c = 2.76 Re l_star. With a per-volume force both terms scale with
1/rho and there is no such sign change.

Units: l_star = nu_inf/c_inf = 1, c_inf = 1 (isothermal sound speed for 'isothermal', adiabatic
otherwise), rho_inf = T_inf = 1. Target Mach number is Re/l.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

PEAK = 0.6381726863389515      # max of (1 - exp(-x^2))/x
HOLE_K = np.log(2.0) / PEAK ** 2   # ln(rho0/rho_inf) = -HOLE_K Ma^2 (isothermal, quasi-steady)


@dataclass
class Config:
    re: float = 1.0
    mu_law: str = "const"
    thermo: str = "isothermal"
    force: str = "mass"
    n: int = 400
    l_start: float = 40.0        # in units of Re*l_star (start Mach = 1/l_start)
    l_end: float = 0.5           # stop when target l reaches this, in units of Re*l_star
    r_max: float = 14.0          # domain radius in units of the start core size
    gamma: float = 1.4
    prandtl: float = 0.71
    mu_exp: float = 0.76
    c_scale: float = 1.0         # >1 raises the sound speed (low-Mach control)
    rtol: float = 1e-7
    atol: float = 1e-9


class Core:
    def __init__(self, cfg: Config):
        self.cfg = c = cfg
        self.nu = 1.0
        self.c0 = c.c_scale
        self.isothermal = c.thermo == "isothermal"
        # gas constant so that the relevant sound speed is c0 at T = 1
        self.R = self.c0 ** 2 if self.isothermal else self.c0 ** 2 / c.gamma
        self.cv = self.R / (c.gamma - 1.0)
        self.cp = c.gamma * self.cv
        self.Gamma = 2.0 * np.pi * self.nu * c.re / PEAK
        self.ls = c.l_start * c.re
        self.T_blow = self.ls ** 2 / self.nu
        self.t_end = self.T_blow - (c.l_end * c.re) ** 2 / self.nu
        # grid: odd map r = a sinh(xi/b); nodes at half-integers so parity gives the axis ghosts
        n = c.n
        rmax = c.r_max * self.ls
        dr0 = 0.04 * c.l_end * c.re * max(1.0, 400.0 / n)     # axis spacing
        b = self._solve_b(n, rmax, dr0)
        a = rmax / np.sinh(n / b)
        xi = np.arange(n) + 0.5
        self.r = a * np.sinh(xi / b)
        self.rh = a * np.sinh(np.arange(n + 1) / b)           # half nodes, rh[0] = 0 (axis)
        self.dr_c = np.diff(self.rh)                          # cell widths
        self.dr_h = np.empty(n + 1)                           # node-to-node distance across a half node
        self.dr_h[1:-1] = np.diff(self.r)
        self.dr_h[0] = 2.0 * self.r[0]
        self.dr_h[-1] = self.dr_h[-2]
        # exact cell measures for the finite-volume divergences (matter next to the axis)
        self.vol2 = 0.5 * np.diff(self.rh ** 2)               # int r dr
        self.vol4 = np.diff(self.rh ** 4) / 4.0               # int r^3 dr
        self.sponge = 0.5 * (1 + np.tanh((self.r - 0.8 * rmax) / (0.04 * rmax))) * (4.0 * self.c0 / rmax)
        self.nvar = 4

    @staticmethod
    def _solve_b(n, rmax, dr0):
        lo, hi = 1.0, 1e6
        for _ in range(200):
            b = np.sqrt(lo * hi)
            a = rmax / np.sinh(n / b)
            if a * np.sinh(0.5 / b) * 2 > dr0:   # axis spacing too coarse -> more stretching
                hi = b
            else:
                lo = b
        return b

    # ---- target and its force -------------------------------------------------------------------
    def ell(self, t):
        return np.sqrt(self.nu * max(self.T_blow - t, 1e-300))

    def target_u(self, t, r=None):
        r = self.r if r is None else r
        l = self.ell(t)
        return self.Gamma / (2 * np.pi * r) * (-np.expm1(-(r / l) ** 2))

    def force_theta(self, t):
        """Residual of incompressible constant-nu NSE for the target: f = -(5/4) nu d(omega)/dr."""
        l = self.ell(t)
        om = self.Gamma / (np.pi * l * l) * np.exp(-(self.r / l) ** 2)
        return 2.5 * self.nu * self.r * om / (l * l)

    # ---- operators --------------------------------------------------------------------------------
    def _ghost(self, f, parity):
        """values extended by one ghost at each end: axis by parity, outer by extrapolation."""
        return np.concatenate(([parity * f[0]], f, [f[-1]]))

    def _ddr(self, f, parity):
        g = self._ghost(f, parity)
        rr = np.concatenate(([-self.r[0]], self.r, [2 * self.r[-1] - self.r[-2]]))
        return (g[2:] - g[:-2]) / (rr[2:] - rr[:-2])

    def _half(self, f, parity):
        g = self._ghost(f, parity)
        return 0.5 * (g[1:] + g[:-1])                # at rh[0..n]

    def _dhalf(self, f, parity):
        g = self._ghost(f, parity)
        return (g[1:] - g[:-1]) / self.dr_h          # d/dr at half nodes

    def mu(self, rho, T):
        law = self.cfg.mu_law
        if law == "rho":
            return self.nu * rho
        if law == "const":
            return np.full_like(rho, self.nu)
        return self.nu * T ** self.cfg.mu_exp

    def rhs(self, t, y):
        n = self.cfg.n
        s, ur, ut, T = y.reshape(n, 4).T
        rho = np.exp(s)
        r, rh = self.r, self.rh
        p = rho * self.R * T
        mu = self.mu(rho, T)
        mu_h = self._half(mu, +1)
        div = self._ddr(ur, -1) + ur / r
        # half-node quantities
        dur_h = self._dhalf(ur, -1)
        ur_over_r_h = self._half(ur / r, +1)
        div_h = dur_h + ur_over_r_h
        # continuity in ln rho (positivity); mass conservation is then a diagnostic
        ds = -ur * self._ddr(s, +1) - div
        # radial momentum
        trr_h = mu_h * (2 * dur_h - (2.0 / 3.0) * div_h)
        tthth = mu * (2 * ur / r - (2.0 / 3.0) * div)
        visc_r = (rh[1:] * trr_h[1:] - rh[:-1] * trr_h[:-1]) / self.vol2 - tthth / r
        dur = -ur * self._ddr(ur, -1) + ut ** 2 / r - self._ddr(p, +1) / rho + visc_r / rho
        # azimuthal momentum: (1/r^2) d/dr ( r^3 mu dOmega/dr ), Omega = u_theta/r, evaluated as
        # r * [(1/r^3) d/dr(...)] with the r^3 cell measure: exact for Omega = a + b r^2 at the axis
        dom_h = self._dhalf(ut / r, +1)
        G = rh ** 3 * mu_h * dom_h
        visc_t = r * (G[1:] - G[:-1]) / self.vol4
        f = self.force_theta(t)
        acc = f if self.cfg.force == "mass" else f / rho
        dut = -ur * self._ddr(ut, -1) - ur * ut / r + visc_t / rho + acc
        # energy
        if self.isothermal:
            dT = np.zeros(n)
        else:
            k_h = mu_h * self.cp / self.cfg.prandtl
            q = rh * k_h * self._dhalf(T, +1)
            cond = (q[1:] - q[:-1]) / self.vol2
            phi = 0.0
            if self.cfg.thermo == "full":
                shear = r * self._ddr(ut / r, +1)
                phi = mu * (2 * self._ddr(ur, -1) ** 2 + 2 * (ur / r) ** 2 + shear ** 2 - (2.0 / 3.0) * div ** 2)
            dT = -ur * self._ddr(T, +1) + (-p * div + cond + phi) / (rho * self.cv)
        # outer sponge towards the steady potential-vortex far field
        sg = self.sponge
        dur -= sg * ur
        ds -= sg * (s - self.s_far)
        if not self.isothermal:
            dT -= sg * (T - 1.0)
        return np.column_stack([ds, dur, dut, dT]).ravel()

    # ---- initial state and diagnostics -----------------------------------------------------------
    def initial(self):
        u = self.target_u(0.0)
        # isothermal cyclostrophic balance: d ln rho/dr = u^2/(R T r), integrated inward from rho = 1
        integrand = u ** 2 / (self.R * self.r)
        tail = np.concatenate((np.cumsum((0.5 * (integrand[1:] + integrand[:-1]) * np.diff(self.r))[::-1])[::-1], [0.0]))
        s = -tail
        self.s_far = s.copy()
        n = self.cfg.n
        return np.column_stack([s, np.zeros(n), u, np.ones(n)]).ravel()

    def core_size(self, ut):
        """Enstrophy-weighted second moment, sqrt(2<r^2>) = l for a Gaussian core, on a window of
        4 l iterated to self-consistency (round-off vorticity at r >> l, weighted by r^3, otherwise
        dominates the moment). Seeded from the radius of peak swirl, r_peak = 1.1209 l."""
        om = self._ddr(self.r * ut, +1) / self.r      # r*u_theta is even in r
        w = om ** 2 * self.r * self.dr_c
        l = self.r[int(np.argmax(np.abs(ut)))] / 1.1209
        for _ in range(8):
            m = self.r < 4.0 * l
            l_new = np.sqrt(2.0 * np.sum((w * self.r ** 2)[m]) / np.sum(w[m]))
            if abs(l_new / l - 1.0) < 1e-10:
                break
            l = l_new
        return l

    def diagnostics(self, t, y):
        n = self.cfg.n
        s, ur, ut, T = y.reshape(n, 4).T
        rho = np.exp(s)
        l_meas, l_tgt = self.core_size(ut), self.core_size(self.target_u(t))
        c_loc = np.sqrt((1.0 if self.isothermal else self.cfg.gamma) * self.R * T)
        i = int(np.argmax(np.abs(ut)))
        mu0 = self.mu(rho, T)[0]
        vol = 2 * np.pi * self.r * self.dr_c
        inner = self.r < 0.7 * self.r[-1]
        return {
            "t": t, "tau": self.T_blow - t, "l_target": self.ell(t), "l_meas": l_meas, "l_ref": l_tgt,
            "lag": l_meas / l_tgt - 1.0, "u_max": float(np.abs(ut[i])), "u_target_max": PEAK * self.Gamma / (2 * np.pi * self.ell(t)),
            "mach_target": self.cfg.re / self.ell(t) / self.c0, "mach_local": float(np.max(np.abs(ut) / c_loc)),
            "rho0": float(rho[0]), "T0": float(T[0]), "T_max": float(T.max()), "nu0_over_nu": float(mu0 / rho[0] / self.nu),
            "ur_max_over_c": float(np.max(np.abs(ur)) / self.c0), "mass_inner": float(np.sum((rho * vol)[inner])),
            "kn_local": float(mu0 / rho[0] / np.sqrt(T[0]) / l_meas),   # lambda_local/l with lambda ~ nu/c
        }

    def run(self, n_samples=240, verbose=True):
        y0 = self.initial()
        # sample uniformly in ln(tau) so the late collapse is resolved
        taus = np.geomspace(self.T_blow, self.T_blow - self.t_end, n_samples)
        ts = self.T_blow - taus
        ts[0] = 0.0
        rec, y, t0w = [self.diagnostics(0.0, y0)], y0, time.time()
        status = "reached_l_end"
        for ta, tb in zip(ts[:-1], ts[1:]):
            sol = solve_ivp(self.rhs, (ta, tb), y, method="LSODA", lband=7, uband=7,
                            rtol=self.cfg.rtol, atol=self.cfg.atol)
            if not sol.success or not np.all(np.isfinite(sol.y[:, -1])):
                status = f"integrator_stopped: {sol.message}"
                break
            y = sol.y[:, -1]
            d = self.diagnostics(tb, y)
            rec.append(d)
            if d["lag"] > 3.0 or d["rho0"] < 1e-6:
                status = "core_lost_target" if d["lag"] > 3.0 else "core_evacuated"
                break
        if verbose:
            print(f"   {status}; {len(rec)} samples; {time.time() - t0w:.0f} s")
        return rec, status


def first_crossing(rec, key, level, x="l_target"):
    """x at which rec[key] first exceeds level (log-linear interpolation); None if never."""
    for a, b in zip(rec[:-1], rec[1:]):
        if a[key] <= level < b[key]:
            w = (level - a[key]) / (b[key] - a[key])
            return float(np.exp(np.log(a[x]) + w * (np.log(b[x]) - np.log(a[x]))))
    return None


def summarize(cfg: Config, rec, status):
    re = cfg.re
    l10 = first_crossing(rec, "lag", 0.10)
    l50 = first_crossing(rec, "lag", 0.50)
    out = {
        "config": asdict(cfg), "status": status,
        "l_at_lag10_over_Re_lstar": None if l10 is None else l10 / re,
        "l_at_lag50_over_Re_lstar": None if l50 is None else l50 / re,
        "mach_target_at_lag10": None if l10 is None else re / l10 / cfg.c_scale,
        "max_lag": max(r["lag"] for r in rec), "min_lag": min(r["lag"] for r in rec),
        "min_l_meas_over_Re_lstar": min(r["l_meas"] for r in rec) / re,
        "l_target_end_over_Re_lstar": rec[-1]["l_target"] / re,
        "rho0_end": rec[-1]["rho0"], "T0_end": rec[-1]["T0"], "T_max": max(r["T_max"] for r in rec),
        "mass_drift_inner": abs(rec[-1]["mass_inner"] / rec[0]["mass_inner"] - 1.0),
        "series": {k: [r[k] for r in rec] for k in rec[0]},
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--re", type=float, default=1.0)
    ap.add_argument("--mu-law", default="const", choices=["rho", "const", "T"])
    ap.add_argument("--thermo", default="isothermal", choices=["isothermal", "full", "noheat"])
    ap.add_argument("--force", default="mass", choices=["mass", "volume"])
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--c-scale", type=float, default=1.0)
    ap.add_argument("--l-end", type=float, default=0.5)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cfg = Config(re=a.re, mu_law=a.mu_law, thermo=a.thermo, force=a.force, n=a.n, c_scale=a.c_scale, l_end=a.l_end)
    print(f"compressible core: {cfg}")
    rec, status = Core(cfg).run()
    out = summarize(cfg, rec, status)
    print({k: v for k, v in out.items() if k not in ("series", "config")})
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
