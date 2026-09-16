import Mathlib.Tactic
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Log.NegMulLog

/-!
# NonlinearBGKEntropy — H-theorem for the nonlinear discrete-velocity BGK step

The Rust kinetic solver integrates a discrete-velocity BGK model: populations
`f : Fin n → ℝ` on velocities `v : Fin n → (Fin d → ℝ)` with quadrature weights
`w i > 0`. Its collision step relaxes `f` toward the *entropic* equilibrium
`feq i = w i * exp (a + b · v i)` whose mass and momentum equal those of `f`
(so `feq` depends nonlinearly on `f`), and its force step is the exact-difference
update `f ↦ f + feq(u + gΔt) − feq(u)`.

With the weighted entropy `Hw f = ∑ f i * log (f i / w i)`:

WHAT IS PROVED (finite-dimensional, elementary):
  (a) `entropic_eq_minimizes`     Hw feq ≤ Hw f  whenever feq is entropic and
                                  f > 0 has the same mass and momentum    (Gibbs)
  (b) `bgk_step_conserves_mass`,
      `bgk_step_conserves_momentum`   f' = (1−ω) f + ω feq keeps both moments
  (c) `bgk_step_pos`, `bgk_step_entropy_decreases`
                                  f' > 0 and Hw f' ≤ Hw f  — the nonlinear H-theorem
  (d) `force_exact_difference_mass`, `force_exact_difference_momentum`
                                  the force step leaves mass unchanged and adds
                                  exactly ρ·g·Δt of momentum

WHAT IS ASSUMED / NOT PROVED: the EXISTENCE of the entropic equilibrium (the pair
`a, b` matching the moments of `f`) is taken as a hypothesis — the solver finds it
by Newton iteration. Positivity of the post-force populations is not claimed.
This is a theorem about the finite-dimensional discrete-velocity collision and force
steps the solver implements; it says nothing about the Boltzmann equation or its
regularity, and nothing about Navier–Stokes.
No `sorry`, no `axiom`; see `#print axioms` at the end.
-/
namespace NonlinearBGKEntropy

open Finset

variable {n d : ℕ}

/-- Weighted Boltzmann entropy on the discrete velocity set. -/
noncomputable def Hw (w f : Fin n → ℝ) : ℝ := ∑ i, f i * Real.log (f i / w i)

/-- Mass `∑ f`. -/
def mass (f : Fin n → ℝ) : ℝ := ∑ i, f i

/-- Momentum component `j`: `∑ f i * v i j`. -/
def mom (v : Fin n → Fin d → ℝ) (f : Fin n → ℝ) (j : Fin d) : ℝ := ∑ i, f i * v i j

/-- Euclidean pairing `b · x`. -/
def dot (b x : Fin d → ℝ) : ℝ := ∑ j, b j * x j

/-- The BGK collision step. -/
def bgk (ω : ℝ) (f feq : Fin n → ℝ) : Fin n → ℝ := fun i => (1 - ω) * f i + ω * feq i

/-! ### Pointwise inequalities -/

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

/-- Convexity of `x ↦ x log (x / w)` along a segment. -/
theorem mul_log_div_convex (ω a b c : ℝ) (hω0 : 0 ≤ ω) (hω1 : ω ≤ 1)
    (ha : 0 < a) (hb : 0 < b) (hc : 0 < c) :
    ((1 - ω) * a + ω * b) * Real.log (((1 - ω) * a + ω * b) / c)
      ≤ (1 - ω) * (a * Real.log (a / c)) + ω * (b * Real.log (b / c)) := by
  have hpos : 0 < (1 - ω) * a + ω * b := by
    rcases eq_or_lt_of_le hω0 with h0 | h0
    · subst h0; simpa using ha
    · have h1 : 0 ≤ (1 - ω) * a := mul_nonneg (by linarith) ha.le
      have h2 : 0 < ω * b := mul_pos h0 hb
      linarith
  have hconv := Real.convexOn_mul_log.2 (Set.mem_Ici.mpr ha.le) (Set.mem_Ici.mpr hb.le)
    (by linarith : (0 : ℝ) ≤ 1 - ω) hω0 (by ring : (1 - ω) + ω = 1)
  simp only [smul_eq_mul] at hconv
  rw [Real.log_div hpos.ne' hc.ne', Real.log_div ha.ne' hc.ne', Real.log_div hb.ne' hc.ne']
  nlinarith [hconv]

/-! ### (a) The entropic equilibrium minimizes the entropy at fixed moments -/

