import NavierStokes.ProblemStatement
import Mathlib.Analysis.Calculus.FDeriv.Comp
import Mathlib.Analysis.Calculus.FDeriv.Prod
import Mathlib.Analysis.Calculus.FDeriv.Add
import Mathlib.Analysis.Calculus.TangentCone.Prod
import Mathlib.Topology.Algebra.Order.Floor

/-!
# Admissibility on OpenAI's own proof objects

**Build.** This file does NOT compile with this folder's own lakefile, because it
imports OpenAI's `NavierStokes.ProblemStatement`. Compile it inside OpenAI's project:

    cd NavierStokesAndEuler
    lake build NavierStokes.ProblemStatement     # imports only Mathlib; fast
    lake env lean <path>/OpenAIAdmissibility.lean

Do not build the full `NavierStokes` library (~580 files); nothing else is needed.

This is the first file in this project whose statements are about OpenAI's
*actual* definitions: `VelocityField`, `spatialDerivative`, `SpeedUnboundedAtOne`
and `CandidateProperties` are imported unchanged from
`NavierStokes.ProblemStatement` of the `NavierStokesAndEuler` repository.

## What is defined

* `GradientBoundedOn u T C`: the operator norm of the spatial velocity gradient is
  at most `C` on `[0, T) × ℝ³`. The operator norm of `∇u` dominates both the
  vorticity magnitude and the rate-of-strain magnitude, so this is the
  Lean-friendly form of the paper's local admissibility bound `|ω| ≲ c²/ν`, and it
  also answers the paper's "wrong field?" question: a bound on `‖∇u‖` constrains
  strain (hence local dissipation) and vorticity at once.
* `Admissible c ν u`: `GradientBoundedOn u 1 (c²/ν)`, the bound in simulation units.
* `AdmissibleScaled L U c ν u`: the same bound read through a dimensional
  embedding in which one simulation length is `L` metres and one simulation
  velocity is `U` metres per second, so a physical gradient is `(U/L)` times the
  simulated one. `admissibleScaled_iff` converts between the two.

## What is ASSUMED, and nothing here proves it

`BKMHypothesis` is an explicit hypothesis, passed as an argument, never an axiom:
*for OpenAI's candidate objects, a uniformly bounded velocity gradient on `[0, 1)`
excludes `SpeedUnboundedAtOne`.* No statement in this file proves it, which is why
it never appears in a `#print axioms` output.

The name is kept for continuity with the paper, but the content is **weaker than
Beale–Kato–Majda** and, for these objects, holds by an elementary argument rather
than by BKM. On the unit periodic cell, the mean velocity satisfies
`d/dt ⟨u⟩ = ⟨f⟩`: the Laplacian and pressure gradient of periodic fields integrate
to zero, and `∫(u·∇)u = ∫∇·(u⊗u) = 0` because `∇·u = 0`. The force is smooth and
periodic on `[0, ∞)`, so `⟨f⟩` is bounded on `[0, 1]`, and `u(0) = 0` gives a bounded
mean. A uniform gradient bound `C` then bounds the oscillation over the cell by
`√3·C`, so `|u| ≤ |⟨u⟩| + √3·C` everywhere. It is left as a hypothesis only because
formalizing it needs integration by parts over the periodic cell for the
`fderiv`-defined operators of `ProblemStatement` (a torus divergence theorem), which
Mathlib does not provide in this form. The theorems below are therefore conditional
on a true but unformalized elementary lemma, not on a deep analytic theorem.

## What is proved

1. `candidate_violates_every_gradient_bound`: under `BKMHypothesis`, any `u`
   satisfying OpenAI's `CandidateProperties` has no uniform gradient bound on
   `[0, 1)`.
2. `candidate_not_admissible`, `candidate_not_admissibleScaled`: consequently it
   is not admissible for any fluid (`c`, `ν`) and in any system of units (`L`, `U`).
3. `exits_admissible_near_one`: moreover, every gradient bound is exceeded
   arbitrarily close to `t = 1`. Besides (1), this uses a fact that *is* proved
   here without extra hypotheses (`gradient_bounded_before`): on every `[0, 1 - δ]`
   the gradient is uniformly bounded. The velocity is `C^∞` relative to the closed
   initial time (so `fderivWithin` is continuous on `preSingularDomain`, which has
   unique derivatives), the spatial slice derivative is that within-derivative
   restricted to the spatial factor, integer-lattice periodicity moves every point
   into the compact unit cube, and a continuous function on the compact set
   `[0, 1 - δ] × cube` is bounded.

