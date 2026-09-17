#!/usr/bin/env python3
"""Micro-macro link through quantum fluids: three exact calculations.

The dual-scale question of this programme is: what microscopic physics stops a collapsing vortex core,
and at what scale? Quantum fluids answer it exactly, and the answer can be carried back to normal fluids
term by term. Three calculations, each with a classical counterpart.

(A) The quantized vortex is OpenAI's diffusive core, and it survives by emptying its axis.
    Around a vortex of one circulation quantum u = hbar/(m r), so u r / (hbar/m) = 1 at every radius: a
    "quantum Reynolds number" identically one, the condition Re_r = O(1) of the OpenAI construction, with
    hbar/m in the role of nu. The Gross-Pitaevskii (GP) equation is, by the Madelung transform, the
    compressible Euler equations with a barotropic pressure plus a quantum-pressure term; its microscopic
    length is the healing length xi = hbar/(sqrt(2) m c), and the sonic radius u = c is r_s = hbar/(m c)
    = sqrt(2) xi -- the analogue of l* = nu/c. We solve the stationary GP vortex profile and compare it
    with its classical twin, the isothermal compressible Euler vortex with the same velocity field, whose
    cyclostrophic density is rho = exp(-(r_s/r)^2 / 2) (exact). Both evacuate the core; the classical one
    does so with an essential singularity, the quantum one as rho ~ r^2 with finite energy per length
    (up to the log), bounded mass current, and a velocity singularity that is harmless because nothing
    is there to carry it.

(B) The critical velocity is a geometric property of the dispersion curve.
    Landau: an object moving at v cannot create an excitation of momentum p and energy eps(p) unless
    eps(p) - p v < 0, so v_c = inf_p eps(p)/p -- the slope of the tangent from the origin to the curve.
    Bogoliubov: v_c = c. Free Bose gas: v_c = 0 (Godfrin and Krotscheck 2022). He-4 with a roton
    minimum: v_c is set by the roton, far below c.

(C) Modular geometry fixes the shape of a vortex lattice.
    For a doubly periodic array of equal vortices (rotating superfluids and BECs), the renormalized
    interaction energy per vortex at fixed density depends on the lattice only through its shape
    parameter tau in the upper half plane, through the SL(2,Z)-invariant function
    F(tau) = sqrt(Im tau) |eta(tau)|^2 (Kronecker's first limit formula; eta = Dedekind eta), with
    W(tau) = -log F(tau) + const. We check the invariance numerically, locate the minimum of W, and
    confirm the ordering with an independent direct lattice sum (Epstein zeta, s = 2). This is the one
    exact place where a modular form fixes a fluid parameter from geometry alone. The same eta function
    builds the K3 elliptic genus and the Mathieu-moonshine twining genera; the shared object comes from
    the modular group of a torus, not from M24, and no M24 structure appears in a fluid.

Writes results/quantum_fluid_link.json and results/quantum_fluid_link.png.
Units for (A): hbar = m = c = 1, so r_s = 1 and xi = 1/sqrt(2).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_bvp

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------------------------------
# (A) stationary GP vortex vs classical isothermal compressible vortex
# ----------------------------------------------------------------------------------------------------
# Units hbar = m = 1, g rho_inf = c^2 = 1: GP  0 = -1/2 (f'' + f'/r - f/r^2) + (f^2 - 1) f,  psi = f(r) e^{i theta}.


def gp_vortex_profile(r_max: float = 40.0, n: int = 4000):
    """Radial amplitude f(r) of a singly quantized GP vortex (f(0) = 0, f(inf) = 1)."""
    r = np.linspace(1e-6, r_max, n)

    def rhs(r, y):
        f, fp = y
        return np.vstack([fp, -fp / r + f / r ** 2 + 2.0 * (f ** 2 - 1.0) * f])

    def bc(ya, yb):
        return np.array([ya[0], yb[0] - (1.0 - 0.25 / r_max ** 2)])   # large-r asymptote f ~ 1 - 1/(4 r^2)

    guess = np.vstack([np.tanh(r / np.sqrt(2.0)), (1.0 / np.sqrt(2.0)) / np.cosh(r / np.sqrt(2.0)) ** 2])
    sol = solve_bvp(rhs, bc, r, guess, tol=1e-8, max_nodes=200000)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol


def part_a():
    sol = gp_vortex_profile()
    r = np.geomspace(1e-3, 30.0, 2000)
    f = sol.sol(r)[0]
    rho_gp = f ** 2
    u = 1.0 / r                                   # hbar/(m r)
    rho_cl = np.exp(-0.5 / r ** 2)                # isothermal Euler vortex, c = 1: d ln rho / dr = u^2 / r
    re_q = u * r / 1.0                            # u r / (hbar/m)
    j_gp = rho_gp * u
    mach_loc_gp = u / np.sqrt(np.maximum(rho_gp, 1e-300))
    xi = 1.0 / np.sqrt(2.0)
    # small-r slope of f: f ~ a r
    a_slope = float(sol.sol(1e-3)[0] / 1e-3)
    r_half_gp = float(np.interp(0.5, rho_gp, r))
    r_half_cl = float(np.interp(0.5, rho_cl, r))
    far = r > 5
    rel_far = float(np.max(np.abs(rho_gp[far] - rho_cl[far]) / (1 - rho_cl[far])))
    # energy per unit length inside radius R (kinetic hydrodynamic + quantum + interaction), relative to uniform
    rr = np.linspace(1e-6, 30.0, 60000)
    ff, ffp = sol.sol(rr)
    dens = 0.5 * ffp ** 2 + 0.5 * ff ** 2 / rr ** 2 + 0.5 * (ff ** 2 - 1.0) ** 2
    e_R = float(np.trapz(dens * 2 * np.pi * rr, rr))
    return {
        "units": "hbar = m = c = 1: sonic radius r_s = hbar/(m c) = 1, healing length xi = 1/sqrt(2)",
        "quantum_reynolds_number_min_max": [float(re_q.min()), float(re_q.max())],
        "sonic_radius_over_xi": 1.0 / xi,
        "gp_core_slope_f_over_r_at_axis": a_slope,
        "radius_where_density_is_half": {"gp": r_half_gp, "classical_isothermal_euler": r_half_cl,
                                         "gp_over_xi": r_half_gp / xi},
        "max_mass_current_rho_u": {"gp": float(j_gp.max()), "at_r": float(r[np.argmax(j_gp)])},
        "local_mach_at_r_s": float(np.interp(1.0, r, mach_loc_gp)),
        "far_field_relative_difference_of_density_deficit_r_gt_5": rel_far,
        "gp_energy_per_length_R30_over_pi_log": e_R / (np.pi * np.log(30.0 / xi)),
        "series": {"r": r[::20].tolist(), "rho_gp": rho_gp[::20].tolist(), "rho_classical": rho_cl[::20].tolist()},
    }


# ----------------------------------------------------------------------------------------------------
# (B) Landau critical velocity from the geometry of the dispersion curve
# ----------------------------------------------------------------------------------------------------
HBAR = 1.054571817e-34
KB = 1.380649e-23
M_HE4 = 6.6464731e-27


def landau_vc(eps, k):
    """v_c = min_k eps(k) / (hbar k) (eps in J, k in 1/m)."""
    v = eps / (HBAR * k)
    i = int(np.argmin(v))
    return float(v[i]), float(k[i])


def part_b():
    # dimensionless Bogoliubov (hbar = m = c = 1): eps = sqrt(k^2 + k^4/4)
    k = np.geomspace(1e-6, 50, 200000)
    bog = np.sqrt(k ** 2 + k ** 4 / 4) / k
    free = (k ** 2 / 2) / k
    # He-4, T -> 0, saturated vapour pressure, approximate standard values (Donnelly & Barenghi 1998):
    c_he, delta, k0, mu = 238.0, 8.62 * KB, 1.92e10, 0.16 * M_HE4
    kk = np.linspace(0.05e10, 3.0e10, 300000)
    phonon = HBAR * c_he * kk
    roton = delta + (HBAR * (kk - k0)) ** 2 / (2 * mu)
    eps_he = np.minimum(phonon, roton)            # lower envelope of the two Landau branches
    vc_he, k_at = landau_vc(eps_he, kk)
    return {
        "bogoliubov_vc_over_c": float(bog.min()),
        "free_bose_gas_vc_at_smallest_k": float(free.min()),
        "he4_inputs": {"c_m_s": c_he, "roton_gap_K": 8.62, "roton_k0_inv_A": 1.92, "roton_mass_over_m4": 0.16,
                       "source": "approximate standard values at T -> 0, SVP (Donnelly & Barenghi 1998)"},
        "he4_landau_vc_m_s": vc_he, "he4_vc_at_k_inv_A": k_at / 1e10,
        "he4_delta_over_hbar_k0_m_s": float(delta / (HBAR * k0)),
        "he4_vc_over_c": vc_he / c_he,
    }


# ----------------------------------------------------------------------------------------------------
# (C) modular geometry of a vortex lattice
# ----------------------------------------------------------------------------------------------------
def eta(tau: complex, nmax: int = 400) -> complex:
    q = np.exp(2j * np.pi * tau)
    n = np.arange(1, nmax + 1)
    return np.exp(2j * np.pi * tau / 24) * np.prod(1 - q ** n)


def F(tau: complex) -> float:
    """SL(2,Z)-invariant sqrt(Im tau) |eta(tau)|^2."""
    return float(np.sqrt(tau.imag) * abs(eta(tau)) ** 2)


def epstein_unit_area(tau: complex, s: float = 2.0, N: int = 120) -> float:
    """sum' |omega|^{-2s} over the lattice Z + tau Z rescaled to unit cell area."""
    scale = 1.0 / np.sqrt(tau.imag)
    m, n = np.meshgrid(np.arange(-N, N + 1), np.arange(-N, N + 1))
    w = (m + n * tau) * scale
    a2 = np.abs(w) ** 2
    a2 = a2[a2 > 0]
    return float(np.sum(a2 ** (-s)))


