# 02_Empirical_Falsification [Tier B Laboratory]

Numerical falsification experiments proving that manufactured singularities in fluid dynamics are unstable, non-generic mathematical artifacts.

## Architecture

*   **`simu_sign_fragility_1D.py`**: Simulates the Katz-Pavlović / Desnyansky-Novikov dyadic cascade. Proves that finite-time blowup requires measure-zero, unbroken $+1$ phase coherence across all dyadic octaves. Any localized phase disruption ($\theta_n = \pi/2$) or turbulent phase noise halts the cascade, bounding enstrophy by multiple orders of magnitude.
*   **`simu_frustration_Z3.py`**: Evaluates the Leray-Helmholtz projection operator $\mathbb{P}(k) = I - (k \otimes k)/|k|^2$ across divergence-free wavevector triads on the 3D Galerkin integer lattice $\mathbb{Z}^3$. Quantifies the geometric Frustration Index $\mathcal{D} \gg 10$ and net shell parity cancellations ($D_{\text{shell}} > 100$).
*   **`euler_counterdetonation/`**: High-performance Rust solver intercepting the OpenAI fractal vortex packet series (`Euler/PacketSourceScaleSequence.lean`). Under the physical Dual-Scale metric ($R_{\text{eff}} = \max(R, \alpha'/R)$), the unphysical ultraviolet divergence is aborted and the fluid relaxes to a regular, force-free Beltrami state ($\nabla \times u = \lambda u$).

## Execution

```bash
# Python experiments
python3 simu_sign_fragility_1D.py
python3 simu_frustration_Z3.py

# Rust counter-detonation engine
cd euler_counterdetonation
cargo run --release
```
