import Mathlib.Tactic
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Log.NegMulLog

/-!
# LatticeBGKEntropy — an H-theorem for the discrete-velocity BGK collision step

Populations `f : Fin n → ℝ` on a finite velocity set relax toward an equilibrium
`feq` by the BGK collision `f ↦ (1 − ω) f + ω feq`, `0 < ω ≤ 1`. With
`H f = ∑ f log f` and relative entropy `D(f‖feq) = ∑ f log (f / feq)`:

WHAT IS PROVED (finite-dimensional, elementary):
  (a) `bgk_pos`                      positivity is preserved
  (b) `bgk_mass`                     mass is conserved
  (c) `H_convex_step`                H (bgk f) ≤ (1−ω) H f + ω H feq
  (d) `relative_entropy_nonneg`      D(f‖feq) ≥ 0 at equal mass   (Gibbs)
  (e) `bgk_relative_entropy_decreases`  D(bgk f ‖ feq) ≤ (1−ω) D(f‖feq)
      — the H-theorem for the discrete step: relative entropy contracts geometrically
      toward equilibrium, with `bgk_fixed_point` / `relEnt_self` the fixed point.

WHAT THIS IS: a theorem about a finite-dimensional discrete model — the lattice
Boltzmann BGK collision that LBM/DSMC-type codes actually integrate. It is NOT a
theorem about the Boltzmann equation, and NOT about Navier–Stokes. Its role in the
programme (DUAL_SCALE_LOCK_PROGRAMME.md, Lock K) is to make precise, for the
discrete model, the statement "the governing equation below ℓ* has an H-theorem".
No `sorry`, no `axiom`; see `#print axioms` at the end.
-/
namespace LatticeBGKEntropy

open Finset

variable {n : ℕ}

/-- The BGK collision step `f ↦ (1 − ω) f + ω feq`. -/
def bgk (ω : ℝ) (f feq : Fin n → ℝ) : Fin n → ℝ := fun i => (1 - ω) * f i + ω * feq i

/-- Boltzmann's H-functional on the finite velocity set. -/
noncomputable def H (f : Fin n → ℝ) : ℝ := ∑ i, f i * Real.log (f i)

/-- Relative entropy (Kullback–Leibler) of `f` with respect to `feq`. -/
noncomputable def relEnt (f feq : Fin n → ℝ) : ℝ := ∑ i, f i * Real.log (f i / feq i)

/-! ### Pointwise inequalities -/

/-- Convexity of `x ↦ x log x` along the BGK segment. -/
theorem mul_log_step (ω a b : ℝ) (hω0 : 0 ≤ ω) (hω1 : ω ≤ 1) (ha : 0 ≤ a) (hb : 0 ≤ b) :
    ((1 - ω) * a + ω * b) * Real.log ((1 - ω) * a + ω * b)
      ≤ (1 - ω) * (a * Real.log a) + ω * (b * Real.log b) := by
  have h := Real.convexOn_mul_log.2 (Set.mem_Ici.mpr ha) (Set.mem_Ici.mpr hb)
    (by linarith : (0 : ℝ) ≤ 1 - ω) hω0 (by ring : (1 - ω) + ω = 1)
  simpa [smul_eq_mul] using h

/-- Gibbs' termwise inequality: `a − c ≤ a log (a / c)`. -/
theorem sub_le_mul_log_div (a c : ℝ) (ha : 0 < a) (hc : 0 < c) :
    a - c ≤ a * Real.log (a / c) := by
  have h := Real.log_le_sub_one_of_pos (div_pos hc ha)
  have hl : Real.log (a / c) = -Real.log (c / a) := by
    rw [← Real.log_inv, inv_div]
  have hm := mul_le_mul_of_nonneg_left h ha.le
  have hc' : a * (c / a - 1) = c - a := by field_simp
  rw [hl]
  linarith