def part_c():
    hexa, square = complex(0.5, np.sqrt(3) / 2), complex(0.0, 1.0)
    test = [complex(0.13, 0.91), complex(-0.31, 1.37), complex(0.42, 0.97)]
    inv = []
    for t in test:
        inv.append({"tau": [t.real, t.imag], "F(tau)": F(t), "F(tau+1)": F(t + 1), "F(-1/tau)": F(-1 / t)})
    inv_err = max(max(abs(d["F(tau+1)"] / d["F(tau)"] - 1), abs(d["F(-1/tau)"] / d["F(tau)"] - 1)) for d in inv)
    # scan the fundamental domain |Re tau| <= 1/2, |tau| >= 1
    xs, ys = np.linspace(-0.5, 0.5, 201), np.linspace(np.sqrt(3) / 2 - 1e-9, 2.0, 230)
    best = (np.inf, None)
    for x in xs:
        for y in ys:
            t = complex(x, y)
            if abs(t) < 1:
                continue
            W = -np.log(F(t))
            if W < best[0]:
                best = (W, t)
    W_hex, W_sq = -np.log(F(hexa)), -np.log(F(square))
    Z_hex, Z_sq = epstein_unit_area(hexa), epstein_unit_area(square)
    Z_rect = epstein_unit_area(complex(0, 1.5))
    return {
        "modular_invariance_max_rel_error": float(inv_err),
        "invariance_samples": inv,
        "argmin_W_in_fundamental_domain": [best[1].real, best[1].imag],
        "hexagonal_tau": [hexa.real, hexa.imag],
        "W_square_minus_W_hexagonal": float(W_sq - W_hex),
        "epstein_s2_unit_area": {"hexagonal": Z_hex, "square": Z_sq, "rectangular_1x1.5": Z_rect},
        "independent_check_hexagonal_is_lowest": bool(Z_hex < Z_sq < Z_rect and W_hex < W_sq),
        "note": "W(tau) = -log(sqrt(Im tau)|eta|^2) is the tau-dependent part of the renormalized energy of a "
                "2D Coulomb (point-vortex) lattice at fixed density (Kronecker limit formula); the minimum at "
                "the hexagonal point is classical (Rankin, Cassels, Ennola, Diananda; Sandier-Serfaty for the "
                "renormalized energy). Observed in rotating BECs (Abo-Shaeer et al., Science 2001).",
    }


