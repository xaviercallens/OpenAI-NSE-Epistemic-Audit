# md_core_rs — molecular dynamics of the forced collapsing core

The **thermal kinetic test** of the Mach lock found in `../experiments/compressible_core.py`, and an
exploratory cavitation run in a liquid. Molecular dynamics has no continuum closure: no viscosity law, no
Fourier law, no equation of state is put in. If the lock appears here it is not an artefact of the
Navier–Stokes–Fourier model.

## Model

Truncated-shifted Lennard-Jones particles (σ = ε = m = 1, r_c = 2.5) in a periodic slab `L × L × Lz`
(`Lz = 8`), velocity Verlet, cell lists with a Verlet skin, rayon-parallel forces. The column vortex is
along `z`. The force is the same as in every forced-core experiment of this project — the residual of
the *incompressible, constant-viscosity* equations on a time-reversed Lamb–Oseen core, per unit mass:
`f_θ(r,t) = 2.5 ν r ω/ℓ²`, `ω = Γ/(πℓ²) exp(−r²/ℓ²)`, `ℓ² = ν(T_blow − t)`, `Γ = 2πν Re/0.63817`.
Outside `R_b = 3.2 ℓ_start` a Langevin thermostat acts on the velocity *relative to the potential vortex*
`Γ/(2πr) e_θ` at `T_∞`: it holds the far field, removes the heat the force injects and absorbs sound. No
thermostat acts inside `R_b`.

State points: gas `ρ = 0.15, T = 2.0` (mean free path 1.49σ); liquid `ρ = 0.79, T = 1.0`
(`p = 1.48`, single phase).

## Validation gates (`../experiments/results/md_core_gates.json`)

| gate | result |
|---|---|
| M1 NVE energy drift / KE per particle | 1×10⁻⁵ (N = 84,100, 4k steps), 4×10⁻⁵ (N = 7,744, 20k steps); momentum exact |
| M2 equilibrium | pressure 0.2816 vs third-virial EOS 0.2794 (+0.8%; second virial alone −5.7%); kurtosis 3.00; temperature within 0.4% in the production-size box. The two small boxes sit 1.3–1.4% from target — the NVE fluctuation √(2/3N) of a 7.7k-particle sample — so the formal 1% criterion fails for them and passes for the big box |
| M3 sound speed | real-gas adiabatic `c = 1.981` from the third-virial EOS (ideal `√(γT)` = 1.826); local Mach numbers use `√(γ T_loc)`, γ = 5/3 (approximate) |
| M4 viscosity, in situ | shear-wave decay, 14 runs, three wavenumbers: **ν = 1.71 ± 0.07**; free decay of a Lamb–Oseen vortex, 4 seeds: 1.87 ± 0.18; modified Enskog 1.83; dilute Chapman–Enskog 1.41. `ν = 1.70` is used in the force. Liquid: ν ≈ 2.5 (3 runs) |
| M5 thermostat buffer | inner temperature within 0.6% of `T_∞` and far-field swirl within 4% of `Γ/2πr` over the free-decay runs |

Hence `ℓ* = ν/c = 0.86σ = 0.58 λ`, and the sonic scale at Re = 16 is `Re ℓ* ≈ 14σ ≈ 9 λ`.

## Forced runs

`jobs_forced_a.txt`, `jobs_forced_b.txt`: gas, `L = 300` (107,584 particles), core driven from 40σ to 4σ
(target Mach 0.34 → 3.4 at Re = 16), three seeds at Re = 16, one each at Re = 4 and Re = 32; liquid,
`L = 160`, Re = 4, 20σ → 3σ, one seed. Results and the comparison with the continuum prediction registered
beforehand are in `../THERMO_COMPRESSIBLE_LOCK_STUDY.md` §7–8 and
`../experiments/results/md_core_runs.json`.

## Limitations

Thin slab (`Lz = 8σ`): the flow is quasi-two-dimensional, with no axial structure or three-dimensional
instability. Truncated potential. Thermal noise is large (`v_th ≈ 1.4` against swirl speeds of 0.7–3), so
every number is an ensemble mean with its standard error, and the peak local Mach number is taken from a
smoothed profile as well as from the raw maximum (which is biased upward by noise). Local Mach numbers use
an ideal-gas sound speed in a mildly non-ideal gas. The buffer is a thermostat, not an open boundary.
Small ensembles.

## Reproduce

```bash
cargo build --offline --release && cargo test --offline --release
sh run_queue.sh jobs_gates.txt && sh run_queue.sh jobs_shear.txt && sh run_queue.sh jobs_shear2.txt
sh run_queue.sh jobs_forced_a.txt & sh run_queue.sh jobs_forced_b.txt &     # ~1-1.5 h per gas run
python3 ../experiments/analyse_md_core.py
```