/-- Convexity of `x ↦ x log (x / c)` along the BGK segment, with `c log (c / c) = 0`:
the termwise form of the H-theorem. -/
theorem mul_log_div_step (ω a c : ℝ) (hω : 0 < ω) (hω1 : ω ≤ 1) (ha : 0 < a) (hc : 0 < c) :
    ((1 - ω) * a + ω * c) * Real.log (((1 - ω) * a + ω * c) / c)
      ≤ (1 - ω) * (a * Real.log (a / c)) := by
  have hpos : 0 < (1 - ω) * a + ω * c := by
    have h1 : 0 ≤ (1 - ω) * a := mul_nonneg (by linarith) ha.le
    have h2 : 0 < ω * c := mul_pos hω hc
    linarith
  rw [Real.log_div hpos.ne' hc.ne', Real.log_div ha.ne' hc.ne']
  have h := mul_log_step ω a c hω.le hω1 ha.le hc.le
  nlinarith [h]

/-! ### The collision step -/

variable (ω : ℝ) (f feq : Fin n → ℝ)

/-- (a) Positivity is preserved. -/
theorem bgk_pos (hω : 0 < ω) (hω1 : ω ≤ 1) (hf : ∀ i, 0 < f i) (hfeq : ∀ i, 0 < feq i)
    (i : Fin n) : 0 < bgk ω f feq i := by
  simp only [bgk]
  have h1 : 0 ≤ (1 - ω) * f i := mul_nonneg (by linarith) (hf i).le
  have h2 : 0 < ω * feq i := mul_pos hω (hfeq i)
  linarith

/-- (b) Mass is conserved when `f` and `feq` carry equal mass. -/
theorem bgk_mass (hmass : ∑ i, f i = ∑ i, feq i) : ∑ i, bgk ω f feq i = ∑ i, f i := by
  simp only [bgk]
  rw [Finset.sum_add_distrib, ← Finset.mul_sum, ← Finset.mul_sum, hmass]
  ring

/-- The equilibrium is a fixed point. -/
theorem bgk_fixed_point : bgk ω feq feq = feq := by
  funext i; simp only [bgk]; ring

/-- Relative entropy of the equilibrium with respect to itself vanishes. -/
theorem relEnt_self (hfeq : ∀ i, 0 < feq i) : relEnt feq feq = 0 := by
  unfold relEnt
  apply Finset.sum_eq_zero
  intro i _
  rw [div_self (hfeq i).ne', Real.log_one, mul_zero]

/-- (c) `H` is convex along the step. -/
theorem H_convex_step (hω : 0 < ω) (hω1 : ω ≤ 1) (hf : ∀ i, 0 < f i) (hfeq : ∀ i, 0 < feq i) :
    H (bgk ω f feq) ≤ (1 - ω) * H f + ω * H feq := by
  unfold H
  rw [Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib]
  apply Finset.sum_le_sum
  intro i _
  simp only [bgk]
  exact mul_log_step ω (f i) (feq i) hω.le hω1 (hf i).le (hfeq i).le

/-- (d) Gibbs' inequality: relative entropy is non-negative at equal mass. -/
theorem relative_entropy_nonneg (hf : ∀ i, 0 < f i) (hfeq : ∀ i, 0 < feq i)
    (hmass : ∑ i, f i = ∑ i, feq i) : 0 ≤ relEnt f feq := by
  unfold relEnt
  have h : ∑ i, (f i - feq i) ≤ ∑ i, f i * Real.log (f i / feq i) :=
    Finset.sum_le_sum fun i _ => sub_le_mul_log_div (f i) (feq i) (hf i) (hfeq i)
  rw [Finset.sum_sub_distrib, hmass, sub_self] at h
  exact h

/-- (e) The H-theorem for the discrete BGK step: relative entropy to equilibrium
contracts by the factor `(1 − ω)` at every collision. -/
theorem bgk_relative_entropy_decreases (hω : 0 < ω) (hω1 : ω ≤ 1)
    (hf : ∀ i, 0 < f i) (hfeq : ∀ i, 0 < feq i) :
    relEnt (bgk ω f feq) feq ≤ (1 - ω) * relEnt f feq := by
  unfold relEnt
  rw [Finset.mul_sum]
  apply Finset.sum_le_sum
  intro i _
  simp only [bgk]
  exact mul_log_div_step ω (f i) (feq i) hω hω1 (hf i) (hfeq i)

#print axioms bgk_pos
#print axioms bgk_mass
#print axioms bgk_fixed_point
#print axioms relEnt_self
#print axioms H_convex_step
#print axioms relative_entropy_nonneg
#print axioms bgk_relative_entropy_decreases

end LatticeBGKEntropy