# ----------------------------------------------------------------------------------------------------
# (D) a floor on the validity length from fundamental constants
# ----------------------------------------------------------------------------------------------------
M_E, M_P, C_LIGHT, ALPHA = 9.1093837015e-31, 1.67262192369e-27, 2.99792458e8, 7.2973525693e-3
A_BOHR = 5.29177210903e-11


def part_d():
    """nu_m = hbar/(4 pi sqrt(m_e m)) (Trachenko & Brazhkin, Sci. Adv. 2020) and
    v_u(A) = alpha c sqrt(m_e/(2 m_p)) / sqrt(A) (Trachenko et al., Sci. Adv. 2020): their ratio is
    independent of A and equals (sqrt 2 / 4 pi) a_B. Both inputs are order-of-magnitude bounds."""
    rows = {}
    for name, A in (("hydrogen (A=1)", 1.0), ("helium-4 (A=4)", 4.0), ("water (A=18)", 18.0), ("mercury (A=200.6)", 200.6)):
        num = HBAR / (4 * np.pi * np.sqrt(M_E * A * M_P))
        vu = ALPHA * C_LIGHT * np.sqrt(M_E / (2 * M_P)) / np.sqrt(A)
        rows[name] = {"nu_m_m2_s": num, "v_u_m_s": vu, "nu_m_over_v_u_m": num / vu}
    floor = np.sqrt(2) / (4 * np.pi) * A_BOHR
    water_lstar = 1.0e-6 / 1482.0
    return {
        "floor_sqrt2_over_4pi_bohr_radius_m": floor,
        "per_fluid": rows,
        "water_lstar_m": water_lstar, "water_lstar_over_floor": water_lstar / floor,
        "hbar_over_m_he4_m2_s": HBAR / M_HE4,
        "note": "l* = nu/c >= nu_m/v_u for any fluid satisfying both bounds; the mass cancels exactly "
                "(QuantumVortexLink.lean, lstar_floor_identity). The inputs are estimates, not theorems.",
    }


