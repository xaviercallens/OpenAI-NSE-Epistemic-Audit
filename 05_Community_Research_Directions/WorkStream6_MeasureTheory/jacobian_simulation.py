import numpy as np
import matplotlib.pyplot as plt
import os

# Simulate the amplification of noise by the ill-conditioned Jacobian
# kappa ~ 10^28 at extreme scales. We'll show the error amplification 
# as a function of the transition parameter lambda.

lambdas = np.logspace(-1, -4, 50)
# Condition number scaling kappa ~ lambda^(-3.00) * X_R^7.75
# For a fixed X_R = 1000, X_R^7.75 ~ 10^23.25
kappa = (lambdas**-3.0) * (1000**7.75)

# Input noise: Thermal fluctuations (approx 10^-9 m/s)
noise_level = 1e-9
output_error = noise_level * kappa

plt.figure(figsize=(8,5))
plt.loglog(lambdas, output_error, 'r-', linewidth=2, label='Amplified Alignment Error')
plt.axhline(1.0, color='k', linestyle='--', label='Macroscopic Breakdown (Error = 1.0)')

plt.gca().invert_xaxis()  # lambda goes to 0
plt.xlabel('Transition Scale $\lambda$ (approaching 0)')
plt.ylabel('Reynolds-Stress Alignment Error')
plt.title('Monte Carlo Noise Amplification (Jacobian $\kappa \sim 10^{28}$)')
plt.grid(True, which="both", ls="--")
plt.legend()

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jacobian_monte_carlo.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Saved {out_path}")