/-- The moment-weighted sum of `f − feq` against `a + b · v` vanishes when the
masses and momenta agree. -/
theorem moment_pairing_zero (v : Fin n → Fin d → ℝ) (f feq : Fin n → ℝ) (a : ℝ)
    (b : Fin d → ℝ) (hmass : mass f = mass feq) (hmom : ∀ j, mom v f j = mom v feq j) :
    ∑ i, (f i - feq i) * (a + dot b (v i)) = 0 := by
  have e1 : ∑ i, (f i - feq i) * (a + dot b (v i))
      = a * (mass f - mass feq) + ∑ j, b j * (mom v f j - mom v feq j) := by
    simp only [mass, mom, dot, mul_add, Finset.mul_sum, sub_mul, Finset.sum_add_distrib,
      Finset.sum_sub_distrib]
    rw [Finset.sum_comm (f := fun i j => f i * (b j * v i j)),
      Finset.sum_comm (f := fun i j => feq i * (b j * v i j))]
    have h2 : ∀ j : Fin d, ∑ i, f i * (b j * v i j) = b j * ∑ i, f i * v i j := by
      intro j; rw [Finset.mul_sum]; exact Finset.sum_congr rfl (fun i _ => by ring)
    have h3 : ∀ j : Fin d, ∑ i, feq i * (b j * v i j) = b j * ∑ i, feq i * v i j := by
      intro j; rw [Finset.mul_sum]; exact Finset.sum_congr rfl (fun i _ => by ring)
    simp only [h2, h3]
    rw [← Finset.sum_mul, ← Finset.sum_mul]
    simp only [mul_sub, Finset.sum_sub_distrib]
    ring
  rw [e1, hmass, sub_self, mul_zero, zero_add]
  exact Finset.sum_eq_zero (fun j _ => by rw [hmom j, sub_self, mul_zero])

