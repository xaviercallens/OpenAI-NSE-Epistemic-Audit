# kinetic_lock_rs — does a forced core arrest at the kinetic cutoff?

This is a nonlinear test of the kinetic link in the dual-scale-lock chain. The linear BGK shear spectrum (`experiments/lock_k_kinetic_spectrum.py`) shows that the hydrodynamic shear mode **terminates** at kλ = √(π/2) ≈ 1.2533. It is not a stronger drain. The question tested here is whether a collapsing, forced vortex core in a kinetic (BGK) fluid then **stops shrinking** at a scale fixed by λ. If it does:

- (a) how does ℓ_arrest scale with λ?
- (b) does k_ω·λ at arrest equal √(π/2), and is it the same at Re_core = 1 and 0.25?
- (c) what does a Navier–Stokes control, driven by the identical forcing on the identical grid, do?

## Result: no kinetic arrest. The "arrest" follows the grid, not λ.

All numbers below are in `experiments/results/kinetic_lock_collapse.json`, and the figure is `experiments/results/kinetic_lock.png`. Every verdict is computed by `collapse_analyze` from the run arrays. The runs use Q = 24, dt = τ/20 and ℓ_start = 4λ unless stated otherwise.

1. **Before any "arrest", the kinetic core is *ahead* of the target, not behind it.** The lag reaches −11.4% at Re = 1 and −12.2% at Re = 0.25, identically in every run.
   - This is the linear result in nonlinear form: kinetic damping is *below* νk² (the Burnett coefficient is +1).
   - The effect is amplified by the forcing, which cancels 4/5 of the viscous term: the net contraction is ¼νk².
   - A drain would give a positive lag. None is seen.
2. **The lag > 10% event and min ℓ_kin move with the grid.** The table is the resolution ladder at λ = 0.065:

   | N | dx/λ | grid floor ℓ_ref,min/λ | Re=1: ℓ_kin/λ at lag>10% | k_ωλ | Mach | Re=0.25: ℓ_kin/λ | k_ωλ | Mach |
   |---|---|---|---|---|---|---|---|---|
   | 144 | 0.67 | 0.84 | 0.98 | 1.79 | 1.72 | 0.96 | 2.26 | 0.72 |
   | 288 | 0.34 | 0.44 | 0.70 | 2.31 | 2.19 | 0.54 | 3.59 | 1.42 |
   | 576 | 0.17 | 0.23 | 0.52 | 4.19 | 2.87 | 0.35 | 4.91 | 2.15 |

   Halving dx halves the estimator floor and pulls the "arrest" to smaller ℓ and larger k_ωλ, with no sign of convergence. At the finest grid the core is at k_ωλ ≈ 4–5, far past both √(π/2) = 1.2533 and the Q = 24 lattice termination at 0.8877.
3. **The lattice is not what stops the core.** At λ = 0.065 and N = 288:
   - Re = 0.25 with Q = 12, 16 and 24 gives ℓ_kin/λ at lag > 10% of 0.5368, 0.5368 and 0.5369.
   - Re = 1 with Q = 16 and 24 gives 0.701 and 0.699.
4. **The start length does not matter.** ℓ_start/λ = 4, 8 and 12 give 0.9840, 0.9827 and 0.9827 (Re = 1, N = 144).

### (a) Exponent of ℓ_arrest in λ (OLS in logs, 95% CI, 4 λ values)

| sweep | Re_core | slope, min ℓ_kin | slope, ℓ_kin at lag>10% |
|---|---|---|---|
| dx/λ fixed ≈ 0.67 (N = 486, 324, 216, 144) | 1 | 0.93 [0.90, 0.97] | 0.93 [0.88, 0.98] |
| dx/λ fixed ≈ 0.67 | 0.25 | 0.95 [0.90, 1.01] | 0.98 [0.92, 1.03] |
| **grid fixed, N = 288** | 1 | **0.35 [0.18, 0.51]** | 0.32 [0.09, 0.54] |
| **grid fixed, N = 288** | 0.25 | **0.19 [0.09, 0.30]** | 0.09 [−0.01, 0.18] |

When the grid spacing is scaled with λ, ℓ_arrest ∝ λ^0.93–0.95, which is what dimensional analysis forces. When the grid is held fixed, the exponent collapses to 0.1–0.35. So ℓ_arrest tracks dx, not λ.

In the main sweep, ℓ_arrest/grid floor is 1.03–1.04 at Re = 0.25 and 1.17–1.21 at Re = 1: the minimum sits on the estimator's floor.

### (b) k_ω·λ at arrest vs √(π/2)

In the dx/λ ≈ 0.67 sweep:

