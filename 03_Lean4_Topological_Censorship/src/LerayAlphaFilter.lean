import Mathlib.Tactic
import Mathlib.Order.Monotone.Basic

/-!
# LerayAlphaFilter — elementary bounds on the Leray-α filter symbol

For `α > 0` the Leray-α transport velocity is `ū = (1 − α²Δ)⁻¹ u`, whose Fourier symbol is
    φ α k = 1 / (1 + α² k²).

WHAT IS PROVED (all elementary real inequalities):
  (a) `φ_pos`          0 < φ α k
  (b) `φ_le_one`       φ α k ≤ 1
  (c) `φ_eq_one_iff`   φ α k = 1 ↔ k = 0
  (d) `φ_le_high_freq` φ α k ≤ 1 / (α² k²) for k ≠ 0      (high-frequency decay)
  (e) `φ_even`, `φ_antitoneOn_nonneg`   evenness in k; antitone on k ≥ 0
  (f) `φ_sq_le`        (φ α k)² ≤ φ α k                   (squared-resolvent variant)

These are the only facts a formalization of "the lock is a gate" needs about the filter;
they say nothing about well-posedness of Leray-α, and nothing about Navier–Stokes.
No `sorry`, no `axiom`; see `#print axioms` at the end.
-/
namespace LerayAlphaFilter

/-- The Leray-α filter symbol φ(k) = 1 / (1 + α² k²). -/
noncomputable def φ (α k : ℝ) : ℝ := 1 / (1 + α ^ 2 * k ^ 2)

variable {α : ℝ}

/-- The denominator is at least one. -/
theorem one_le_denom (α k : ℝ) : 1 ≤ 1 + α ^ 2 * k ^ 2 := by
  have := mul_nonneg (sq_nonneg α) (sq_nonneg k)
  linarith

/-- (a) The symbol is strictly positive. -/
theorem φ_pos (hα : 0 < α) (k : ℝ) : 0 < φ α k := by
  unfold φ; positivity

/-- (b) The symbol is at most one. -/
theorem φ_le_one (hα : 0 < α) (k : ℝ) : φ α k ≤ 1 := by
  unfold φ
  rw [div_le_one (by positivity)]
  exact one_le_denom α k

/-- (c) The symbol equals one exactly at k = 0. -/
theorem φ_eq_one_iff (hα : 0 < α) (k : ℝ) : φ α k = 1 ↔ k = 0 := by
  unfold φ
  constructor
  · intro h
    have hpos : 0 < 1 + α ^ 2 * k ^ 2 := by positivity
    rw [div_eq_iff hpos.ne'] at h
    have h0 : α ^ 2 * k ^ 2 = 0 := by linarith
    rcases mul_eq_zero.mp h0 with h1 | h1
    · exact absurd h1 (by positivity)
    · exact (pow_eq_zero_iff two_ne_zero).mp h1
  · intro hk
    rw [hk]; norm_num

/-- (d) High-frequency decay: for k ≠ 0, φ α k ≤ 1 / (α² k²). -/
theorem φ_le_high_freq (hα : 0 < α) {k : ℝ} (hk : k ≠ 0) :
    φ α k ≤ 1 / (α ^ 2 * k ^ 2) := by
  unfold φ
  have hx : 0 < α ^ 2 * k ^ 2 := by positivity
  exact one_div_le_one_div_of_le hx (by linarith)

/-- (e) The symbol is even in k. -/
theorem φ_even (α k : ℝ) : φ α (-k) = φ α k := by
  unfold φ; rw [neg_sq]

/-- (e) The symbol is antitone on k ≥ 0 (hence antitone in |k| by evenness). -/
theorem φ_antitoneOn_nonneg (hα : 0 < α) : AntitoneOn (φ α) (Set.Ici 0) := by
  intro a ha b hb hab
  have ha0 : 0 ≤ a := Set.mem_Ici.mp ha
  have hab2 : a ^ 2 ≤ b ^ 2 := by nlinarith
  have h : α ^ 2 * a ^ 2 ≤ α ^ 2 * b ^ 2 :=
    mul_le_mul_of_nonneg_left hab2 (sq_nonneg α)
  unfold φ
  exact one_div_le_one_div_of_le (by positivity) (by linarith)

/-- (f) The squared-resolvent symbol is dominated by the first-order one: φ² ≤ φ. -/
theorem φ_sq_le (hα : 0 < α) (k : ℝ) : (φ α k) ^ 2 ≤ φ α k := by
  have h0 := φ_pos hα k
  have h1 := φ_le_one hα k
  nlinarith

end LerayAlphaFilter

#print axioms LerayAlphaFilter.φ_pos
#print axioms LerayAlphaFilter.φ_le_one
#print axioms LerayAlphaFilter.φ_eq_one_iff
#print axioms LerayAlphaFilter.φ_le_high_freq
#print axioms LerayAlphaFilter.φ_even
#print axioms LerayAlphaFilter.φ_antitoneOn_nonneg
#print axioms LerayAlphaFilter.φ_sq_le
