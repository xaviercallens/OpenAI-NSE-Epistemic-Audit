import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Viscous heating of the OpenAI collapsing core, water at 300 K, h = 1/200.
#
# Scalings: integrated enstrophy Omega = int |omega|^2 dx ~ tau^(-0.515);
# LOCAL enstrophy density |omega|^2 ~ tau^(-2.010); Delta T ~ tau^(-1.010).
#
# Because the core keeps Re_r = O(1), its radius is the diffusive length
# l_r^2 = nu * t (t = physical time remaining), so the dissipation per unit
# mass eps = nu (u/l_r)^2 acting over t gives Delta T = eps t / c_p = u^2 / c_p
# exactly (Eckert number ~ 1). No calibration constant is needed; an earlier
# version of this script used an illustrative C_dissipation = 1.5e-10 and a
# wrong exponent, which produced a spurious "45.6 ps" boiling time.

NU = 1.0e-6        # m^2/s
C_P = 4184.0       # J/(kg K)
C_S = 1500.0       # m/s
H = 1.0 / 200.0
T_UNIT = 100.0     # s, = l0^2/nu for l0 = 1 cm; enters only as (t/T)^(-h)


def core_velocity(t):
    """u(t) = sqrt(nu/t) * (t/T)^(-h), t = seconds before blow-up."""
    return np.sqrt(NU / t) * (t / T_UNIT) ** (-H)


def calculate_temperature_rise(t):
    """Delta T = u^2 / c_p (viscous heating trapped in the core, Pr >~ 1)."""
    return core_velocity(t) ** 2 / C_P


if __name__ == "__main__":
    t = np.logspace(-9, -14, 400)
    dT = calculate_temperature_rise(t)
    boil = 73.0
    t_boil = t[np.argmin(np.abs(dT - boil))]
    u_boil = core_velocity(t_boil)
    t_ma03 = t[np.argmin(np.abs(core_velocity(t) - 0.3 * C_S))]

    plt.figure(figsize=(8, 5))
    plt.plot(t, dT, 'r-', linewidth=2, label=r'$\Delta T = u^2/c_p$ (water)')
    plt.axhline(boil, color='k', linestyle='--', label='Boiling (+73 K from 300 K)')
    plt.axvline(t_boil, color='k', linestyle=':',
                label=f'boiling at t = {t_boil:.1e} s, Ma = {u_boil / C_S:.2f}')
    plt.axvline(t_ma03, color='b', linestyle=':', label=f'Ma = 0.3 at t = {t_ma03:.1e} s')
    plt.gca().invert_xaxis()
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Physical time before singularity t (s)')
    plt.ylabel('Temperature rise $\\Delta T$ (K)')
    plt.title('Viscous heating of the collapsing core (Eckert ~ 1; upper estimate if Pr < 1)')
    plt.legend(fontsize=8)
    plt.grid(True)
    plt.savefig('thermal_vaporization.png', dpi=200, bbox_inches='tight')
    print(f"Saved thermal_vaporization.png; boiling at t = {t_boil:.2e} s "
          f"(u = {u_boil:.0f} m/s, Ma = {u_boil / C_S:.2f}); Ma=0.3 at t = {t_ma03:.2e} s")