/-- (a) Gibbs: the entropic equilibrium has the least weighted entropy among
positive populations with the same mass and momentum. Existence of `a, b` is a
hypothesis (encoded as `hfeq`). -/
theorem entropic_eq_minimizes (w : Fin n → ℝ) (v : Fin n → Fin d → ℝ) (f feq : Fin n → ℝ)
    (a : ℝ) (b : Fin d → ℝ) (hw : ∀ i, 0 < w i) (hf : ∀ i, 0 < f i)
    (hfeq : ∀ i, feq i = w i * Real.exp (a + dot b (v i)))
    (hmass : mass f = mass feq) (hmom : ∀ j, mom v f j = mom v feq j) :
    Hw w feq ≤ Hw w f := by
  have hfeqpos : ∀ i, 0 < feq i := fun i => by rw [hfeq i]; exact mul_pos (hw i) (Real.exp_pos _)
  have hlogeq : ∀ i, Real.log (feq i / w i) = a + dot b (v i) := by
    intro i
    have e : w i * Real.exp (a + dot b (v i)) / w i = Real.exp (a + dot b (v i)) :=
      mul_div_cancel_left₀ _ (hw i).ne'
    rw [hfeq i, e, Real.log_exp]
  -- f log(f/w) = f log(f/feq) + f (a + b·v)
  have hsplit : ∀ i, f i * Real.log (f i / w i)
      = f i * Real.log (f i / feq i) + f i * (a + dot b (v i)) := by
    intro i
    rw [← hlogeq i, ← mul_add, ← Real.log_mul (div_pos (hf i) (hfeqpos i)).ne'
      (div_pos (hfeqpos i) (hw i)).ne']
    congr 2
    field_simp [(hfeqpos i).ne', (hw i).ne']
  have hHf : Hw w f = ∑ i, f i * Real.log (f i / feq i) + ∑ i, f i * (a + dot b (v i)) := by
    rw [Hw, ← Finset.sum_add_distrib]; exact Finset.sum_congr rfl (fun i _ => hsplit i)
  have hHfeq : Hw w feq = ∑ i, feq i * (a + dot b (v i)) := by
    rw [Hw]; exact Finset.sum_congr rfl (fun i _ => by rw [hlogeq i])
  have hgibbs : ∑ i, (f i - feq i) ≤ ∑ i, f i * Real.log (f i / feq i) :=
    Finset.sum_le_sum (fun i _ => sub_le_mul_log_div _ _ (hf i) (hfeqpos i))
  have hzero : ∑ i, (f i - feq i) = 0 := by
    rw [Finset.sum_sub_distrib]; simpa [mass] using sub_eq_zero.mpr hmass
  have hpair := moment_pairing_zero v f feq a b hmass hmom
  have hpair' : ∑ i, f i * (a + dot b (v i)) = ∑ i, feq i * (a + dot b (v i)) := by
    have : ∑ i, (f i - feq i) * (a + dot b (v i))
        = ∑ i, f i * (a + dot b (v i)) - ∑ i, feq i * (a + dot b (v i)) := by
      rw [← Finset.sum_sub_distrib]; exact Finset.sum_congr rfl (fun i _ => by ring)
    linarith
  rw [hHf, hHfeq, hpair']
  linarith

/-! ### (b), (c) The collision step -/

theorem bgk_step_conserves_mass (ω : ℝ) (f feq : Fin n → ℝ) (hmass : mass f = mass feq) :
    mass (bgk ω f feq) = mass f := by
  simp only [mass, bgk, Finset.sum_add_distrib, ← Finset.mul_sum]
  simp only [mass] at hmass
  rw [← hmass]; ring

theorem bgk_step_conserves_momentum (ω : ℝ) (v : Fin n → Fin d → ℝ) (f feq : Fin n → ℝ)
    (hmom : ∀ j, mom v f j = mom v feq j) (j : Fin d) :
    mom v (bgk ω f feq) j = mom v f j := by
  have h := hmom j
  simp only [mom, bgk] at h ⊢
  have e : ∑ i, ((1 - ω) * f i + ω * feq i) * v i j
      = (1 - ω) * ∑ i, f i * v i j + ω * ∑ i, feq i * v i j := by
    rw [Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl (fun i _ => by ring)
  rw [e, ← h]; ring

theorem bgk_step_pos (ω : ℝ) (f feq : Fin n → ℝ) (hω0 : 0 ≤ ω) (hω1 : ω ≤ 1)
    (hf : ∀ i, 0 < f i) (hfeq : ∀ i, 0 < feq i) (i : Fin n) : 0 < bgk ω f feq i := by
  simp only [bgk]
  rcases eq_or_lt_of_le hω0 with h0 | h0
  · subst h0; simpa using hf i
  · have h1 : 0 ≤ (1 - ω) * f i := mul_nonneg (by linarith) (hf i).le
    have h2 : 0 < ω * feq i := mul_pos h0 (hfeq i)
    linarith

/-- (c) The nonlinear H-theorem for the discrete BGK collision: relaxing toward the
entropic equilibrium with matching moments never increases the weighted entropy. -/
theorem bgk_step_entropy_decreases (ω : ℝ) (hω0 : 0 ≤ ω) (hω1 : ω ≤ 1)
    (w : Fin n → ℝ) (v : Fin n → Fin d → ℝ) (f feq : Fin n → ℝ)
    (a : ℝ) (b : Fin d → ℝ) (hw : ∀ i, 0 < w i) (hf : ∀ i, 0 < f i)
    (hfeq : ∀ i, feq i = w i * Real.exp (a + dot b (v i)))
    (hmass : mass f = mass feq) (hmom : ∀ j, mom v f j = mom v feq j) :
    Hw w (bgk ω f feq) ≤ Hw w f := by
  have hfeqpos : ∀ i, 0 < feq i := fun i => by rw [hfeq i]; exact mul_pos (hw i) (Real.exp_pos _)
  have hconv : Hw w (bgk ω f feq) ≤ (1 - ω) * Hw w f + ω * Hw w feq := by
    simp only [Hw, bgk, Finset.mul_sum, ← Finset.sum_add_distrib]
    exact Finset.sum_le_sum (fun i _ =>
      mul_log_div_convex ω (f i) (feq i) (w i) hω0 hω1 (hf i) (hfeqpos i) (hw i))
  have hmin := entropic_eq_minimizes w v f feq a b hw hf hfeq hmass hmom
  nlinarith [hconv, hmin, mul_le_mul_of_nonneg_left hmin hω0]

/-! ### (d) The exact-difference force step -/

/-- The force step `f ↦ f + feq₂ − feq₁`. -/
def forceStep (f feq₁ feq₂ : Fin n → ℝ) : Fin n → ℝ := fun i => f i + feq₂ i - feq₁ i

theorem force_exact_difference_mass (f feq₁ feq₂ : Fin n → ℝ) (ρ : ℝ)
    (h₁ : mass feq₁ = ρ) (h₂ : mass feq₂ = ρ) :
    mass (forceStep f feq₁ feq₂) = mass f := by
  simp only [mass, forceStep, Finset.sum_sub_distrib, Finset.sum_add_distrib] at h₁ h₂ ⊢
  rw [h₁, h₂]; ring

/-- The force step adds exactly `ρ · g_j · Δt` to momentum component `j` when the two
equilibria carry momenta `ρ u` and `ρ (u + g Δt)`. -/
theorem force_exact_difference_momentum (v : Fin n → Fin d → ℝ) (f feq₁ feq₂ : Fin n → ℝ)
    (ρ Δt : ℝ) (u g : Fin d → ℝ)
    (h₁ : ∀ j, mom v feq₁ j = ρ * u j) (h₂ : ∀ j, mom v feq₂ j = ρ * (u j + g j * Δt))
    (j : Fin d) :
    mom v (forceStep f feq₁ feq₂) j = mom v f j + ρ * g j * Δt := by
  have e1 := h₁ j
  have e2 := h₂ j
  simp only [mom, forceStep] at e1 e2 ⊢
  have e : ∑ i, (f i + feq₂ i - feq₁ i) * v i j
      = ∑ i, f i * v i j + ∑ i, feq₂ i * v i j - ∑ i, feq₁ i * v i j := by
    rw [← Finset.sum_add_distrib, ← Finset.sum_sub_distrib]
    exact Finset.sum_congr rfl (fun i _ => by ring)
  rw [e, e1, e2]; ring

end NonlinearBGKEntropy

#print axioms NonlinearBGKEntropy.entropic_eq_minimizes
#print axioms NonlinearBGKEntropy.bgk_step_conserves_mass
#print axioms NonlinearBGKEntropy.bgk_step_conserves_momentum
#print axioms NonlinearBGKEntropy.bgk_step_pos
#print axioms NonlinearBGKEntropy.bgk_step_entropy_decreases
#print axioms NonlinearBGKEntropy.force_exact_difference_mass
#print axioms NonlinearBGKEntropy.force_exact_difference_momentum