Nothing here says the construction exists, and nothing here says anything about
physical fluids beyond the definitional content of the bound. The theorems
constrain *any* object with OpenAI's candidate properties, including the one their
paper constructs, conditional on `BKMHypothesis`.
-/

noncomputable section

open Set Filter Topology
open scoped ContDiff

namespace OpenAIAdmissibility

open NavierStokes.ProblemStatement

/-- Uniform bound `C` on the operator norm of the spatial velocity gradient on
`[0, T) × ℝ³`. Dominates both vorticity and strain magnitude. -/
def GradientBoundedOn (u : VelocityField) (T C : ℝ) : Prop :=
  ∀ t ∈ Ico (0 : ℝ) T, ∀ x : Space, ‖spatialDerivative u t x‖ ≤ C

/-- The paper's local admissibility bound `‖∇u‖ ≤ c²/ν`, in simulation units. -/
def Admissible (c nu : ℝ) (u : VelocityField) : Prop :=
  GradientBoundedOn u 1 (c ^ 2 / nu)

/-- The admissibility bound under a dimensional embedding: one simulation length
is `L` m and one simulation velocity is `U` m/s, so the physical gradient is
`(U / L)` times the simulated gradient. -/
def AdmissibleScaled (L U c nu : ℝ) (u : VelocityField) : Prop :=
  ∀ t ∈ Ico (0 : ℝ) 1, ∀ x : Space, (U / L) * ‖spatialDerivative u t x‖ ≤ c ^ 2 / nu

/-- Unit conversion: the scaled bound is the simulation-unit bound with threshold
`(L / U) · c²/ν`. -/
theorem admissibleScaled_iff {L U c nu : ℝ} (hL : 0 < L) (hU : 0 < U)
    (u : VelocityField) :
    AdmissibleScaled L U c nu u ↔ GradientBoundedOn u 1 ((L / U) * (c ^ 2 / nu)) := by
  have hUL : 0 < U / L := div_pos hU hL
  constructor
  · intro h t ht x
    have := h t ht x
    rw [show (L / U) * (c ^ 2 / nu) = (c ^ 2 / nu) / (U / L) by field_simp]
    exact (le_div_iff₀ hUL).2 (by linarith [mul_comm (U / L) ‖spatialDerivative u t x‖])
  · intro h t ht x
    have := h t ht x
    rw [show (L / U) * (c ^ 2 / nu) = (c ^ 2 / nu) / (U / L) by field_simp] at this
    have := (le_div_iff₀ hUL).1 this
    linarith [mul_comm (U / L) ‖spatialDerivative u t x‖]

/-- **HYPOTHESIS, not a theorem and not an axiom.** For OpenAI's candidate objects,
a uniformly bounded velocity gradient on `[0, 1)` excludes `SpeedUnboundedAtOne`.
Named for continuity with the paper, but weaker than Beale–Kato–Majda: for these
periodic, forced, zero-initial-data objects it follows from the mean-velocity
identity `d/dt ⟨u⟩ = ⟨f⟩` plus the oscillation bound `√3·C` (see the module
docstring), which needs torus integration by parts not available here in this form.
Not proved in this file; every use below takes it as an explicit argument. -/
def BKMHypothesis : Prop :=
  ∀ (u : VelocityField) (p : PressureField) (f : VelocityField),
    CandidateProperties u p f → (∃ C, GradientBoundedOn u 1 C) → ¬ SpeedUnboundedAtOne u

variable {u : VelocityField} {p : PressureField} {f : VelocityField}

/-- (1) Under the hypothesis, a candidate has no uniform gradient bound on `[0, 1)`. -/
theorem candidate_violates_every_gradient_bound (hBKM : BKMHypothesis)
    (hc : CandidateProperties u p f) : ∀ C : ℝ, ¬ GradientBoundedOn u 1 C := by
  intro C hC
  exact hBKM u p f hc ⟨C, hC⟩ hc.speed_unbounded

/-- (2) Under the hypothesis, a candidate is not admissible for any fluid. -/
theorem candidate_not_admissible (hBKM : BKMHypothesis)
    (hc : CandidateProperties u p f) : ∀ c nu : ℝ, ¬ Admissible c nu u := by
  intro c nu
  exact candidate_violates_every_gradient_bound hBKM hc (c ^ 2 / nu)

