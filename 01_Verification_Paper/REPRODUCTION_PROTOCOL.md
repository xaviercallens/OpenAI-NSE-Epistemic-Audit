# Reproduction Protocol: Physical Verification of OpenAI's Navier-Stokes Formalization

This protocol provides step-by-step instructions for peer reviewers, fluid dynamicists, and formal verification researchers to independently reproduce the original directive results of the physical reading.

> **Scope and status (v5.5.0).** OpenAI's Lean proofs are correct; these steps reproduce a *physical reading* of them,
> not a refutation. This file covers the original directives (Steps 1–6). The later results — the 3D spectral solver,
> forced collapsing core, kinetic BGK and compressible/thermal simulations, and all nine verified Lean files — are
> regenerated and checked by `scripts/run_benchmarks.sh`; see [`../BENCHMARKS.md`](../BENCHMARKS.md).

---

## 1. Prerequisites

- Linux or macOS system (x86_64 or aarch64)
- Python $\ge$ 3.10 with `numpy`, `scipy`, `sympy`, `requests`
- `git`
- (Optional for Lean 4 formalization) `elan` and `lake` with Lean 4 toolchain `leanprover/lean4:v4.34.0-rc2` (Mathlib v4.34.0-rc2, matching OpenAI's NavierStokesAndEuler project)

Install Python dependencies:
```bash
pip install numpy scipy sympy requests
```

---

## 2. Step 1: Clone the Checked OpenAI Formalization Commit

The construction, including how its force is defined, is in the Lean 4 source (commit checked for this project):

```bash
git clone https://github.com/openai/NavierStokesAndEuler.git
cd NavierStokesAndEuler
git checkout 8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538
cd ..
```

---

## 3. Step 2: Automated AST & Syntax Check (Directive 1)

Verify that the OpenAI formalization contains zero unproven gaps in the core proof and no opaque axioms:

```bash
# In the NavierStokesAndEuler directory:
cd NavierStokesAndEuler

# Check for sorry/admit in core theorem path
grep -rn "sorry" NavierStokes/
# Expected: 0 hits in NavierStokes/ (core theorem)
# Hits only appear in ComparatorChallenges/ (intentional open benchmark problems)

# Verify external force type is C^\infty
grep -rn "ContDiff ℝ ∞" NavierStokes/CandidateFromLimits.lean
# Expected: confirms force is smooth with compact support

# How the force is defined
grep -n -A 5 "def tracedResidual" NavierStokes/CandidateFromLimits.lean
grep -n "theorem force_eq_activated_residual" NavierStokes/CandidateFromLimits.lean
# Expected: the force equals the Navier-Stokes residual of the final (u, p) on 0 <= t < 1.
# Reading (paper Sec. 2.3, 6): it is the smooth remainder left after shear-amplified pulses
# cancel the singular part of the residual -- it seeds the pulses, it does not drive the collapse.
# A legitimate existence-proof technique, not a flaw.
cd ..
```

---

## 4. Step 3: Gevrey Regularity vs C^\infty Boundary (Directive 4)

Verify that the cutoff function $\exp(-1/q^2)$ has an exact theoretical asymptotic Gevrey index $s = 1.5$, while remaining in $C^\infty$:

```bash
python3 scripts/directive4_gevrey_regularity.py
```
**Expected Results:**
- Theoretical asymptotic Gevrey index $s = 1.5$ (Gevrey-1.5 class)
- Pre-asymptotic fit on small sample $N \le 15$ yields empirical slope $\approx 2.22$
- Flatness at origin: $\lim_{q \to 0^+} \frac{d^N}{dq^N}\left[q^{-A} e^{-1/q^2}\right] = 0$ for all $N, A$
- Shows no formal cheat occurred: Gevrey-1.5 $\subset C^\infty \setminus C^\omega$, and a compactly supported smooth force requires exactly this gap.

---

## 5. Step 4: Thermodynamic Paradox & Enstrophy Divergence (Directive 2)

Track the asymptotic exponents of all physical quantities as $\tau = 1 - t \to 0$:

```bash
python3 scripts/directive2_thermodynamic_paradox.py
```
**Expected Exponents ($\tau^x$):**
- Global $L^2$ kinetic energy: $\tau^{+0.485} \to 0$ (bounded, satisfies Prize Alternative C)
- Intensive local kinetic energy density: $e_{\text{local}} \sim \tau^{-1.010} \to \infty$ (diverges)
- Enstrophy $\int |\nabla \times u|^2 dV$: $\tau^{-0.515} \to \infty$ (diverges)
- $L^3$ norm $\|u\|_3$: $\tau^{-0.0067} \to \infty$ (diverges)
- Sobolev norm $\|u\|_{H^{3/2}}$: $\tau^{-0.5075} \to \infty$ (diverges)
- Local temperature rise from viscous heating: $\Delta T \sim \tau^{-1.010} \to \infty$ — the model's decoupled-temperature (isothermal) assumption fails; no law of thermodynamics is violated inside the model. In water $\Delta T\simeq u^2/c_p$ is about 48 K at Ma 0.3 and 540 K at Ma 1 (not a plasma).

---

## 6. Step 5: Moment Matrix Scaling & Structural Stability (Directive 3 & 6)

Verify non-dimensionalization of the 5-moment matching system ($A = D B D$):

```bash
python3 scripts/directive3_jacobian_instability.py
python3 scripts/directive6_thermal_instability.py
```
**Expected Results:**
- Factorization: $A = D B D$ with diagonal scaling $D = \text{diag}(1, X_R^2, X_R^4)$
- Non-dimensionalized condition number: $\kappa(B) \approx 4.11 \times 10^5$ (bounded and constant for all $X_R$)
- Raw condition number $\kappa(A) \sim 10^{28}$ at $X_R = 1000$ was an unscaled dimensional artifact
- Under proper scaling, the moment-matching system is well conditioned; the raw figure is not evidence of physical fine-tuning or fragility.

---

## 7. Step 6: Mach Number and Continuum Validity Times (Directive 5)

Track the local Mach number $\text{Ma} = |u|/c_s$ in water at 300 K ($c_s = 1500$ m/s) for a 1 cm vortex:

```bash
python3 scripts/directive5_mach_divergence.py
```
**Expected critical times.** $\tau$ is the construction's **dimensionless** time to blow-up; physical time is $t = T\tau$ with $T = L_0^2/\nu = 100$ s:
- $\text{Ma} = 0.3$ (onset of compressibility effects): $\tau \approx 6.69 \times 10^{-14}$, **$t \approx 6.7$ ps**
- $\text{Ma} = 1.0$ (sonic): $\tau \approx 6.16 \times 10^{-15}$, $t \approx 0.62$ ps
- core radius at molecular size ($\text{Kn} \sim 1$): $\tau \approx 9.0 \times 10^{-16}$, $t \approx 90$ fs

The incompressible model stops describing water a few picoseconds before the mathematical singularity. (Earlier
versions read $\tau$ as seconds and quoted "67 femtoseconds"; that unit error is withdrawn.) On the construction's
diffusive route these limits coincide at one scale, $\ell_* = \nu/c_s \approx 0.7$ nm (paper Prop. 5.1). This is a
statement about which model the theorem is about, not a self-refutation of the equations.

---

## 8. Step 7: Formal Lean 4 statements (current)

The earlier "Thermodynamic Censorship" file (a global bounded-enstrophy *axiom* with an underived constant) is
withdrawn and kept only as an unverified draft in `03_Lean4_Topological_Censorship/src/drafts/`. The verified
statements compile inside OpenAI's own project:

```bash
cd NavierStokesAndEuler
lake build NavierStokes.PeriodicUniqueness
lake env lean ../OpenAI-NSE-Verification/03_Lean4_Topological_Censorship/src/OpenAIAdmissibility.lean
```
Key results (no `sorry`, standard axioms only, no remaining hypothesis):
- `exits_admissible_near_one'`: any object with OpenAI's `CandidateProperties` exceeds every velocity-gradient bound arbitrarily close to $t = 1$;
- `candidate_not_admissible'`, `candidate_not_admissibleScaled'`: so it leaves $|\nabla u| \lesssim c_s^2/\nu$ for every fluid and every choice of units.

That is a bridge to the proof objects ("velocity blow-up forces gradient blow-up"), not new physics. All nine verified
files (74 declarations) are listed in `03_Lean4_Topological_Censorship/README.md`.

---

## 9. Automated runs

```bash
scripts/run_benchmarks.sh --full        # maintained: tests, solvers, Lean files, every number checked (BENCHMARKS.md)
bash 01_Verification_Paper/verify-physical-vacuity.sh /path/to/NavierStokesAndEuler   # older directive runner (legacy filename)
```
