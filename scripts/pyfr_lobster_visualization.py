import numpy as np
import matplotlib.pyplot as plt
import os

# A funny visualization (illustration only, not a physical result) of a lobster near an OpenAI
# Navier-Stokes singularity. The "Thermodynamic Censorship shield" of earlier versions is a withdrawn
# framing: nothing shields a fluid from a blow-up of a model; the model simply stops applying at
# l* = nu/c_s (see README "Current status").

t = np.linspace(0, 2*np.pi, 1000)
# Draw a rough "lobster" shape
x_lob = 0.5 * np.cos(t)
y_lob = 0.2 * np.sin(t)
x_claw1 = 0.6 + 0.2 * np.cos(t)
y_claw1 = 0.2 + 0.1 * np.sin(t)
x_claw2 = 0.6 + 0.2 * np.cos(t)
y_claw2 = -0.2 + 0.1 * np.sin(t)

# The Singularity vortex (OpenAI)
theta = np.linspace(0, 8*np.pi, 1000)
r = theta**1.5
x_vortex = r * np.cos(theta) * 0.05
y_vortex = r * np.sin(theta) * 0.05

plt.figure(figsize=(10, 8))
plt.style.use('dark_background')

# Plot the violent AI singularity
plt.plot(x_vortex, y_vortex, 'r-', lw=2, alpha=0.6, label="Mathematical Singularity (Infinite Energy)")
plt.plot(-x_vortex, -y_vortex, 'm-', lw=2, alpha=0.6)

# The continuum-validity boundary (drawn as a circle; illustrative)
circle = plt.Circle((0, 0), 1.0, color='cyan', fill=False, lw=4, label="Where the continuum model stops applying (illustrative)")
plt.gca().add_patch(circle)

# Plot the lobster
plt.plot(x_lob, y_lob, 'orange', lw=3, label="The Lobster (Surviving)")
plt.plot(x_claw1, y_claw1, 'orange', lw=3)
plt.plot(x_claw2, y_claw2, 'orange', lw=3)

# Add text
plt.text(-0.4, 0, "🦞 Unharmed!", color='white', fontsize=15, fontweight='bold')

plt.xlim(-4, 4)
plt.ylim(-4, 4)
plt.title("Why the Lobster Survived the OpenAI Singularity\n(illustration: the model ends at l* = nu/c_s; PyFR concepts)", fontsize=14)
plt.legend(loc='upper right')
plt.axis('off')

out_path = os.path.join(os.path.dirname(__file__), "../dataset/animations/lobster_survival.png")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Lobster visualization saved to {out_path}")