def main():
    a, b, c, d = part_a(), part_b(), part_c(), part_d()
    out = {"A_quantized_vortex_vs_classical": a, "B_landau_criterion": b, "C_vortex_lattice_modular": c,
           "D_validity_length_floor": d}
    (OUT / "quantum_fluid_link.json").write_text(json.dumps(out, indent=1))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
        s = a["series"]
        ax[0].semilogx(s["r"], s["rho_gp"], label="GP (quantum fluid)")
        ax[0].semilogx(s["r"], s["rho_classical"], "--", label="isothermal compressible Euler, same u = 1/r")
        ax[0].axvline(1.0, color="k", lw=0.7, ls=":"); ax[0].text(1.05, 0.05, "sonic radius r_s = sqrt(2) xi", fontsize=8)
        ax[0].set_xlabel("r / (hbar / m c)"); ax[0].set_ylabel("rho / rho_inf"); ax[0].legend(fontsize=8)
        ax[0].set_title("(A) both fluids survive u = 1/r by emptying the core")
        k = np.linspace(0.01, 3.0, 600)
        ax[1].plot(k, np.sqrt(k ** 2 + k ** 4 / 4), label="Bogoliubov eps(k)")
        ax[1].plot(k, k ** 2 / 2, label="free Bose gas")
        ax[1].plot(k, k, "k:", label="slope v_c = c")
        ax[1].set_xlabel("k (units m c / hbar)"); ax[1].set_ylabel("eps (units m c^2)")
        ax[1].set_title(f"(B) v_c = min eps/p;  He-4 roton: {b['he4_landau_vc_m_s']:.0f} m/s vs c = 238 m/s", fontsize=9)
        ax[1].legend(fontsize=8); ax[1].set_ylim(0, 4)
        X, Y = np.meshgrid(np.linspace(-0.5, 0.5, 121), np.linspace(0.8, 1.8, 121))
        Wg = np.vectorize(lambda x, y: -np.log(F(complex(x, y))) if x * x + y * y >= 1 else np.nan)(X, Y)
        cs = ax[2].contourf(X, Y, Wg, 30); fig.colorbar(cs, ax=ax[2])
        ax[2].plot([0.5, -0.5], [np.sqrt(3) / 2] * 2, "r*", ms=12)
        ax[2].set_xlabel("Re tau"); ax[2].set_ylabel("Im tau")
        ax[2].set_title("(C) lattice energy -log(sqrt(Im tau)|eta|^2): minimum at hexagonal tau", fontsize=9)
        fig.tight_layout(); fig.savefig(OUT / "quantum_fluid_link.png", dpi=130)
    except Exception as e:  # plotting is optional
        print("plot skipped:", e)
    for key, block in out.items():
        print(key)
        for kk, v in block.items():
            if kk not in ("series", "invariance_samples"):
                print("  ", kk, v)


if __name__ == "__main__":
    main()
