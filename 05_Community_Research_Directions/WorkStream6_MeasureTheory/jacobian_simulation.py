import numpy as np
import matplotlib.pyplot as plt
import os

# Deterministic (NOT Monte Carlo -- this script contains no randomness; a
# previous version was titled "Monte Carlo" despite that) noise-amplification
# sweep using the RAW/UNSCALED Jacobian condition number kappa(A) ~ 10^28.
#
# IMPORTANT CAVEAT (see 01_Verification_Paper/OpenAI_NSE_Verification.tex
# Sec. 3 "Matrix Scaling & Non-Dimensionalization"): this raw kappa(A) is a
# non-dimensionalization artifact of mixing terms spanning X_R^0..X_R^8 in
# an unscaled basis. Once properly non-dimensionalized (A = D*B*D), the
# condition number kappa(B) ~ 4.11e5 is well-conditioned and INDEPENDENT of
# X_R -- it shows none of the amplification plotted below. The plot below is
# a study of what the *raw, unscaled* number would imply if taken at face
# value; it is not evidence of physical fine-tuning or fragility once the
# proper non-dimensionalization is applied.

lambdas = np.logspace(-1, -4, 50)
# Condition number scaling kappa ~ lambda^(-3.00) * X_R^7.75 (RAW, UNSCALED --
# see caveat above)
# For a fixed X_R = 1000, X_R^7.75 ~ 10^23.25
kappa_raw_unscaled = (lambdas**-3.0) * (1000**7.75)

# Input noise: Thermal fluctuations (approx 10^-9 m/s)
noise_level = 1e-9
output_error = noise_level * kappa_raw_unscaled

plt.figure(figsize=(8,5))
plt.loglog(lambdas, output_error, 'r-', linewidth=2, label='Amplified error (raw, unscaled $\\kappa(A)$)')
plt.axhline(1.0, color='k', linestyle='--', label='Macroscopic Breakdown (Error = 1.0)')
plt.axhline(noise_level * 4.11e5, color='g', linestyle=':', linewidth=2,
            label='Same noise x properly-scaled $\\kappa(B)\\approx4.11\\times10^5$ (flat, well-conditioned)')

plt.gca().invert_xaxis()  # lambda goes to 0
plt.xlabel('Transition Scale $\\lambda$ (approaching 0)')
plt.ylabel('Reynolds-Stress Alignment Error')
plt.title('Deterministic Noise-Amplification Sweep, RAW UNSCALED $\\kappa(A)$\n(see script comment: this is a non-dimensionalization artifact, not physical fragility)')
plt.grid(True, which="both", ls="--")
plt.legend(fontsize=8)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jacobian_monte_carlo.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Saved {out_path}")
print("NOTE: this sweep uses the RAW/UNSCALED kappa(A); the properly non-dimensionalized")
print("kappa(B)~4.11e5 is flat/well-conditioned and does not show this amplification.")
