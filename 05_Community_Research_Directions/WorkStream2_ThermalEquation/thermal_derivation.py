import numpy as np
import matplotlib.pyplot as plt

def calculate_temperature_rise(tau):
    """
    Simulates the temperature rise Delta T(tau) driven by 
    enstrophy divergence tau^(-2.515) in water.
    """
    rho = 1000 # kg/m^3
    cp = 4184  # J/(kg K)
    mu = 8.9e-4 # Pa s
    
    # Asymptotic scaling constants from OpenAI Lemma 8.7 extraction
    C_dissipation = 1.5e-10 
    
    # Delta T ~ integral of dissipation 
    # Simplified power-law fit for the pre-singularity regime
    delta_T = C_dissipation * (tau ** -1.515) / (rho * cp)
    return delta_T

taus = np.logspace(-10, -12, 100)
temps = calculate_temperature_rise(taus)

plt.figure(figsize=(8,5))
plt.plot(taus, temps, 'r-', linewidth=2)
plt.axhline(73, color='k', linestyle='--', label='Boiling Point (+73K from 300K)')
plt.gca().invert_xaxis()
plt.xscale('log')
plt.yscale('log')
plt.xlabel('Time to singularity tau (s)')
plt.ylabel('Temperature Rise Delta T (K)')
plt.title('Vaporization by Pure Force (Thermal Shock)')
plt.legend()
plt.grid(True)
plt.savefig('thermal_vaporization.png')
print("Saved thermal_vaporization.png")
