# Reproduction Protocol: Physical Verification of OpenAI's Navier-Stokes Formalization

This protocol provides step-by-step instructions for peer reviewers, fluid dynamicists, and formal verification researchers to independently reproduce all findings of the physical verification.

---

## 1. Prerequisites

- Linux or macOS system (x86_64 or aarch64)
- Python $\ge$ 3.10 with `numpy`, `scipy`, `sympy`, `requests`
- `git`
- (Optional for Lean 4 formalization) `elan` and `lake` with Lean 4 toolchain `leanprover/lean4:v4.11.0`

Install Python dependencies:
```bash
pip install numpy scipy sympy requests
```

---

## 2. Step 1: Clone the Checked OpenAI Formalization Commit

The mathematical construction and the Method of Manufactured Solutions (MMS) are embedded directly in the Lean 4 source:

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

# Verify the Method of Manufactured Solutions (forcing defined as residual)
grep -n -A 5 "def tracedResidual" NavierStokes/CandidateFromLimits.lean
# Expected: shows force is defined as the extended trace of 'pastResidual'
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
- Proves no formal cheat occurred: Gevrey-1.5 $\subset C^\infty \setminus C^\omega$.

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
- Local temperature rise: $\Delta T \sim \tau^{-1.010} \to \infty$ (violates Boussinesq isothermal state)

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
- Under proper scaling, the moment-matching system remains structurally stable under physical 300K thermal fluctuations.

---

## 7. Step 6: Mach Number Divergence & Self-Invalidation (Directive 5)

Track the local Mach number $\text{Ma} = |u|/c_s$ in physical units (water at 300K, $c_s = 1500$ m/s):

```bash
python3 scripts/directive5_mach_divergence.py
```
**Expected Critical Times:**
- $\text{Ma} = 0.3$ (incompressible breakdown): $\tau \approx 6.69 \times 10^{-14}$ s
- $\text{Ma} = 1.0$ (sonic barrier): $\tau \approx 6.16 \times 10^{-15}$ s
- Core reaches molecular scale ($Kn \sim 1$): $\tau \approx 9.0 \times 10^{-16}$ s
- Proves Navier-Stokes equations invalidate themselves 67 femtoseconds before mathematical blowup.

---

## 8. Step 7: Lean 4 Thermodynamic Censorship Formalization (Directive 7)

Inspect the formal Lean 4 implementation of the bounded enstrophy axiom:

```bash
cat 03_Lean4_Topological_Censorship/src/ThermodynamicCensorship.lean
```
Key definitions:
- `UniformBoundedEnstrophy`: requires $\sup_t \int |\nabla \times u|^2 dV \le \Omega_{\max}$
- `PhysicalFluidProperties`: extends `CandidateProperties` with thermodynamic admissibility
- `thermodynamic_censorship_challenge`: formalizes the conjecture that physical fluids cannot blow up.

---

## 9. Certified Verification Script

To run the complete suite automatically:
```bash
./01_Challenger_Paper/verify-physical-vacuity.sh
```
