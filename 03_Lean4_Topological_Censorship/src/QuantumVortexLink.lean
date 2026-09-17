import Mathlib.Tactic
import Mathlib.Analysis.SpecialFunctions.Sqrt
import Mathlib.Analysis.SpecialFunctions.Pow.Real

/-!
# The micro–macro link through quantum fluids: exact statements

A classical Navier–Stokes core of size `ℓ` and speed `u` has Reynolds number `Re = uℓ/ν` and meets its
validity length `ℓ* = ν/c`. In a superfluid the kinematic viscosity is replaced by the quantum of
circulation per `2π`, `ħ/m`, and the microscopic length is the healing length `ξ = ħ/(√2 m c)`.

## What is proved

1. `quantum_reynolds_eq_one` — around a singly quantized vortex, `u(r) = ħ/(m r)`, so
   `u r / (ħ/m) = 1` at **every** radius: the quantized vortex *is* a core with Reynolds number one, the
   condition that defines the diffusive route of the OpenAI construction (`BlowupRegimeMap.lean`).
2. `sonic_radius` — `u(r) = c` exactly at `r = ħ/(m c)`, and `sonic_radius_eq_sqrt_two_xi`: that radius is
   `√2 ξ`. So `ħ/(m c)` plays for the superfluid the role `ℓ* = ν/c` plays for the classical fluid
   (`lstar_analogue`).
3. `landau_no_excitation` — Landau's criterion: if `ε(p) ≥ v_c p` for all `p > 0`, a body moving at
   `v < v_c` cannot create any excitation (`ε(p) − p v > 0`).
4. `bogoliubov_ratio_ge` and `bogoliubov_vc_is_c` — for the Bogoliubov spectrum
   `ε(k) = √(c²k² + (k²/2)²)` (units `ħ = m = 1`) one has `ε(k)/k ≥ c`, and `c` is the infimum: the
   critical velocity equals the sound speed.
5. `free_gas_vc_zero` — for a free gas `ε = k²/2` the ratio `ε/k` is below any positive speed for small `k`:
   no superfluidity without interactions (Godfrin & Krotscheck 2022).
6. `atomistic_mach_bound` — the one-particle form of `BlowupRegimeMap.atomistic_speed_bound`: a particle of
   mass `m` with kinetic energy at most `E` has `v² ≤ 2E/m`.
7. `lstar_floor_identity` — combining two published estimates, the minimal kinematic viscosity
   `ν_m = ħ / (4π √(m_e A m_p))` (Trachenko & Brazhkin 2020) and the maximal speed of sound
   `v_u = α c √(m_e / (2 m_p)) / √A` (Trachenko et al. 2020), the atomic mass number `A` cancels exactly:
   `ν_m / v_u = (√2 / 4π) · ħ / (m_e c α) = (√2 / 4π) a_B`, a fixed fraction of the Bohr radius. Hence any
   fluid obeying both estimates has `ℓ* = ν/c ≥ (√2/4π) a_B ≈ 6 pm` (`lstar_floor`). The identity is exact;
   the two inputs are order-of-magnitude bounds from the literature, not theorems.

Nothing here is a statement about solutions of the Gross–Pitaevskii or Navier–Stokes equations; these are
the exact identities that make the quantum–classical correspondence precise.
-/

namespace QuantumVortexLink

variable {hbar m c r : ℝ}

/-- velocity of a singly quantized vortex -/
noncomputable def uq (hbar m r : ℝ) : ℝ := hbar / (m * r)

/-- healing length `ξ = ħ / (√2 m c)` -/
noncomputable def xi (hbar m c : ℝ) : ℝ := hbar / (Real.sqrt 2 * m * c)

theorem quantum_reynolds_eq_one (hh : 0 < hbar) (hm : 0 < m) (hr : 0 < r) :
    uq hbar m r * r / (hbar / m) = 1 := by
  unfold uq
  field_simp

theorem sonic_radius (hh : 0 < hbar) (hm : 0 < m) (hc : 0 < c) (hr : 0 < r) :
    uq hbar m r = c ↔ r = hbar / (m * c) := by
  unfold uq
  constructor
  · intro h
    field_simp at h ⊢
    linarith
  · intro h
    subst h
    field_simp

theorem sonic_radius_eq_sqrt_two_xi (hh : 0 < hbar) (hm : 0 < m) (hc : 0 < c) :
    hbar / (m * c) = Real.sqrt 2 * xi hbar m c := by
  unfold xi
  have h2 : Real.sqrt 2 ≠ 0 := by positivity
  field_simp

/-- The superfluid analogue of `ℓ* = ν/c`: replace `ν` by `ħ/m`. -/
theorem lstar_analogue (hh : 0 < hbar) (hm : 0 < m) (hc : 0 < c) :
    (hbar / m) / c = hbar / (m * c) := by
  field_simp

/-- Landau's criterion. -/
theorem landau_no_excitation (eps : ℝ → ℝ) {vc v : ℝ} (hbound : ∀ p, 0 < p → vc * p ≤ eps p)
    (hv : v < vc) : ∀ p, 0 < p → 0 < eps p - p * v := by
  intro p hp
  have := hbound p hp
  nlinarith