| Re_core | k_ωλ at lag > 10% | 95% CI | ratio to √(π/2) | CI contains √(π/2)? |
|---|---|---|---|---|
| 1 | 1.72 | [1.62, 1.81] | 1.37 | no |
| 0.25 | 2.20 | [2.07, 2.32] | 1.75 | no |

- **Same at both Re? No.** The difference (Re 1 − Re 0.25) is −0.48 [−0.60, −0.36].
- The value is resolution-dependent: at λ = 0.065 it rises to 4.19 (Re = 1) and 4.91 (Re = 0.25) at N = 576.
- It does not equal √(π/2) and it is not a constant.

### (c) NSE control, same forcing and grid

- The NSE control tracks the truncated target: |lag| ≤ 4e-4 through the kinetic "arrest" in every main-sweep run, and ≤ 3e-2 in all runs.
- It never lags > 10% except at N = 288/576 with Re = 0.25, and there only at ℓ_target ≤ 0.32λ, i.e. below the kinetic event, where the grid floor dominates both.
- Grid effects alone therefore do not produce the kinetic lag. The kinetic core departs from the target before NSE does. But the departure point moves with dx, so it is a kinetic + grid event, not a λ-set lock.

### What the kinetic event actually coincides with

- **Re = 1.** The core is compressible and supersonic long before any arrest:
  - Mach at lag > 10% is 1.64 on average, with max|ρ−1| = 0.82–0.98.
  - The negative-mass fraction exceeds the G5 tolerance (up to 3.6e-5 > 1e-6) once Mach ≳ 1.1, at ℓ_target ≈ 1.3λ.
  - In that regime the spectral-streaming lattice solution is **outside its validated envelope**. The finest Re = 1 run stopped at Mach 6.6, ℓ_target = 0.22λ.
- **Re = 0.25.** Positivity holds up to the arrest on the coarse grids (4.5e-8), but fails on the finer grids (up to 1.1e-5), where the event happens at Mach 1.4–2.2.
- In both cases the core reaches Mach ≈ 1 near ℓ ≈ Re_core·λ, as Ma ≈ Re·Kn predicts. Compressibility sets in *before* or *at* the would-be kinetic scale.

**Verdict.** In this forced 2D-2V isothermal BGK test, the core does not arrest at k_ωλ ≈ √(π/2). It keeps shrinking with the forcing, running ahead of Navier–Stokes, until the grid floor or the loss of lattice validity (Mach > 1, negative f) stops the measurement. The "lock" is a termination of the linear hydrodynamic mode, not an arrest mechanism for a driven core. This is a null result for the lock.

**Limits of this conclusion:**
- It is 2D, isothermal and BGK (no energy equation, no shocks physics beyond isothermal), with Q ≤ 24.
- The target forcing is the NSE residual, applied unchanged.
- Resolution only reaches dx = λ/6.
- A different forcing, one not tied to the NSE solution, could behave differently.


## Model

Isothermal BGK in 2D space × 2D velocity, on the periodic square [0, 2π)².

- **Units.** v_th = c_s = 1 (RT = 1) and ν = τ = λ, so the Knudsen number is Kn = λ/ℓ and q = kλ.
- **Velocity space.** A tensor Gauss–Hermite lattice with Q×Q nodes, Q ∈ {12, 16, 24}. The nodes use Golub–Welsch plus a Newton polish on the orthonormal Hermite recurrence, with weights w = 1/(Q h_{Q−1}²). The nodes are made exactly symmetric and the weights sum to 1.
- **Equilibrium.** The entropic discrete Maxwellian, feq = ρ w exp(b·v)/Z(b). It minimises H = Σ f ln(f/w) under mass and momentum constraints and factorises into two strictly monotone 1D Newton solves for b(u).
  - Newton is warm-started from a cubic-Hermite table of b(u).
  - Once the Newton step is below 1e-8, the last exponential evaluation is corrected to first order. This keeps the moments exact to roundoff, and the departure from the exact entropic tilt is O(1e-16).
- **Time stepping.** Strang splitting, A(h/2)·S(h)·A(h/2):
  - S is exact Fourier free streaming: the separable spectral shift f̂ ← f̂ e^{−ik·v h}, with the Nyquist mode kept real.
  - A is the exact BGK exponential f ← feq + (f − feq) e^{−s/τ}, combined with **exact-difference forcing**, f ← a(f − feq(u)) + feq(u + g s). This single formula equals both "collide then force" and "force then collide", which is why consecutive half-steps can be merged.
  - The momentum added is exactly ρ g s, and the momentum balance closes to about 1e-15.
