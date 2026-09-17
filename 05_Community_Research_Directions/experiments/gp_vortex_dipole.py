#!/usr/bin/env python3
"""Gross-Pitaevskii vortex dipole: does a quantum fluid lock the velocity of a collapsing vortex pair?

Classical (Euler) point-vortex pair, circulation +-kappa, separation d: U = kappa/(2 pi d), unbounded as
d -> 0. In a quantum fluid kappa = h/m is quantized, so u r = hbar/m around each vortex (the "quantum
Reynolds number" u r/(hbar/m) is identically 1, the diffusive-route condition of the OpenAI core), and the
GP equation carries the microscopic length xi = hbar/(sqrt(2) m c), the analogue of l* = nu/c with hbar/m in
place of nu. Jones & Roberts (1982, J. Phys. A 15, 2599) found that the 2D pair branch stays below c and
turns into rarefaction pulses as U -> c. This script measures U(d) numerically.

Units: hbar = m = 1, g = 1, background density rho_inf = 1, so c = 1, xi = 1/sqrt(2), kappa = 2 pi;
lengths are reported in units of xi, velocities in units of c.

Equation: i psi_t = -1/2 lap psi + (|psi|^2 - 1) psi, doubly periodic box, Strang split-step Fourier.

Periodic initial state. A single vortex dipole cannot be written as an exactly periodic psi with zero mean
flow (the phase jumps by 2 pi d/Lx across the box). We therefore place TWO dipoles: dipole A (+ at
Lx/4 - d/2, - at Lx/4 + d/2) and dipole B, its charge-flipped copy shifted by Lx/2 (- at 3Lx/4 - d/2,
+ at 3Lx/4 + d/2). B moves opposite to A, the phase jumps cancel exactly, and the configuration has zero
mean flow. The phase of each vortex is arg theta_1(pi (z - z_j)/Lx | tau = i Ly/Lx) (Jacobi theta), which is
the exact doubly periodic point-vortex phase; the classical periodic translation speed of A follows from
the same functions (classical_periodic_U), so image effects are accounted for in the comparison.
Amplitude: product of r/sqrt(r^2 + 1) core profiles (minimum-image r). The state is then relaxed in
imaginary time with the phase re-imposed after every step, which fills in the cores without moving them.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import scipy.fft as sfft

OUT = Path(__file__).parent / "results"
XI = 1.0 / np.sqrt(2.0)
WORKERS = 4


# ---------------------------------------------------------------------------------------------------------
# Jacobi theta_1 and the doubly periodic vortex phase
# ---------------------------------------------------------------------------------------------------------
def theta1(z, q, nterms=40):
    """theta_1(z|q) = 2 sum_n (-1)^n q^((n+1/2)^2) sin((2n+1) z), complex z."""
    s = np.zeros_like(z, dtype=complex)
    for n in range(nterms):
        c = (-1) ** n * q ** ((n + 0.5) ** 2)
        if abs(c) < 1e-300:
            break
        s += c * np.sin((2 * n + 1) * z)
    return 2.0 * s


def theta1_logderiv(z, q, nterms=40):
    num = np.zeros_like(z, dtype=complex)
    den = np.zeros_like(z, dtype=complex)
    for n in range(nterms):
        c = (-1) ** n * q ** ((n + 0.5) ** 2)
        if abs(c) < 1e-300:
            break
        den += c * np.sin((2 * n + 1) * z)
        num += c * (2 * n + 1) * np.cos((2 * n + 1) * z)
    return num / den


def dipole_pair_positions(d, Lx, Ly, shift=(0.0, 0.0)):
    """Vortex positions (x, y, charge). `shift` moves the whole configuration (used to keep the cores off
    grid nodes, where psi = 0 exactly and the phase is undefined)."""
    y0 = 0.25 * Ly + shift[1]
    sx = shift[0]
    return [
        (0.25 * Lx - 0.5 * d + sx, y0, +1),
        (0.25 * Lx + 0.5 * d + sx, y0, -1),
        (0.75 * Lx - 0.5 * d + sx, y0, -1),
        (0.75 * Lx + 0.5 * d + sx, y0, +1),
    ]


def classical_periodic_U(d, Lx, Ly):
    """Translation speed of point-vortex dipole A in the same doubly periodic 4-vortex configuration
    (kappa = 2 pi, hbar/m = 1). Velocity at vortex 1 = sum over k != 1 of q_k grad arg theta_1."""
    q = np.exp(-np.pi * Ly / Lx)
    vs = dipole_pair_positions(d, Lx, Ly)
    x1 = vs[0][0]
    uy = 0.0
    for xk, _, qk in vs[1:]:
        zeta = np.array([np.pi * (x1 - xk) / Lx + 0j])
        W = theta1_logderiv(zeta, q)[0]
        uy += qk * W.real * np.pi / Lx
    # vortex 2 moves with the same speed by symmetry; report |U|
    return abs(uy)


# ---------------------------------------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------------------------------------
class GP2D:
    def __init__(self, Lx, Ly, dx_target, dt):
        self.nx = int(2 * np.ceil(Lx / dx_target / 2))
        self.ny = int(2 * np.ceil(Ly / dx_target / 2))
        self.Lx, self.Ly = Lx, Ly
        self.dx, self.dy = Lx / self.nx, Ly / self.ny
        self.x = np.arange(self.nx) * self.dx
        self.y = np.arange(self.ny) * self.dy
        self.X, self.Y = np.meshgrid(self.x, self.y)          # arrays indexed [iy, ix]
        kx = 2 * np.pi * sfft.fftfreq(self.nx, d=self.dx)
        ky = 2 * np.pi * sfft.fftfreq(self.ny, d=self.dy)
        self.KX, self.KY = np.meshgrid(kx, ky)
        self.K2 = self.KX ** 2 + self.KY ** 2
        self.set_dt(dt)

    def stable_dt(self, fac=1.5):
        """Split-step Fourier for NLS has a resonance instability when dt k_max^2/2 exceeds pi; we use
        dt = fac / (k_max^2/2) with fac = 1.5 (energy drift ~1e-7 over 20 time units, checked)."""
        return fac / (0.5 * float(self.K2.max()))

    def set_dt(self, dt):
        if dt is None:
            dt = self.stable_dt()
        self.dt = dt
        self.kin = np.exp(-0.5j * self.K2 * dt)

    def fft(self, a):
        return sfft.fft2(a, workers=WORKERS)

    def ifft(self, a):
        return sfft.ifft2(a, workers=WORKERS)

    def evolve(self, psi, nsteps):
        """Strang splitting N(dt/2) K(dt) N(dt/2), consecutive half nonlinear steps merged."""
        dt = self.dt
        psi = psi * np.exp(-0.5j * dt * (np.abs(psi) ** 2 - 1.0))
        for n in range(nsteps):
            psi = self.ifft(self.kin * self.fft(psi))
            h = dt if n < nsteps - 1 else 0.5 * dt
            psi = psi * np.exp(-1j * h * (np.abs(psi) ** 2 - 1.0))
        return psi

    def relax(self, psi, phase_factor, nsteps, dt_im=0.02):
        """Imaginary-time relaxation of the amplitude with the phase re-imposed every step."""
        kin = np.exp(-0.5 * self.K2 * dt_im)
        for _ in range(nsteps):
            psi = psi * np.exp(-0.5 * dt_im * (np.abs(psi) ** 2 - 1.0))
            psi = self.ifft(kin * self.fft(psi))
            psi = psi * np.exp(-0.5 * dt_im * (np.abs(psi) ** 2 - 1.0))
            psi = np.abs(psi) * phase_factor
        return psi

    def energy(self, psi):
        ph = self.fft(psi)
        gx = self.ifft(1j * self.KX * ph)
        gy = self.ifft(1j * self.KY * ph)
        dA = self.dx * self.dy
        ekin = 0.5 * np.sum(np.abs(gx) ** 2 + np.abs(gy) ** 2) * dA
        eint = 0.5 * np.sum((np.abs(psi) ** 2 - 1.0) ** 2) * dA
        return float(ekin + eint)

    def norm(self, psi):
        return float(np.sum(np.abs(psi) ** 2) * self.dx * self.dy)

    def current(self, psi):
        ph = self.fft(psi)
        gx = self.ifft(1j * self.KX * ph)
        gy = self.ifft(1j * self.KY * ph)
        c = np.conj(psi)
        return (c * gx).imag, (c * gy).imag


# ---------------------------------------------------------------------------------------------------------
# Initial state, vortex detection
# ---------------------------------------------------------------------------------------------------------
def initial_dipoles(g: GP2D, d, core=1.0):
    q = np.exp(-np.pi * g.Ly / g.Lx)
    phase = np.ones((g.ny, g.nx), dtype=complex)
    amp = np.ones((g.ny, g.nx))
    for xj, yj, qj in dipole_pair_positions(d, g.Lx, g.Ly, shift=(0.3718 * g.dx, 0.4431 * g.dy)):
        yrel = (g.Y - yj + 0.5 * g.Ly) % g.Ly - 0.5 * g.Ly
        zeta = np.pi * ((g.X - xj) + 1j * yrel) / g.Lx
        t = theta1(zeta, q)
        f = t / np.abs(t)
        phase *= f if qj > 0 else np.conj(f)
        xm = (g.X - xj + 0.5 * g.Lx) % g.Lx - 0.5 * g.Lx
        r2 = xm ** 2 + yrel ** 2
        amp *= np.sqrt(r2 / (r2 + core ** 2))
    return amp * phase, phase


def _wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def find_vortices(g: GP2D, psi):
    """Phase-winding plaquettes, then the zero of the bilinear interpolant of psi on the plaquette."""
    ph = np.angle(psi)
    p00 = ph
    p10 = np.roll(ph, -1, axis=1)
    p11 = np.roll(p10, -1, axis=0)
    p01 = np.roll(ph, -1, axis=0)
    w = (_wrap(p10 - p00) + _wrap(p11 - p10) + _wrap(p01 - p11) + _wrap(p00 - p01)) / (2 * np.pi)
    iy, ix = np.nonzero(np.abs(w) > 0.5)
    out = []
    for jy, jx in zip(iy, ix):
        jx1, jy1 = (jx + 1) % g.nx, (jy + 1) % g.ny
        a = psi[jy, jx]
        b = psi[jy, jx1] - a
        c = psi[jy1, jx] - a
        e = psi[jy1, jx1] - psi[jy, jx1] - psi[jy1, jx] + a
        s = t = 0.5
        for _ in range(20):
            f = a + b * s + c * t + e * s * t
            fs, ft = b + e * t, c + e * s
            J = np.array([[fs.real, ft.real], [fs.imag, ft.imag]])
            try:
                ds, dt_ = np.linalg.solve(J, [-f.real, -f.imag])
            except np.linalg.LinAlgError:
                break
            s, t = s + ds, t + dt_
            if abs(ds) + abs(dt_) < 1e-12:
                break
        s, t = min(max(s, -0.5), 1.5), min(max(t, -0.5), 1.5)
        out.append((g.x[jx] + s * g.dx, g.y[jy] + t * g.dy, int(np.sign(w[jy, jx]))))
    return out


# ---------------------------------------------------------------------------------------------------------
# One run
# ---------------------------------------------------------------------------------------------------------
def default_box(d):
    Lx = max(80 * XI, 10.0 * d)
    Ly = max(60 * XI, 5.0 * d)
    return Lx, Ly


def run_dipole(d_over_xi, dx_over_xi=0.35, box_scale=1.0, dt=None, relax_steps=300, t_run=None,
               sample_every=None, verbose=True, keep_final=False):
    d = d_over_xi * XI
    Lx, Ly = default_box(d)
    Lx, Ly = Lx * box_scale, Ly * box_scale
    g = GP2D(Lx, Ly, dx_over_xi * XI, dt)
    dt = g.dt
    U_cl_free = 1.0 / d
    U_cl_per = classical_periodic_U(d, Lx, Ly)
    if t_run is None:
        t_run = float(np.clip(8 * XI / min(U_cl_per, 0.8), 30.0, 160.0))
    nsteps = int(round(t_run / dt))
    if sample_every is None:
        sample_every = max(1, int(round(0.5 / dt)))
    w0 = time.time()
    psi0, phase = initial_dipoles(g, d)
    E_ansatz = g.energy(psi0)
    psi = g.relax(psi0, phase, relax_steps)
    E0, N0 = g.energy(psi), g.norm(psi)

    ts, ya, xa_sep, rhomin_left, rhomin_left_y, nvort_left = [], [], [], [], [], []
    t = 0.0
    done = 0
    annihilated_at = None
    while done <= nsteps:
        vs = find_vortices(g, psi)
        left = [v for v in vs if v[0] < 0.5 * Lx]
        rho_left = np.abs(psi[:, : g.nx // 2]) ** 2
        k = int(np.argmin(rho_left))
        ts.append(t)
        nvort_left.append(len(left))
        rhomin_left.append(float(rho_left.flat[k]))
        rhomin_left_y.append(float(g.y[k // (g.nx // 2)]))
        if len(left) == 2 and left[0][2] != left[1][2]:
            ya.append(0.5 * (left[0][1] + left[1][1]))
            xa_sep.append(abs(left[0][0] - left[1][0]))
        else:
            ya.append(np.nan)
            xa_sep.append(np.nan)
            if annihilated_at is None and len(left) == 0:
                annihilated_at = t
        if done == nsteps:
            break
        n = min(sample_every, nsteps - done)
        psi = g.evolve(psi, n)
        done += n
        t = done * dt
    E1, N1 = g.energy(psi), g.norm(psi)
    ts, ya, sep = np.array(ts), np.array(ya), np.array(xa_sep)

    res = {
        "d_over_xi": d_over_xi, "dx_over_xi": g.dx / XI, "Lx_over_xi": Lx / XI, "Ly_over_xi": Ly / XI,
        "nx": g.nx, "ny": g.ny, "dt": dt, "t_run": t_run, "relax_steps": relax_steps,
        "U_classical_free": U_cl_free, "U_classical_periodic": U_cl_per,
        "energy_ansatz": E_ansatz, "energy_relaxed": E0, "energy_final": E1,
        "energy_rel_drift": abs(E1 - E0) / abs(E0), "norm_rel_drift": abs(N1 - N0) / N0,
        "relax_energy_removed_fraction": (E_ansatz - E0) / E_ansatz,
        "annihilated": annihilated_at is not None, "annihilation_time": annihilated_at,
    }
    ok = ~np.isnan(ya)
    if ok.sum() >= 8 and not res["annihilated"]:
        tt, yy, ss = ts[ok], np.unwrap(ya[ok] * 2 * np.pi / Ly) * Ly / (2 * np.pi), sep[ok]
        m = tt >= 0.3 * tt[-1]
        p = np.polyfit(tt[m], yy[m], 1)
        resid = yy[m] - np.polyval(p, tt[m])
        # slope uncertainty from residuals
        se = np.sqrt(np.sum(resid ** 2) / max(1, m.sum() - 2) / np.sum((tt[m] - tt[m].mean()) ** 2))
        U = abs(p[0])
        res.update({
            "U": U, "U_stderr": float(se), "U_over_c": U, "travel_over_xi": float(abs(yy[m][-1] - yy[m][0]) / XI),
            "U_over_classical_free": U / U_cl_free, "U_over_classical_periodic": U / U_cl_per,
            "separation_mean_over_xi": float(np.mean(ss[m]) / XI), "separation_drift_over_xi": float((ss[m][-1] - ss[m][0]) / XI),
        })
        d_meas = float(np.mean(ss[m]))
        res["U_classical_free_at_measured_sep"] = 1.0 / d_meas
        res["U_classical_periodic_at_measured_sep"] = classical_periodic_U(d_meas, Lx, Ly)
        res["U_over_classical_periodic_at_measured_sep"] = U / res["U_classical_periodic_at_measured_sep"]
    elif res["annihilated"] or ok.sum() < 8:
        # rarefaction pulse / dark region: speed of the density minimum in the left half after annihilation
        t0 = annihilated_at if annihilated_at is not None else 0.0
        m = ts >= t0 + 0.2 * (ts[-1] - t0)
        yy = np.unwrap(np.array(rhomin_left_y)[m] * 2 * np.pi / Ly) * Ly / (2 * np.pi)
        if m.sum() >= 6:
            p = np.polyfit(ts[m], yy, 1)
            res.update({"pulse_speed_over_c": abs(p[0]), "pulse_rho_min_mean": float(np.mean(np.array(rhomin_left)[m])),
                        "pulse_rho_min_final": rhomin_left[-1]})
        res["U"] = None
    if keep_final:
        jx, jy = g.current(psi)
        rho = np.abs(psi) ** 2
        left = np.s_[:, : g.nx // 2]
        jm = np.hypot(jx, jy)
        with np.errstate(divide="ignore", invalid="ignore"):
            mach = jm / rho ** 1.5
        band = lambda lo, hi: (rho[left] > lo) & (rho[left] < hi)
        res["core_state"] = {
            "rho_min_grid": float(rho[left].min()),
            "mass_current_max": float(jm[left].max()),
            "mach_local_median_rho_0.45_0.55": float(np.median(mach[left][band(0.45, 0.55)])),
            "mach_local_median_rho_0.85_0.95": float(np.median(mach[left][band(0.85, 0.95)])),
            "speed_max_where_rho_gt_0.5": float(np.max((jm / np.maximum(rho, 1e-300))[left][rho[left] > 0.5])),
        }
    res["wall_s"] = time.time() - w0
    if verbose:
        msg = (f"d={d_over_xi:5.2f}xi box {Lx/XI:.0f}x{Ly/XI:.0f}xi grid {g.nx}x{g.ny} dx={g.dx/XI:.3f}xi: ")
        if res.get("U") is not None:
            msg += (f"U={res['U']:.4f}c  U/U_free={res['U_over_classical_free']:.3f}  U/U_per={res['U_over_classical_periodic']:.3f}"
                    f"  U/U_per(d_meas)={res['U_over_classical_periodic_at_measured_sep']:.3f}"
                    f"  travel={res['travel_over_xi']:.1f}xi  sep={res['separation_mean_over_xi']:.2f}xi")
        else:
            msg += f"annihilated={res['annihilated']} t={annihilated_at} pulse_speed={res.get('pulse_speed_over_c')}"
        msg += f"  dE={res['energy_rel_drift']:.1e}  wall={res['wall_s']:.0f}s"
        print(msg, flush=True)
    return res


# ---------------------------------------------------------------------------------------------------------
# Solver checks
# ---------------------------------------------------------------------------------------------------------
def bogoliubov_check(kxi_values=(0.25, 0.5, 1.0, 1.5, 2.0), eps=1e-4, dt=None, L=None):
    """Density mode of psi = 1 + eps cos(k x) oscillates as cos(omega t), omega^2 = k^2 (k^2/4 + 1)."""
    from scipy.optimize import curve_fit
    out = []
    for kxi in kxi_values:
        k = kxi / XI
        n_per = 4
        Lx = n_per * 2 * np.pi / k
        g = GP2D(Lx, 4 * 0.35 * XI, 0.35 * XI, dt)
        dt = g.dt
        psi = (1.0 + eps * np.cos(k * g.X)).astype(complex)
        omega = k * np.sqrt(k * k / 4 + 1)
        T = 6 * 2 * np.pi / omega
        nsamp = 240
        per = max(1, int(round(T / nsamp / dt)))
        ts, amps = [], []
        idx = n_per  # k index along x
        t = 0.0
        for _ in range(nsamp):
            rho_k = np.fft.fft(np.mean(np.abs(psi) ** 2, axis=0))[idx].real * 2 / g.nx
            ts.append(t)
            amps.append(rho_k)
            psi = g.evolve(psi, per)
            t += per * dt
        ts, amps = np.array(ts), np.array(amps)
        (A, w), _ = curve_fit(lambda tt, A, w: A * np.cos(w * tt), ts, amps, p0=[amps[0], omega])
        out.append({"k_xi": kxi, "omega_theory": omega, "omega_measured": abs(w), "rel_err": abs(abs(w) - omega) / omega})
    return out


def conservation_check(d_over_xi=6.0, facs=(3.0, 1.5, 0.75), t_run=20.0):
    out = []
    for fac in facs:
        d = d_over_xi * XI
        Lx, Ly = default_box(d)
        dt = GP2D(Lx, Ly, 0.35 * XI, None).stable_dt(fac)
        r = run_dipole(d_over_xi, dt=dt, t_run=t_run, relax_steps=150, verbose=False)
        out.append({"dt": dt, "dt_kmax2_over_2": fac, "energy_rel_drift": r["energy_rel_drift"], "norm_rel_drift": r["norm_rel_drift"],
                    "U": r.get("U")})
    return out


# ---------------------------------------------------------------------------------------------------------
def plot(json_path, png_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    doc = json.loads(Path(json_path).read_text())
    runs = doc["runs"]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    dd = np.geomspace(0.8, 60, 300)
    for a in ax:
        a.plot(dd, 1.0 / (dd * XI), color="0.35", ls="--", label="classical point-vortex pair: U = kappa/(2 pi d)")
        a.axhline(1.0, color="tab:red", lw=1.2, label="sound speed c")
    surv = [r for r in runs if r.get("U") is not None]
    ann = [r for r in runs if r.get("U") is None]
    xs = [r["separation_mean_over_xi"] for r in surv]
    for a in ax:
        a.errorbar(xs, [r["U"] for r in surv], yerr=[2 * r["U_stderr"] for r in surv], fmt="o", color="tab:blue",
                   label="GP pair (x = measured separation)")
        if ann:
            a.plot([r["d_over_xi"] for r in ann], [r.get("pulse_speed_over_c", np.nan) for r in ann], "s", mfc="none",
                   color="tab:orange", label="GP: pair annihilated; speed of rarefaction pulse (x = initial d)")
        a.set_xlabel("separation d / xi")
        a.grid(alpha=0.3, which="both")
    ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_ylabel("translation speed U / c")
    ax[0].set_title("velocity of a collapsing vortex pair"); ax[0].set_ylim(0.01, 3)
    ax[0].legend(fontsize=7, loc="lower left")
    ax[1].set_xlim(0, 12); ax[1].set_ylim(0, 1.6); ax[1].set_title("small separations (linear axes)")
    fig.suptitle("2D Gross-Pitaevskii (hbar = m = 1, c = 1, xi = 1/sqrt 2): the classical law diverges, the quantum fluid does not exceed c", fontsize=9)
    fig.tight_layout()
    fig.savefig(png_path, dpi=130)
    print("written", png_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot", action="store_true", help="only (re)draw the figure from the JSON")
    ap.add_argument("--d", type=float, nargs="*", default=[1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0, 14.0, 20.0, 28.0, 40.0])
    ap.add_argument("--skip-convergence", action="store_true")
    ap.add_argument("--out", default=str(OUT / "gp_vortex_dipole.json"))
    a = ap.parse_args()
    if a.plot:
        plot(a.out, str(Path(a.out).with_suffix(".png")))
        return
    t0 = time.time()
    doc = {
        "units": "hbar = m = g = rho_inf = 1: c = 1, xi = 1/sqrt(2), kappa = 2 pi; lengths in xi, speeds in c",
        "equation": "i psi_t = -1/2 lap psi + (|psi|^2 - 1) psi, doubly periodic, Strang split-step Fourier",
        "initial_state": ("two counter-moving dipoles (A and its charge-flipped copy shifted by Lx/2) so the phase is exactly "
                          "periodic with zero mean flow; phase = product of arg theta_1(pi(z-z_j)/Lx | i Ly/Lx); amplitude "
                          "prod r/sqrt(r^2+1); imaginary-time amplitude relaxation with phase re-imposed"),
        "classical_reference": "U_free = kappa/(2 pi d) = 1/d; U_periodic = point-vortex speed in the same periodic 4-vortex lattice",
    }
    print("== Bogoliubov dispersion check", flush=True)
    doc["check_bogoliubov"] = bogoliubov_check()
    for r in doc["check_bogoliubov"]:
        print(f"   k xi={r['k_xi']:.2f} omega={r['omega_measured']:.5f} theory={r['omega_theory']:.5f} err={r['rel_err']:.1e}")
    print("== conservation / dt check (d = 6 xi)", flush=True)
    doc["check_conservation"] = conservation_check()
    for r in doc["check_conservation"]:
        print(f"   dt={r['dt']:.4f} (dt kmax^2/2={r['dt_kmax2_over_2']}): dE/E={r['energy_rel_drift']:.1e} dN/N={r['norm_rel_drift']:.1e} U={r['U']}")
    print("== sweep", flush=True)
    runs = []
    smallest_surviving = None
    for dd in sorted(a.d):
        r = run_dipole(dd, keep_final=True)
        runs.append(r)
    doc["runs"] = runs
    surv = [r for r in runs if r.get("U") is not None]
    if surv:
        s0 = min(surv, key=lambda r: r["d_over_xi"])
        smallest_surviving = s0["d_over_xi"]
        doc["summary"] = {
            "max_U_surviving_pair_over_c": max(r["U"] for r in surv),
            "smallest_surviving_d_over_xi": smallest_surviving,
            "largest_annihilating_d_over_xi": max([r["d_over_xi"] for r in runs if r.get("U") is None], default=None),
            "core_state_at_smallest_surviving_d": s0.get("core_state"),
            "all_U_below_c": all(r["U"] < 1.0 for r in surv),
        }
    if not a.skip_convergence:
        print("== convergence", flush=True)
        conv = []
        for dd in (4.0, 8.0, 20.0):
            base = next((r for r in runs if r["d_over_xi"] == dd), None) or run_dipole(dd)
            fine = run_dipole(dd, dx_over_xi=0.25)
            big = run_dipole(dd, box_scale=2.0)
            keys = ("U", "U_stderr", "U_over_classical_periodic", "U_over_classical_periodic_at_measured_sep",
                    "separation_mean_over_xi", "U_classical_periodic", "dx_over_xi", "Lx_over_xi", "Ly_over_xi", "annihilated")
            conv.append({"d_over_xi": dd, "base": {k: base.get(k) for k in keys},
                         "fine_dx": {k: fine.get(k) for k in keys}, "box_x2": {k: big.get(k) for k in keys}})
        doc["convergence"] = conv
    doc["wall_s_total"] = time.time() - t0
    Path(a.out).write_text(json.dumps(doc, indent=1, default=float))
    print("written", a.out, f"{doc['wall_s_total']:.0f}s")
    plot(a.out, str(Path(a.out).with_suffix(".png")))


if __name__ == "__main__":
    main()