/-- (2') Under the hypothesis, a candidate is not admissible for any fluid (`c > 0`, `ν > 0`)
in any system of units (`L > 0`, `U > 0`). -/
theorem candidate_not_admissibleScaled (hBKM : BKMHypothesis)
    (hc : CandidateProperties u p f) :
    ∀ L U c nu : ℝ, 0 < L → 0 < U → 0 < c → 0 < nu → ¬ AdmissibleScaled L U c nu u := by
  intro L U c nu hL hU _ _ h
  exact candidate_violates_every_gradient_bound hBKM hc _ ((admissibleScaled_iff hL hU u).1 h)

/-! ### Unconditional part: the gradient is bounded away from `t = 1` -/

lemma uniqueDiffOn_preSingular : UniqueDiffOn ℝ preSingularDomain :=
  (uniqueDiffOn_Ico 0 1).prod uniqueDiffOn_univ

/-- Slice derivative equals the within-derivative on the domain, restricted to the spatial factor. -/
lemma spatialDerivative_eq_fderivWithin (hs : ContDiffOn ℝ ∞ u preSingularDomain)
    {t : ℝ} (ht : t ∈ Ico (0:ℝ) 1) (x : Space) :
    spatialDerivative u t x =
      (fderivWithin ℝ u preSingularDomain (t, x)).comp (ContinuousLinearMap.inr ℝ ℝ Space) := by
  have hmem : (t, x) ∈ preSingularDomain := ⟨ht, mem_univ _⟩
  have hd : DifferentiableWithinAt ℝ u preSingularDomain (t, x) :=
    (hs.differentiableOn (by simp)) (t, x) hmem
  have hg : HasFDerivWithinAt (fun y : Space => ((t, y) : SpaceTime))
      (ContinuousLinearMap.inr ℝ ℝ Space) univ x :=
    (hasFDerivAt_prodMk_right t x).hasFDerivWithinAt
  have hmaps : MapsTo (fun y : Space => ((t, y) : SpaceTime)) univ preSingularDomain :=
    fun y _ => ⟨ht, mem_univ _⟩
  have hc := HasFDerivWithinAt.comp x hd.hasFDerivWithinAt hg hmaps
  rw [hasFDerivWithinAt_univ] at hc
  exact hc.fderiv

lemma continuousOn_slice_norm (hs : ContDiffOn ℝ ∞ u preSingularDomain) :
    ContinuousOn (fun q : SpaceTime =>
      ‖(fderivWithin ℝ u preSingularDomain q).comp (ContinuousLinearMap.inr ℝ ℝ Space)‖)
      preSingularDomain := by
  have h1 := hs.continuousOn_fderivWithin uniqueDiffOn_preSingular (by simp)
  have hL : Continuous (fun L : SpaceTime →L[ℝ] Space => L.comp (ContinuousLinearMap.inr ℝ ℝ Space)) :=
    ((ContinuousLinearMap.compL ℝ Space SpaceTime Space).flip (ContinuousLinearMap.inr ℝ ℝ Space)).continuous
  exact continuous_norm.comp_continuousOn (hL.comp_continuousOn h1)

/-- Integer-shift periodicity along one coordinate. -/
lemma periodic_int {t : ℝ} (hp : UnitSpatialPeriodsOn (Ico (0:ℝ) 1) u) (ht : t ∈ Ico (0:ℝ) 1)
    (i : Fin 3) (n : ℤ) (y : Space) :
    u (t, y + (n:ℝ) • coordinateVector i) = u (t, y) := by
  induction n using Int.induction_on generalizing y with
  | zero => simp
  | succ k ih =>
      simp only [Int.cast_add, Int.cast_one, add_smul, one_smul]
      rw [← add_assoc, hp t ht, ih]
  | pred k ih =>
      simp only [Int.cast_sub, Int.cast_one, sub_smul, one_smul]
      rw [← add_sub_assoc, unit_period_negative hp ht, ih]

def latticeShift (x : Space) : Space := ∑ i : Fin 3, ((⌊x i⌋ : ℤ) : ℝ) • coordinateVector i

lemma periodic_lattice {t : ℝ} (hp : UnitSpatialPeriodsOn (Ico (0:ℝ) 1) u) (ht : t ∈ Ico (0:ℝ) 1)
    (x y : Space) : u (t, y + latticeShift x) = u (t, y) := by
  simp only [latticeShift, Fin.sum_univ_three]
  rw [← add_assoc, ← add_assoc, periodic_int hp ht 2, periodic_int hp ht 1, periodic_int hp ht 0]

lemma spatialDerivative_shift {t : ℝ} (hp : UnitSpatialPeriodsOn (Ico (0:ℝ) 1) u)
    (ht : t ∈ Ico (0:ℝ) 1) (x y : Space) :
    spatialDerivative u t (y + latticeShift x) = spatialDerivative u t y := by
  unfold spatialDerivative
  rw [← fderiv_comp_add_right (f := fun y => u (t, y)) (latticeShift x)]
  congr 1
  funext z
  exact periodic_lattice hp ht x z

lemma sub_latticeShift_apply (x : Space) (j : Fin 3) :
    (x - latticeShift x) j = Int.fract (x j) := by
  rw [← Int.self_sub_floor]
  fin_cases j <;> simp [latticeShift, coordinateVector, Fin.sum_univ_three]

def cube : Set Space := {y | ∀ j, y j ∈ Icc (0:ℝ) 1}

lemma isCompact_cube : IsCompact cube := by
  have h : cube = (EuclideanSpace.equiv (Fin 3) ℝ) ⁻¹' (Set.pi univ fun _ => Icc (0:ℝ) 1) := by
    ext y; simp only [cube, Set.mem_ofPred_eq, mem_preimage, Set.mem_pi, mem_univ, true_implies]; rfl
  rw [h]
  exact (EuclideanSpace.equiv (Fin 3) ℝ).toHomeomorph.isCompact_preimage.2
    (isCompact_univ_pi fun _ => isCompact_Icc)

lemma sub_latticeShift_mem_cube (x : Space) : x - latticeShift x ∈ cube := by
  intro j
  rw [sub_latticeShift_apply]
  exact ⟨Int.fract_nonneg _, (Int.fract_lt_one _).le⟩

/-- Unconditional: a smooth periodic velocity field has a uniformly bounded
spatial gradient on every `[0, 1 - δ]`. -/
theorem gradient_bounded_before (hs : ContDiffOn ℝ ∞ u preSingularDomain)
    (hp : UnitSpatialPeriodsOn (Ico (0:ℝ) 1) u) {δ : ℝ} (hδ : 0 < δ) :
    ∃ B : ℝ, ∀ t ∈ Icc (0:ℝ) (1 - δ), ∀ x : Space, ‖spatialDerivative u t x‖ ≤ B := by
  have hK : IsCompact (Icc (0:ℝ) (1 - δ) ×ˢ cube) := isCompact_Icc.prod isCompact_cube
  have hsub : Icc (0:ℝ) (1 - δ) ×ˢ cube ⊆ preSingularDomain := by
    rintro ⟨t, y⟩ ⟨ht, _⟩
    exact ⟨⟨ht.1, by linarith [ht.2]⟩, mem_univ _⟩
  obtain ⟨B, hB⟩ := hK.exists_bound_of_continuousOn ((continuousOn_slice_norm hs).mono hsub)
  refine ⟨B, fun t ht x => ?_⟩
  have ht' : t ∈ Ico (0:ℝ) 1 := ⟨ht.1, by linarith [ht.2]⟩
  set y := x - latticeShift x with hy
  have hx : x = y + latticeShift x := by rw [hy, sub_add_cancel]
  rw [hx, spatialDerivative_shift hp ht' x y, spatialDerivative_eq_fderivWithin hs ht' y]
  have := hB (t, y) ⟨ht, sub_latticeShift_mem_cube x⟩
  rwa [Real.norm_of_nonneg (norm_nonneg _)] at this

/-- (3) Under the hypothesis, every gradient bound is exceeded arbitrarily close
to `t = 1`: a candidate leaves the admissible set in every final time window. -/
theorem exits_admissible_near_one (hBKM : BKMHypothesis)
    (hc : CandidateProperties u p f) :
    ∀ C δ : ℝ, 0 < δ → ∃ t ∈ Ioo (1 - δ) 1, ∃ x : Space, C < ‖spatialDerivative u t x‖ := by
  intro C δ hδ
  by_contra hcon
  push Not at hcon
  obtain ⟨B, hB⟩ := gradient_bounded_before hc.velocity_smooth hc.velocity_periodic hδ
  apply candidate_violates_every_gradient_bound hBKM hc (max B C)
  intro t ht x
  by_cases h : t ≤ 1 - δ
  · exact (hB t ⟨ht.1, h⟩ x).trans (le_max_left _ _)
  · exact (hcon t ⟨lt_of_not_ge h, ht.2⟩ x).trans (le_max_right _ _)

end OpenAIAdmissibility

#print axioms OpenAIAdmissibility.admissibleScaled_iff
#print axioms OpenAIAdmissibility.candidate_violates_every_gradient_bound
#print axioms OpenAIAdmissibility.candidate_not_admissible
#print axioms OpenAIAdmissibility.candidate_not_admissibleScaled
#print axioms OpenAIAdmissibility.spatialDerivative_eq_fderivWithin
#print axioms OpenAIAdmissibility.gradient_bounded_before
#print axioms OpenAIAdmissibility.exits_admissible_near_one