- **Forced target.** The target is that of `experiments/forced_core.py` in 2D: ω = Γ/(πℓ²) e^{−r²/ℓ²}, with ℓ² = ν(T − t), T = ℓ0²/ν, ℓ0 = 0.8 and Γ = 2πν Re_core/0.63817. It is built **spectrally** (Nyquist-truncated) so that it is defined for every ℓ ≥ 0.
  - The forcing per unit mass is the incompressible-NSE residual of the target. For the axisymmetric column this is ĝ_ω = (5/4)νk² ω̂_target.
  - The initial state is the target velocity with the isothermal cyclostrophic density (∇ ln ρ = −u·∇u) at entropic equilibrium.
  - Runs start on the target trajectory at ℓ_start = 4λ and run to T. The start length does not matter: ℓ_start/λ = 4, 8 and 12 give the same lag crossing to 0.2% (table below).
- **Diagnostics.** These are computed from f every 10 steps, and every step once ℓ_target < 2λ:
  - ℓ_kin: the forced_core.py `ell_from_moment` estimator, applied to the vorticity of u = j/ρ.
  - ℓ_ref: the same estimator applied to the truncated target on the same grid. The lag is ℓ_kin/ℓ_ref − 1, so the estimator's own grid bias cancels.
  - k_ω = √(Σk²|ω̂|²/Σ|ω̂|²), which equals √2/ℓ for a Gaussian.
  - Mach = max|u|, Kn = λ/ℓ_kin, max|ρ−1|, and the non-equilibrium fraction ‖f − feq‖₁/‖f‖₁.
  - H, the negative-mass fraction, the mass drift, and the momentum-balance residual.
  - Two more-local size estimators: a windowed moment over r < 6λ, and the peak-based √(Γ/πω_max).
- **Arrest.** The arrest is the first sample with lag > 10%, and ℓ_arrest is the minimum of ℓ_kin over the run.
- **NSE control.** 2D incompressible vorticity equation with the same spectral target forcing, on the same grid. It uses an integrating-factor RK4 with 2/3 dealiasing and CFL-limited substeps.
- **Stop rule.** If the flow leaves the range the lattice represents, the run stops, keeps everything recorded so far, and records the reason in `termination`. The trigger is either a sampled Mach ≥ ½ v_max, or any velocity that would leave the node span.

## Validation gates (`cargo run --release --features sundials --bin gates -- --dt-over-tau 0.05`)

The results are in `experiments/results/kinetic_lock_gates.json`. All gates pass at the time step used for the collapse runs, dt = τ/20.

