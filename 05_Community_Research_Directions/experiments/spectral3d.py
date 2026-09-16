"""
3D pseudo-spectral incompressible Navier-Stokes solver.

Built as the enabling infrastructure for the open questions stated in
01_Verification_Paper/OpenAI_NSE_Verification.tex (Outlook):

  Q1 (cutoff law)  If a regularization arrests the collapse when the core radius
                   reaches sqrt(alpha'), then since l_r ~ sqrt(nu t) and
                   u ~ sqrt(nu/t), the arrested peak velocity should scale as
                   u_max ~ nu/sqrt(alpha') and the arrest time as t_c ~ alpha'/nu.
                   UNTESTED until now -- see sweep_cutoff_law.py.
  Q2 (thermal noise)  Do the exponentially small seeded pulses survive
                      Landau-Lifshitz fluctuating hydrodynamics? -- see thermal_noise.py.
  Q3 (validity)    A runtime monitor for the paper's local admissibility bound
                   |omega| <~ c_s^2/nu.  -- see ValidityMonitor below.

Why this file exists: the DualScale solver package provides
`PseudoSpectralNavierStokes2D`, which is 2D only. Two-dimensional Navier-Stokes
is unconditionally globally regular, so it cannot address a 3D regularity
question at all. This module is the 3D extension, reusing that solver's
projection/dealiasing design and the package's RK4 integrator.

Design notes
------------
* Rotational form.  (u.grad)u = omega x u + grad(|u|^2/2). The Leray projector
  annihilates the gradient, so only  omega x u  is ever transformed. This costs
  9 FFTs per RHS instead of 12+ and is standard practice.
* Integrating-factor RK4.  The dissipation operator nu|k|^2(1 + alpha'|k|^2) is
  linear, diagonal, and extremely stiff once alpha'|k|^2 >> 1 -- an explicit RK4
  step would be limited to dt ~ 1/(nu k^4 alpha'), which makes a sweep over
  decades of alpha' infeasible. IFRK4 integrates that term exactly, leaving only
  the advective CFL constraint. This is the change that makes Q1 testable.
* Divergence.  Reported as a *relative* quantity. An absolute figure is
  meaningless: a previous benchmark in this program reported |div u| ~ 1e-32 as
  "exact machine zero" when it was an artifact of the 2D Taylor-Green initial
  condition having 8 nonzero modes with power-of-two coefficients, so that k.u
  cancelled exactly in binary. A generic field in the same solver gives ~1e-15,
  which is ordinary float64. See divergence_report().
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np

# --- Dependency on the DualScale solver package -----------------------------
# Imported for the non-stiff reference integrator so the two codebases share a
# time-stepper. Located via PYTHONPATH or the default sibling checkout; the
# import is optional because IFRK4 (below) is what the stiff sweeps actually use.
_DUALSCALE_SRC = os.path.expanduser(
    "~/xdev/SocrateAI-Numeric-DualScale-Solver/SocrateAI-Numeric-DualScale-Solver/src"
)
if os.path.isdir(_DUALSCALE_SRC) and _DUALSCALE_SRC not in sys.path:
    sys.path.insert(0, _DUALSCALE_SRC)

try:
    from dualscale_solver.numeric.rk4_integrator import rk4_step as _dualscale_rk4_step
    HAVE_DUALSCALE = True
except Exception:  # pragma: no cover - the package is optional
    _dualscale_rk4_step = None
    HAVE_DUALSCALE = False


# ---------------------------------------------------------------------------
# Physical reference constants (water at 300 K), matching the flagship paper
# ---------------------------------------------------------------------------

WATER_300K = {
    "nu": 1.0e-6,        # m^2/s
    "c_s": 1500.0,       # m/s
    "c_p": 4184.0,       # J/(kg K)
    "rho": 1000.0,       # kg/m^3
    "lambda_mol": 3.0e-10,  # m (intermolecular spacing)
}

AIR_300K = {
    "nu": 1.56e-5,
    "c_s": 343.0,
    "c_p": 1005.0,
    "rho": 1.2,
    "lambda_mol": 6.8e-8,
}


def admissible_vorticity_bound(nu: float, c_s: float) -> float:
    """
    The paper's local admissibility bound  |omega| <~ c_s^2 / nu.

    Derivation (Prop. 5.1 / Eq. admissible): a vortex of velocity U and size L has
    |omega| ~ U/L; validity needs U <~ c_s (Mach) and L >~ nu/c_s (Knudsen, via
    l_* = nu/c_s). Hence |omega| <~ c_s^2/nu. Water: 2.2e12 1/s. Air: 7.5e9 1/s.
    """
    return c_s**2 / nu


# ---------------------------------------------------------------------------
# Validity monitor (research direction 4)
# ---------------------------------------------------------------------------

@dataclass
class ValidityMonitor:
    """
    Runtime monitor for departure from the regime where incompressible
    Navier-Stokes is a valid model *of a real fluid*.

    This is deliberately distinct from a numerical stability check. A simulation
    can be perfectly stable numerically while describing a state no real fluid
    can be in. The monitor reports the first crossing of each threshold and the
    running worst case, in the fluid's own physical units.

    Thresholds (flagship paper, Prop. 5.1 and Eq. admissible):
      Mach        Ma = |u|/c_s          <~ 0.3   (constant-density convention)
      Knudsen     Kn = lambda/l          <~ 0.1
      Vorticity   |omega| <~ c_s^2/nu             (equivalent to Ma <~1 and Kn <~1)

    `u_scale` and `l_scale` convert the simulation's nondimensional units to SI:
    a simulation velocity of 1.0 means u_scale m/s, a simulation length of 1.0
    means l_scale m.
    """

    nu: float
    c_s: float
    lambda_mol: float
    u_scale: float = 1.0
    l_scale: float = 1.0
    ma_threshold: float = 0.3
    kn_threshold: float = 0.1

    first_ma_crossing: Optional[float] = None
    first_kn_crossing: Optional[float] = None
    first_vort_crossing: Optional[float] = None
    worst_ma: float = 0.0
    worst_kn: float = 0.0
    worst_vort_ratio: float = 0.0
    history: list = field(default_factory=list)

    @property
    def omega_max_admissible(self) -> float:
        return admissible_vorticity_bound(self.nu, self.c_s)

    def update(self, t: float, u_max_sim: float, omega_max_sim: float,
               l_min_sim: float) -> Dict[str, Any]:
        """Record one sample. Returns the flags raised at this time."""
        u_phys = u_max_sim * self.u_scale
        # |omega| has dimensions 1/time: (u_scale/l_scale) per simulation unit
        omega_phys = omega_max_sim * (self.u_scale / self.l_scale)
        l_phys = l_min_sim * self.l_scale

        ma = u_phys / self.c_s
        kn = self.lambda_mol / l_phys if l_phys > 0 else np.inf
        vort_ratio = omega_phys / self.omega_max_admissible

        self.worst_ma = max(self.worst_ma, ma)
        self.worst_kn = max(self.worst_kn, kn)
        self.worst_vort_ratio = max(self.worst_vort_ratio, vort_ratio)

        flags = {}
        if ma > self.ma_threshold:
            flags["mach"] = ma
            if self.first_ma_crossing is None:
                self.first_ma_crossing = t
        if kn > self.kn_threshold:
            flags["knudsen"] = kn
            if self.first_kn_crossing is None:
                self.first_kn_crossing = t
        if vort_ratio > 1.0:
            flags["vorticity"] = vort_ratio
            if self.first_vort_crossing is None:
                self.first_vort_crossing = t

        self.history.append(
            {"t": t, "Ma": ma, "Kn": kn, "vort_ratio": vort_ratio}
        )
        return flags

    def report(self) -> Dict[str, Any]:
        return {
            "omega_max_admissible_per_s": self.omega_max_admissible,
            "worst_Ma": self.worst_ma,
            "worst_Kn": self.worst_kn,
            "worst_vorticity_ratio": self.worst_vort_ratio,
            "first_Ma_crossing_t": self.first_ma_crossing,
            "first_Kn_crossing_t": self.first_kn_crossing,
            "first_vorticity_crossing_t": self.first_vort_crossing,
            "stayed_admissible": (
                self.first_ma_crossing is None
                and self.first_kn_crossing is None
                and self.first_vort_crossing is None
            ),
        }


# ---------------------------------------------------------------------------
# The solver
# ---------------------------------------------------------------------------

class PseudoSpectralNavierStokes3D:
    """
    3D incompressible Navier-Stokes in a periodic box [0, 2*pi)^3.

        du/dt + (u.grad)u = -grad p + D(u) [+ thermal noise]
        div(u) = 0

    Dissipation operator D, in Fourier space, is one of:
        'laplacian'  :  -nu |k|^2                          (standard NSE)
        'bihyper'    :  -nu |k|^2 (1 + alpha' |k|^2)       (as in the 2D DualScale solver)
        'barrier'    :  -nu |k|^2 max(1, alpha' |k|^2)     (as in the dyadic shell model)

    The two alpha' forms differ: 'bihyper' adds hyperviscosity at *all* scales,
    'barrier' leaves scales with alpha'|k|^2 < 1 untouched and only bites above
    k = 1/sqrt(alpha'). 'barrier' is the one that corresponds to a cutoff *scale*
    and is therefore the right operator for testing the cutoff law; a previous
    benchmark in this program conflated the two.
    """

    def __init__(
        self,
        n_grid: int = 64,
        nu: float = 1e-3,
        alpha_prime: Optional[float] = None,
        dissipation: str = "laplacian",
        dealias: bool = True,
        leray_alpha: Optional[float] = None,
        leray_filter_power: int = 1,
    ):
        if dissipation not in ("laplacian", "bihyper", "barrier"):
            raise ValueError(f"unknown dissipation operator: {dissipation}")
        if dissipation != "laplacian" and not alpha_prime:
            raise ValueError(f"dissipation='{dissipation}' requires alpha_prime > 0")

        self.n = int(n_grid)
        self.nu = float(nu)
        self.alpha_prime = alpha_prime
        self.dissipation = dissipation

        k1d = np.fft.fftfreq(self.n, d=1.0 / self.n)
        self.kx, self.ky, self.kz = np.meshgrid(k1d, k1d, k1d, indexing="ij")
        self.k_vec = np.stack([self.kx, self.ky, self.kz])

        self.k_sq = self.kx**2 + self.ky**2 + self.kz**2
        self.k_mag = np.sqrt(self.k_sq)
        with np.errstate(divide="ignore", invalid="ignore"):
            self.k_sq_inv = np.where(self.k_sq > 0, 1.0 / np.where(self.k_sq > 0, self.k_sq, 1.0), 0.0)

        # Orszag 2/3 dealiasing
        if dealias:
            kcut = (2.0 / 3.0) * (self.n / 2.0)
            self.dealias_mask = (
                (np.abs(self.kx) < kcut) & (np.abs(self.ky) < kcut) & (np.abs(self.kz) < kcut)
            )
        else:
            self.dealias_mask = np.ones_like(self.k_sq, dtype=bool)

        self.k_max_effective = (2.0 / 3.0) * (self.n / 2.0) if dealias else self.n / 2.0
        self.diss_symbol = self._build_dissipation_symbol()

        # --- Leray-alpha transport regularization -------------------------
        # NOTE: this is a *different* model from the 'barrier'/'bihyper'
        # dissipation operators above, and the two are easily conflated.
        #   hyperviscous barrier : modifies DISSIPATION,  nu|k|^2 -> nu|k|^2 m(k)
        #   Leray-alpha          : modifies TRANSPORT,    (u.grad)u -> (ubar.grad)u
        # Only the second is the Leray-alpha / Navier-Stokes-alpha family whose
        # 3D global well-posedness is a theorem (Foias-Holm-Titi 2001;
        # Cheskidov-Holm-Olson-Titi 2005). A result about one says nothing about
        # the other.
        self.leray_alpha = leray_alpha
        self.leray_filter_power = int(leray_filter_power)
        if leray_alpha:
            self.filter_symbol = 1.0 / (1.0 + leray_alpha**2 * self.k_sq) ** self.leray_filter_power
        else:
            self.filter_symbol = None

    # -- operators ----------------------------------------------------------

    def _build_dissipation_symbol(self) -> np.ndarray:
        """Return the (negative, real) linear dissipation symbol L(k)."""
        if self.dissipation == "laplacian":
            return -self.nu * self.k_sq
        if self.dissipation == "bihyper":
            return -self.nu * self.k_sq * (1.0 + self.alpha_prime * self.k_sq)
        # 'barrier'
        return -self.nu * self.k_sq * np.maximum(1.0, self.alpha_prime * self.k_sq)

    @property
    def barrier_wavenumber(self) -> Optional[float]:
        """k_alpha = 1/sqrt(alpha'), the wavenumber where the barrier engages."""
        if not self.alpha_prime:
            return None
        return 1.0 / np.sqrt(self.alpha_prime)

    def barrier_is_resolved(self) -> bool:
        """True if the barrier engages inside the resolved (dealiased) band."""
        ka = self.barrier_wavenumber
        return ka is not None and 1.0 < ka < self.k_max_effective

    def project_leray(self, u_hat: np.ndarray) -> np.ndarray:
        """P(k)u = u - k(k.u)/|k|^2, then zero the mean mode and dealias."""
        k_dot_u = self.kx * u_hat[0] + self.ky * u_hat[1] + self.kz * u_hat[2]
        factor = k_dot_u * self.k_sq_inv
        out = np.empty_like(u_hat)
        out[0] = u_hat[0] - factor * self.kx
        out[1] = u_hat[1] - factor * self.ky
        out[2] = u_hat[2] - factor * self.kz
        out[:, 0, 0, 0] = 0.0
        out *= self.dealias_mask
        return out

    def curl(self, u_hat: np.ndarray) -> np.ndarray:
        """Vorticity in Fourier space: omega = i k x u."""
        return 1j * np.stack([
            self.ky * u_hat[2] - self.kz * u_hat[1],
            self.kz * u_hat[0] - self.kx * u_hat[2],
            self.kx * u_hat[1] - self.ky * u_hat[0],
        ])

    def nonlinear(self, u_hat: np.ndarray) -> np.ndarray:
        """
        Projected nonlinear term in rotational form.

        (u.grad)u = omega x u + grad(|u|^2/2); the Leray projector kills the
        gradient, so the projected RHS needs only -(omega x u).
        """
        u = np.stack([np.fft.ifftn(u_hat[i]).real for i in range(3)])
        w = np.stack([np.fft.ifftn(self.curl(u_hat)[i]).real for i in range(3)])
        wxu = np.stack([
            w[1] * u[2] - w[2] * u[1],
            w[2] * u[0] - w[0] * u[2],
            w[0] * u[1] - w[1] * u[0],
        ])
        nl_hat = np.stack([np.fft.fftn(wxu[i]) for i in range(3)])
        return self.project_leray(-nl_hat)

    def smoothed_velocity(self, u_hat: np.ndarray) -> np.ndarray:
        """The Leray-alpha transport velocity ubar = (1 - alpha^2 Delta)^{-p} u."""
        if self.filter_symbol is None:
            return u_hat
        return u_hat * self.filter_symbol

    def nonlinear_leray_alpha(self, u_hat: np.ndarray) -> np.ndarray:
        """
        Projected nonlinear term for Leray-alpha: -P[(ubar.grad)u].

        Computed in divergence form, (ubar.grad)u = div(ubar (x) u), which is
        valid because ubar is solenoidal (the filter is a function of |k| and so
        commutes with the Leray projector). The rotational form used for plain
        Navier-Stokes does not apply here: the identity
        (u.grad)u = omega x u + grad(|u|^2/2) needs the advecting and advected
        velocities to be the same field, and in this model they are not.
        """
        ub_hat = self.smoothed_velocity(u_hat)
        u = np.stack([np.fft.ifftn(u_hat[i]).real for i in range(3)])
        ub = np.stack([np.fft.ifftn(ub_hat[i]).real for i in range(3)])
        out = np.empty_like(u_hat)
        for i in range(3):
            flux = np.stack([np.fft.fftn(ub[j] * u[i]) for j in range(3)])
            out[i] = 1j * (self.kx * flux[0] + self.ky * flux[1] + self.kz * flux[2])
        return self.project_leray(-out)

    def nonlinear_term(self, u_hat: np.ndarray) -> np.ndarray:
        """Dispatch to the Leray-alpha or the plain Navier-Stokes nonlinearity."""
        if self.filter_symbol is None:
            return self.nonlinear(u_hat)
        return self.nonlinear_leray_alpha(u_hat)

    def rhs(self, t: float, u_hat: np.ndarray) -> np.ndarray:
        """Full RHS including dissipation (for the non-stiff reference stepper)."""
        return self.nonlinear_term(u_hat) + self.diss_symbol * u_hat

    # -- diagnostics --------------------------------------------------------

    def energy(self, u_hat: np.ndarray) -> float:
        """Mean kinetic energy per unit volume, (1/2)<|u|^2>."""
        return 0.5 * float(np.sum(np.abs(u_hat) ** 2)) / (self.n**6)

    def enstrophy(self, u_hat: np.ndarray) -> float:
        """Mean enstrophy per unit volume, (1/2)<|omega|^2>."""
        w_hat = self.curl(u_hat)
        return 0.5 * float(np.sum(np.abs(w_hat) ** 2)) / (self.n**6)

    def dissipation_rate(self, u_hat: np.ndarray) -> float:
        """epsilon = 2 nu <(1/2)|omega|^2> for the plain Laplacian; uses the actual symbol."""
        return float(np.sum(-2.0 * self.diss_symbol * np.abs(u_hat) ** 2)) / (self.n**6) / 2.0

    def max_velocity(self, u_hat: np.ndarray) -> float:
        u = np.stack([np.fft.ifftn(u_hat[i]).real for i in range(3)])
        return float(np.max(np.sqrt(np.sum(u**2, axis=0))))

    def max_vorticity(self, u_hat: np.ndarray) -> float:
        w_hat = self.curl(u_hat)
        w = np.stack([np.fft.ifftn(w_hat[i]).real for i in range(3)])
        return float(np.max(np.sqrt(np.sum(w**2, axis=0))))

    def divergence_report(self, u_hat: np.ndarray) -> Dict[str, float]:
        """
        Divergence, reported *relatively*. See module docstring: an absolute
        figure is not interpretable, and a very small one is usually an artifact
        of a special initial condition rather than a property of the method.
        """
        div_hat = 1j * (self.kx * u_hat[0] + self.ky * u_hat[1] + self.kz * u_hat[2])
        div_l2 = float(np.sqrt(np.sum(np.abs(div_hat) ** 2)))
        # Natural comparison scale: |k||u|, the size div would have if u were not solenoidal
        scale = float(np.sqrt(np.sum(self.k_sq * np.sum(np.abs(u_hat) ** 2, axis=0))))
        return {
            "div_l2_absolute": div_l2,
            "div_l2_relative": div_l2 / scale if scale > 0 else 0.0,
            "comparison_scale_k_times_u": scale,
        }

    def energy_spectrum(self, u_hat: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Shell-averaged E(k), k = 1 .. n/2."""
        e_density = 0.5 * np.sum(np.abs(u_hat) ** 2, axis=0) / (self.n**6)
        kbin = np.rint(self.k_mag).astype(int)
        nk = self.n // 2
        spectrum = np.bincount(kbin.ravel(), weights=e_density.ravel(), minlength=nk + 1)[: nk + 1]
        return np.arange(nk + 1), spectrum

    def taylor_microscale_reynolds(self, u_hat: np.ndarray) -> float:
        """Re_lambda = u_rms * lambda / nu with lambda = sqrt(15 nu u_rms^2/epsilon)."""
        e = self.energy(u_hat)
        u_rms = np.sqrt(2.0 * e / 3.0)
        eps = self.dissipation_rate(u_hat)
        if eps <= 0:
            return float("inf")
        lam = np.sqrt(15.0 * self.nu * u_rms**2 / eps)
        return float(u_rms * lam / self.nu)

    def kolmogorov_scale(self, u_hat: np.ndarray) -> float:
        eps = self.dissipation_rate(u_hat)
        if eps <= 0:
            return float("inf")
        return float((self.nu**3 / eps) ** 0.25)

    # -- initial conditions -------------------------------------------------

    def grid(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        x1d = np.linspace(0.0, 2.0 * np.pi, self.n, endpoint=False)
        return np.meshgrid(x1d, x1d, x1d, indexing="ij")

    def initialize_taylor_green(self, u0: float = 1.0) -> np.ndarray:
        """
        Standard 3D Taylor-Green vortex (the canonical transition benchmark):
            u = ( U sin x cos y cos z, -U cos x sin y cos z, 0 )
        """
        x, y, z = self.grid()
        ux = u0 * np.sin(x) * np.cos(y) * np.cos(z)
        uy = -u0 * np.cos(x) * np.sin(y) * np.cos(z)
        uz = np.zeros_like(x)
        u_hat = np.stack([np.fft.fftn(ux), np.fft.fftn(uy), np.fft.fftn(uz)])
        return self.project_leray(u_hat)

    def initialize_random_solenoidal(self, seed: int = 0, k_peak: float = 4.0,
                                     energy: float = 0.5) -> np.ndarray:
        """
        Random solenoidal field with a von Karman-like spectrum peaked at k_peak.

        Deliberately *not* a special initial condition: used as the control that
        shows the divergence floor of this method is ordinary float64 (~1e-15
        relative), not the ~1e-32 an algebraically special field can produce.
        """
        rng = np.random.default_rng(seed)
        shape = (3,) + self.k_sq.shape
        noise = rng.normal(size=shape) + 1j * rng.normal(size=shape)
        amp = np.where(
            self.k_sq > 0,
            (self.k_mag / k_peak) ** 2 / (1.0 + (self.k_mag / k_peak) ** 2) ** (17.0 / 6.0),
            0.0,
        )
        u_hat = self.project_leray(noise * amp)
        e = self.energy(u_hat)
        if e > 0:
            u_hat *= np.sqrt(energy / e)
        return u_hat

    def initialize_colliding_vortex_tubes(self, u0: float = 1.0, core: float = 0.35,
                                          offset: float = 0.9) -> np.ndarray:
        """
        Two antiparallel vortex tubes, offset and perturbed so they approach and
        strain each other. This is the configuration in which intense vortex
        stretching and small-scale generation are expected, so it is the
        candidate initial condition for driving a flow *into* the barrier
        (research direction 2). Built from a vector potential so that the field
        is solenoidal by construction before projection.
        """
        x, y, z = self.grid()
        # Perturb the tube axes sinusoidally in z so they are not translation-invariant
        wiggle = 0.25 * np.sin(z)
        ay = np.zeros_like(x)
        ax = np.zeros_like(x)
        az = np.zeros_like(x)
        for sign, y0 in ((1.0, np.pi - offset), (-1.0, np.pi + offset)):
            r2 = (x - np.pi - sign * wiggle) ** 2 + (y - y0) ** 2
            az += sign * u0 * np.exp(-r2 / (2.0 * core**2))
        a_hat = np.stack([np.fft.fftn(ax), np.fft.fftn(ay), np.fft.fftn(az)])
        u_hat = self.curl(a_hat)  # u = curl A is solenoidal identically
        u_hat = self.project_leray(u_hat)
        e = self.energy(u_hat)
        if e > 0:
            u_hat *= np.sqrt(0.5 * u0**2 / e)
        return u_hat

    # -- thermal noise (research direction 3) -------------------------------

    def thermal_noise_increment(self, dt: float, temperature_param: float,
                                rng: np.random.Generator) -> np.ndarray:
        """
        One Landau-Lifshitz fluctuating-hydrodynamics increment.

        The fluctuating stress s has covariance
            <s_ij s_kl> = 2 k_B T eta (d_ik d_jl + d_il d_jk - (2/3) d_ij d_kl) delta(r-r') delta(t-t'),
        and enters the momentum equation as div(s)/rho. In Fourier space, after
        Leray projection, the solenoidal forcing has variance per mode
        proportional to  2 nu k_B T |k|^2 / (rho V)  per unit time, so the
        increment over dt scales as sqrt(2 nu theta |k|^2 dt).

        `temperature_param` is theta = k_B T/(rho V) in simulation units; it is
        calibrated by the fluctuation-dissipation check in thermal_noise.py,
        which verifies that the resulting equilibrium obeys equipartition rather
        than assuming the prefactor is right.
        """
        shape = (3,) + self.k_sq.shape
        xi = (rng.normal(size=shape) + 1j * rng.normal(size=shape)) / np.sqrt(2.0)
        amp = np.sqrt(2.0 * self.nu * temperature_param * self.k_sq * dt) * (self.n**3)
        return self.project_leray(xi * amp)

    # -- time stepping ------------------------------------------------------

    def cfl_dt(self, u_hat: np.ndarray, cfl: float = 0.4) -> float:
        """Advective CFL step. With IFRK4 the dissipation imposes no limit."""
        umax = max(self.max_velocity(u_hat), 1e-12)
        dx = 2.0 * np.pi / self.n
        return cfl * dx / umax

    def ifrk4_step(self, u_hat: np.ndarray, dt: float) -> np.ndarray:
        """
        Integrating-factor RK4. The linear dissipation is integrated exactly:

            E = exp(L dt),  E2 = exp(L dt/2)
            N1 = N(u);            N2 = N(E2 (u + dt/2 N1))
            N3 = N(E2 u + dt/2 N2); N4 = N(E u + dt E2 N3)
            u+ = E u + (dt/6)(E N1 + 2 E2 (N2 + N3) + N4)

        This removes the O(nu alpha' k^4) stiffness that would otherwise make an
        alpha' sweep over decades computationally impossible.
        """
        E = np.exp(self.diss_symbol * dt)
        E2 = np.exp(self.diss_symbol * dt * 0.5)
        n1 = self.nonlinear_term(u_hat)
        n2 = self.nonlinear_term(E2 * (u_hat + 0.5 * dt * n1))
        n3 = self.nonlinear_term(E2 * u_hat + 0.5 * dt * n2)
        n4 = self.nonlinear_term(E * u_hat + dt * E2 * n3)
        out = E * u_hat + (dt / 6.0) * (E * n1 + 2.0 * E2 * (n2 + n3) + n4)
        return self.project_leray(out)

    def rk4_step_reference(self, t: float, u_hat: np.ndarray, dt: float) -> np.ndarray:
        """
        Plain RK4 using the DualScale package's integrator, for cross-checking
        IFRK4 in non-stiff regimes. Raises if the package is unavailable.
        """
        if not HAVE_DUALSCALE:
            raise RuntimeError(
                "dualscale_solver is not importable; set PYTHONPATH to its src/ directory"
            )
        return _dualscale_rk4_step(self.rhs, t, u_hat, dt, projector=self.project_leray)

    def run(
        self,
        u_hat0: np.ndarray,
        t_end: float,
        dt: Optional[float] = None,
        cfl: float = 0.4,
        diagnostics_every: int = 5,
        monitor: Optional[ValidityMonitor] = None,
        temperature_param: float = 0.0,
        rng: Optional[np.random.Generator] = None,
        stepper: str = "ifrk4",
        progress: Optional[Callable[[float, Dict[str, Any]], None]] = None,
        max_steps: int = 200000,
    ) -> Dict[str, Any]:
        """
        Integrate to t_end, recording diagnostics.

        Returns a dict of time series plus the final state. `dt=None` selects an
        adaptive advective CFL step.
        """
        u_hat = self.project_leray(u_hat0.copy())
        if temperature_param > 0 and rng is None:
            rng = np.random.default_rng(0)

        t = 0.0
        step = 0
        rec: Dict[str, list] = {
            "t": [], "energy": [], "enstrophy": [], "dissipation": [],
            "u_max": [], "omega_max": [], "div_rel": [], "dt": [],
        }

        def record() -> None:
            # Never record the same instant twice: a duplicated final sample puts a
            # zero interval into the time series, which makes np.gradient (and any
            # dE/dt diagnostic built on it) return NaN.
            if rec["t"] and t <= rec["t"][-1]:
                return
            d = self.divergence_report(u_hat)
            rec["t"].append(t)
            rec["energy"].append(self.energy(u_hat))
            rec["enstrophy"].append(self.enstrophy(u_hat))
            rec["dissipation"].append(self.dissipation_rate(u_hat))
            umax = self.max_velocity(u_hat)
            wmax = self.max_vorticity(u_hat)
            rec["u_max"].append(umax)
            rec["omega_max"].append(wmax)
            rec["div_rel"].append(d["div_l2_relative"])
            rec["dt"].append(dt if dt is not None else float("nan"))
            if monitor is not None:
                monitor.update(t, umax, wmax, 2.0 * np.pi / self.k_max_effective)

        record()
        while t < t_end and step < max_steps:
            h = dt if dt is not None else self.cfl_dt(u_hat, cfl)
            h = min(h, t_end - t)
            if h <= 0:
                break
            if stepper == "ifrk4":
                u_hat = self.ifrk4_step(u_hat, h)
            elif stepper == "rk4":
                u_hat = self.rk4_step_reference(t, u_hat, h)
            else:
                raise ValueError(f"unknown stepper {stepper}")

            if temperature_param > 0:
                u_hat = self.project_leray(
                    u_hat + self.thermal_noise_increment(h, temperature_param, rng)
                )

            t += h
            step += 1
            if step % diagnostics_every == 0:
                record()
                if not np.isfinite(rec["energy"][-1]):
                    raise FloatingPointError(f"solution diverged at t={t:.4g}, step {step}")
                if progress is not None:
                    progress(t, {k: v[-1] for k, v in rec.items()})

        record()
        out: Dict[str, Any] = {k: np.asarray(v) for k, v in rec.items()}
        out.update({
            "u_hat_final": u_hat,
            "steps": step,
            "n_grid": self.n,
            "nu": self.nu,
            "alpha_prime": self.alpha_prime,
            # NB: key is *_operator, not "dissipation" -- the latter is the
            # dissipation-rate time series recorded above, and overwriting it
            # with the operator name silently corrupts every energy-balance check.
            "dissipation_operator": self.dissipation,
            "barrier_wavenumber": self.barrier_wavenumber,
            "barrier_resolved": self.barrier_is_resolved(),
        })
        if monitor is not None:
            out["validity"] = monitor.report()
        return out
