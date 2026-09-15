"""
Unified Physical Constants and Fluid Property Specifications.
MechanicaFluidorum Program · SocrateAI Lab · September 2026

Central repository for physical constants, thermodynamic boundaries,
and dimensionless scaling parameters used across all audit directives
and verification scripts.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Any


# ==============================================================================
# Universal Fundamental Physical Constants (CODATA Recommended)
# ==============================================================================
BOLTZMANN_CONSTANT: float = 1.380649e-23      # k_B (J / K)
PLANCK_CONSTANT: float = 6.62607015e-34        # h (J · s)
HBAR: float = 1.054571817e-34                  # hbar = h / 2pi (J · s)
SPEED_OF_LIGHT: float = 299792458.0            # c (m / s)
STANDARD_PRESSURE: float = 101325.0            # P_atm (Pa, 1 atm)
AMBIENT_TEMPERATURE: float = 300.0             # T_0 (K, standard reference)


# ==============================================================================
# Fluid Property Specification Dataclass
# ==============================================================================
@dataclass(frozen=True)
class FluidProperties:
    """Immutable thermodynamic and transport properties of a reference fluid."""
    name: str
    speed_of_sound: float           # c_s (m/s)
    kinematic_viscosity: float      # nu (m^2/s)
    density: float                  # rho (kg/m^3)
    isobaric_heat_capacity: float   # c_p (J / (kg · K))
    thermal_conductivity: float     # kappa (W / (m · K))
    mean_free_path: float           # lambda_mfp (m)
    vapor_pressure_300k: float      # P_v (Pa)
    boiling_point: float            # T_boil (K) at 1 atm
    critical_temperature: float     # T_crit (K)
    max_physical_enstrophy: float   # LEGACY, UNJUSTIFIED (s^-2): no derivation exists;
                                    # use max_local_vorticity instead.

    @property
    def max_local_vorticity(self) -> float:
        """Physically motivated local vorticity bound |omega|_max = c_s^2 / nu (s^-1).

        A vortex of speed U and size L has |omega| ~ U/L; the incompressible
        continuum model requires U < c_s (Ma < 1) and L > lambda ~ nu/c_s
        (Kn < 1), hence |omega| < c_s^2/nu. Water: ~2.2e12 s^-1; air: ~7.8e9 s^-1.
        """
        return self.speed_of_sound ** 2 / self.kinematic_viscosity

    @property
    def max_local_dissipation(self) -> float:
        """Corresponding bound on dissipation per unit mass eps = nu*|omega|^2 < c_s^4/nu (W/kg)."""
        return self.speed_of_sound ** 4 / self.kinematic_viscosity

    @property
    def dynamic_viscosity(self) -> float:
        """Dynamic shear viscosity mu = rho * nu (Pa · s)."""
        return self.density * self.kinematic_viscosity

    @property
    def acoustic_impedance(self) -> float:
        """Acoustic impedance Z = rho * c_s (kg / (m^2 · s))."""
        return self.density * self.speed_of_sound


# ==============================================================================
# Standard Fluid Presets
# ==============================================================================
WATER_300K = FluidProperties(
    name="Liquid Water (300 K)",
    speed_of_sound=1500.0,
    kinematic_viscosity=1.0e-6,
    density=1000.0,
    isobaric_heat_capacity=4184.0,
    thermal_conductivity=0.606,
    mean_free_path=3.0e-10,           # Intermolecular spacing
    vapor_pressure_300k=3536.0,
    boiling_point=373.15,
    critical_temperature=647.0,
    max_physical_enstrophy=1.13e13    # UNJUSTIFIED legacy constant -- no derivation exists;
                                      # use max_local_vorticity = c_s^2/nu instead
)

AIR_300K = FluidProperties(
    name="Dry Air (300 K, 1 atm)",
    speed_of_sound=343.0,
    kinematic_viscosity=1.5e-5,
    density=1.204,
    isobaric_heat_capacity=1005.0,
    thermal_conductivity=0.026,
    mean_free_path=6.8e-8,
    vapor_pressure_300k=0.0,
    boiling_point=78.8,
    critical_temperature=132.5,
    max_physical_enstrophy=5.0e11
)

HELIUM_GAS_300K = FluidProperties(
    name="Helium Gas (300 K, 1 atm)",
    speed_of_sound=1007.0,
    kinematic_viscosity=1.2e-4,
    density=0.1786,
    isobaric_heat_capacity=5193.0,
    thermal_conductivity=0.152,
    mean_free_path=1.8e-7,
    vapor_pressure_300k=0.0,
    boiling_point=4.22,
    critical_temperature=5.19,
    max_physical_enstrophy=1.0e11
)

FLUID_PRESETS: Dict[str, FluidProperties] = {
    "water": WATER_300K,
    "air": AIR_300K,
    "helium": HELIUM_GAS_300K
}


# ==============================================================================
# OpenAI Formalization Model Scaling Parameters
# ==============================================================================
# Anisotropy exponent h < 1/100 (Section 2.1)
ANISOTROPY_H_DEFAULT: float = 0.005           # h = 1/200
ANISOTROPY_H_DEFAULT_RAT: Fraction = Fraction(1, 200)
ANISOTROPY_H_MAX: float = 0.01                # 1/100

# Physical admissibility thresholds
MACH_INCOMPRESSIBILITY_LIMIT: float = 0.3     # Ma < 0.3
SONIC_MACH_LIMIT: float = 1.0                 # Ma = 1.0
KNUDSEN_CONTINUUM_LIMIT: float = 0.1          # Kn < 0.1

# Reference macroscopic scales
L_REF_DEFAULT: float = 0.01                   # 1 cm initial core radius (m)

# Dual-scale topological minimal cutoff (alpha')
ALPHA_PRIME_TOPOLOGICAL: float = 1.0e-6


def get_reference_velocity(fluid: FluidProperties = WATER_300K, l_ref: float = L_REF_DEFAULT) -> float:
    """Calculates reference viscous velocity scale u_ref = nu / L_ref."""
    return fluid.kinematic_viscosity / l_ref


def as_dict() -> Dict[str, Any]:
    """Serializes constants to a structured dictionary for JSON telemetry."""
    return {
        "constants": {
            "k_B": BOLTZMANN_CONSTANT,
            "hbar": HBAR,
            "c": SPEED_OF_LIGHT,
            "T_0": AMBIENT_TEMPERATURE,
            "P_atm": STANDARD_PRESSURE
        },
        "thresholds": {
            "mach_limit": MACH_INCOMPRESSIBILITY_LIMIT,
            "knudsen_limit": KNUDSEN_CONTINUUM_LIMIT,
            "anisotropy_h_default": ANISOTROPY_H_DEFAULT,
            "alpha_prime": ALPHA_PRIME_TOPOLOGICAL
        },
        "fluids": {
            k: {
                "name": v.name,
                "c_s": v.speed_of_sound,
                "nu": v.kinematic_viscosity,
                "rho": v.density,
                "c_p": v.isobaric_heat_capacity,
                "mean_free_path": v.mean_free_path,
                "max_enstrophy_legacy_unjustified": v.max_physical_enstrophy,
                "max_local_vorticity": v.max_local_vorticity
            }
            for k, v in FLUID_PRESETS.items()
        }
    }