| gate | criterion | result |
|---|---|---|
| G1 Newton equilibrium | moments exact to 1e-13; b → u | worst relative moment residual **1.1e-15** (Q = 12/16/24, ρ ∈ {0.5, 1, 1.7}, \|u\| ≤ 2). \|b−u\| is non-increasing in Q. At u = 2: 5.1e-8 (Q=12), 1.8e-12 (Q=16), 2.2e-16 (Q=24). At \|u\| ≤ 1 it is below 1.4e-14 for all Q. **pass** |
| G2 exact collision | mass/momentum to 1e-13; H non-increasing | conservation **2.3e-15**; largest H change −8.2e-7 (strictly decreasing in 6000 far-from-equilibrium steps); exact-difference force momentum residual 1.5e-15. **pass** |
| G3 rusty-SUNDIALS CVODE | independent integrator agrees | nonlinear relaxation vs CVODE BDF: max error 1.7e-7 of max f/w (CVODE's tightest accepted rtol is 1e-8). Full Strang solver vs CVODE on the Q = 24 transverse ODE at q = 0.5: error 5.7e-4 at dt = τ/20 and 1.4e-4 at τ/40, observed order **2.00**. **pass** |
| G4 shear wave vs exact BGK | Q=24, q ≤ 1.0: rate within 2% | the solver's k = 1 history equals the exact Strang propagator Pⁿ to **1.5e-9**; decay rate (least-damped eigenvalue of P) vs M1 below. **pass** |
| G5 positivity | negative mass ≤ 1e-6 | Taylor–Green, Mach 0.3/0.6, τ = 0.02/0.1, Q = 24: negative mass **0**; mass drift 1e-13. **pass** |

G4 detail at dt = τ/20: the solver rate Γτ, the relative error vs exact BGK, and the lattice mode type.

| q = kλ | 0.05 | 0.2 | 0.5 | 0.8 | 1.0 | 1.2 | 1.5 | 2.0 |
|---|---|---|---|---|---|---|---|---|
| exact BGK Γτ | 0.00249 | 0.0386 | 0.2141 | 0.4827 | 0.6974 | 0.9338 | none | none |
| Q=24 solver Γτ | 0.00249 | 0.0386 | 0.2141 | 0.4922 | 0.6937 | 0.7151 | 0.7321 | 0.7446 |
| rel. err | 0.02% | 0.02% | 0.03% | **1.97%** | 0.52% | 23% | — | — |
| mode | real | real | real | real | complex (ωτ = 0.18) | complex | complex | complex |

**Caveats that G4 exposes:**
- **Thin margin at q = 0.8.** Q = 24 passes at q = 0.8 by only 0.03 points. The continuous-time lattice itself is 1.94% off; Strang splitting adds 0.03% at τ/20 and 0.12% at τ/10. The same gates **fail at dt = τ/10** (2.06%), recorded in `logs/gates_dt0.1.json`, which is why the collapse runs use τ/20.
- **The q = 1.0 pass is on Re s only.** Discrete lattices terminate early: the least-damped mode becomes complex at q = 0.797 (Q=12), 0.836 (Q=16) and 0.888 (Q=24). So at q = 1.0 the Q = 24 "hydrodynamic" mode is already a complex pair, and the gate passes on its real part only. Above the exact termination, the lattice keeps spurious least-damped modes with rates of about 0.7/τ. This is why the Q-independence in the result above matters: the collapse behaviour does not depend on where the lattice terminates.
- **M1 reference check.** The Rust exact-BGK dispersion (erfcx root) matches `lock_k_kinetic_spectrum.json` to 5.6e-12 over 168 points.
- **Collapse bookkeeping.** Every collapse run conserves mass to 5e-14, and the momentum balance (P − P0 − ∫ρg) closes to 1.3e-15.


## Reproduce

```sh
cd kinetic_lock_rs
cargo test  --offline --release --features sundials          # G1/G2 unit tests
RAYON_NUM_THREADS=4 cargo run --offline --release --features sundials --bin gates -- --dt-over-tau 0.05
cargo build --offline --release --features sundials
./run_queue.sh jobs_stage2.txt && ./run_queue.sh jobs_stage3.txt   # runs/*.json (git-ignored); runs/res_* and ls12 used --lstart 8/12 (see jobs files and logs/)
./target/release/collapse_analyze --main runs/main_*.json \
    --fixn runs/fixn_*.json runs/ls4_l0.065_re1_n288.json runs/ls4_l0.065_re0.25_n288.json \
    --fine runs/fine_*.json runs/ls4_l0.065_re1_n576.json runs/ls4_l0.065_re0.25_n576.json \
    --extra runs/res_l0.065_re1_n144.json runs/ls12_l0.065_re1_n144.json runs/q1*.json \
    --gates ../experiments/results/kinetic_lock_gates.json --out ../experiments/results/kinetic_lock_collapse.json
python3 ../experiments/plot_kinetic_lock.py
```

## What was used from rusty-SUNDIALS, runux-ai-runtime and DualScale, and why

- **rusty-SUNDIALS (`~/xdev/rusty-SUNDIALS`, crates `cvode` and `nvector`): used for G3 only.** It is a read-only, optional path dependency behind the `sundials` feature, and it builds offline. CVODE supplies an independent integrator for two checks:
  - the nonlinear homogeneous relaxation df/dt = (feq(f) − f)/τ, with the entropic Newton equilibrium inside the RHS;
  - the Q-node linear transverse ODE, against which the full Strang solver is checked.

  Two limitations were found and are recorded in the gates JSON (`attempts_*`):
  - CVODE BDF in this port rejects rtol below 1e-8 on the relaxation problem and below 1e-9 on the shear ODE ("local error test failed > max times"), so G3 uses the tightest tolerance it accepts.
  - The states had to be rescaled to f/w, because the raw f spans 1e-35 to 1e-1 and defeats CVODE's error weights.

  Nothing in rusty-SUNDIALS was modified. Its working tree already had uncommitted user changes in `crates/cvode/src/solver.rs`, which were used as found.
- **runux-ai-runtime (`crates/navier_stokes`, `interval_arith`): not used.** Its Navier–Stokes solver is a spectral Galerkin triad code with O(M⁶) interactions, built for rigorous small-mode enclosures. It has no kinetic streaming or collision operator, and the interval arithmetic cannot help a 10⁸-DOF floating-point kinetic run. Pulling it in would have added a dependency chain (`ai_runtime`, `arena_mem`) without adding any capability this test needs.
- **DualScale solver (`crates/leanflow-core`): not used.** It provides the dual-scale hyperviscous and α-model dissipation (`r_eff`, `k_eff`, `dualscale_dissipation_rate`, `FourierVelocity2D`). This test is about a kinetic cutoff, not a hyperviscous barrier. The only overlapping piece, a 2D Fourier velocity field, is 30 lines here. Linking a crate with uncommitted user work, for that, was not justified.
- **External crates (all offline, from the local registry):** `rustfft` 6.4.1, `rayon` 1.12, `num-complex` 0.4.6, `nalgebra` 0.34 (dense eigenvalues for G4, OLS), `serde_json`.

