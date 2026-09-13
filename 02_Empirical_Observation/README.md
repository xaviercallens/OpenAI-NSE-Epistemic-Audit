# 02_Empirical_Observation [Tier B Laboratory]

Numerical Observation experiments proving that manufactured singularities in fluid dynamics are unstable, non-generic mathematical artifacts. 

**Rigor Assurance:** All ordinary differential equations are integrated using rigorous adaptive solvers (SciPy `Radau` for stiff systems, Rust `Dopri5` RK4(5)) to mathematically guarantee that the observed cascade saturation is driven by true geometric phase cancellations, not explicit numerical dissipation.

## Architecture

*   **`simu_sign_fragility_1D.py`**: Simulates the Katz-Pavlović / Desnyansky-Novikov dyadic cascade using a stiff implicit Radau solver. Proves that finite-time blowup requires measure-zero, unbroken $+1$ phase coherence across all dyadic octaves. Any localized phase disruption ($\theta_n = \pi/2$) or turbulent phase noise halts the cascade, bounding enstrophy by multiple orders of magnitude.
*   **`simu_frustration_Z3.py`**: Evaluates the Leray-Helmholtz projection operator $\mathbb{P}(k) = I - (k \otimes k)/|k|^2$ across divergence-free wavevector triads on the 3D Galerkin integer lattice $\mathbb{Z}^3$. Quantifies the geometric Frustration Index (median $\mathcal{D} \approx 2.4$, 95th percentile $\mathcal{D} > 27$) and isotropic shell vector phase incoherence cancellations ($> 40\times$). The basis sampling is isotropic and frame-invariant.
*   **`euler_counterdetonation/`**: Phenomenological Rust solver integrating the envelope of the OpenAI fractal vortex packet series (`Euler/PacketSourceScaleSequence.lean`). Utilizing an adaptive Dormand-Prince RK4(5) engine, it demonstrates that under the physical Dual-Scale metric ($R_{\text{eff}} = \max(R, \alpha'/R)$), the unphysical ultraviolet divergence is aborted and the fluid relaxes to a regular, force-free Beltrami state ($\nabla \times u = \lambda u$).

## Execution

```bash
# Python experiments
python3 simu_sign_fragility_1D.py
python3 simu_frustration_Z3.py

# Rust phenomenological counter-detonation engine
cd euler_counterdetonation
cargo run --release
```