/-- Bogoliubov spectrum (ħ = m = 1). -/
noncomputable def bog (c k : ℝ) : ℝ := Real.sqrt (c ^ 2 * k ^ 2 + (k ^ 2 / 2) ^ 2)

theorem bogoliubov_ratio_ge (_hc : 0 < c) {k : ℝ} (hk : 0 < k) : c ≤ bog c k / k := by
  unfold bog
  rw [le_div_iff₀ hk]
  apply Real.le_sqrt_of_sq_le
  nlinarith [sq_nonneg (k ^ 2 / 2)]

theorem bogoliubov_vc_is_c (hc : 0 < c) {δ : ℝ} (hδ : 0 < δ) :
    ∃ k : ℝ, 0 < k ∧ bog c k / k < c + δ := by
  -- bog c k / k = sqrt(c² + k²/4) ≤ c + k/2
  refine ⟨δ, hδ, ?_⟩
  have hk : 0 < δ := hδ
  rw [div_lt_iff₀ hk]
  unfold bog
  rw [Real.sqrt_lt' (by positivity)]
  nlinarith [sq_nonneg δ, mul_pos hc hk, mul_pos hk hk, mul_pos (mul_pos hk hk) hk, mul_pos (mul_pos hk hk) (mul_pos hk hk)]

theorem free_gas_vc_zero {v : ℝ} (hv : 0 < v) : ∃ k : ℝ, 0 < k ∧ (k ^ 2 / 2) / k < v := by
  refine ⟨v, hv, ?_⟩
  rw [div_lt_iff₀ hv]
  nlinarith

/-- Speed bound from bounded kinetic energy, in the form used for Mach numbers. -/
theorem atomistic_mach_bound {E v : ℝ} (hm : 0 < m) (hE : (1 / 2) * m * v ^ 2 ≤ E) :
    v ^ 2 ≤ 2 * E / m := by
  rw [le_div_iff₀ hm]
  nlinarith

/-- `ν_m / v_u` does not depend on the atomic mass number `A`. -/
theorem lstar_floor_identity {hbar me mp cl alpha A : ℝ} (hh : 0 < hbar) (he : 0 < me) (hp : 0 < mp)
    (hcl : 0 < cl) (ha : 0 < alpha) (hA : 0 < A) :
    (hbar / (4 * Real.pi * Real.sqrt (me * (A * mp)))) /
        (alpha * cl * Real.sqrt (me / (2 * mp)) / Real.sqrt A)
      = (Real.sqrt 2 / (4 * Real.pi)) * (hbar / (me * cl * alpha)) := by
  have hsA : 0 < Real.sqrt A := Real.sqrt_pos.mpr hA
  have hs1 : Real.sqrt (me * (A * mp)) = Real.sqrt me * Real.sqrt A * Real.sqrt mp := by
    rw [Real.sqrt_mul he.le, Real.sqrt_mul hA.le]; ring
  have hs2 : Real.sqrt (me / (2 * mp)) = Real.sqrt me / (Real.sqrt 2 * Real.sqrt mp) := by
    rw [Real.sqrt_div he.le, Real.sqrt_mul (by norm_num : (0:ℝ) ≤ 2)]
  have hme : 0 < Real.sqrt me := Real.sqrt_pos.mpr he
  have hmp : 0 < Real.sqrt mp := Real.sqrt_pos.mpr hp
  have h2 : 0 < Real.sqrt 2 := by positivity
  have hsq : Real.sqrt me * Real.sqrt me = me := Real.mul_self_sqrt he.le
  rw [hs1, hs2]
  field_simp
  have hsq2 : Real.sqrt me ^ 2 = me := Real.sq_sqrt he.le
  nlinarith [hsq2, hsq, hme, hmp, h2, hsA]

/-- Consequence: if `ν ≥ ν_m` and `0 < c ≤ v_u`, then `ℓ* = ν/c ≥ ν_m/v_u`. -/
theorem lstar_floor {nu cs num vu : ℝ} (hnum : 0 < num) (_hvu : 0 < vu) (hcs : 0 < cs)
    (hnu : num ≤ nu) (hc : cs ≤ vu) : num / vu ≤ nu / cs := by
  calc num / vu ≤ num / cs := div_le_div_of_nonneg_left hnum.le hcs hc
    _ ≤ nu / cs := div_le_div_of_nonneg_right hnu hcs.le

end QuantumVortexLink

#print axioms QuantumVortexLink.quantum_reynolds_eq_one
#print axioms QuantumVortexLink.sonic_radius
#print axioms QuantumVortexLink.sonic_radius_eq_sqrt_two_xi
#print axioms QuantumVortexLink.lstar_analogue
#print axioms QuantumVortexLink.landau_no_excitation
#print axioms QuantumVortexLink.bogoliubov_ratio_ge
#print axioms QuantumVortexLink.bogoliubov_vc_is_c
#print axioms QuantumVortexLink.free_gas_vc_zero
#print axioms QuantumVortexLink.atomistic_mach_bound
#print axioms QuantumVortexLink.lstar_floor_identity
#print axioms QuantumVortexLink.lstar_floor
