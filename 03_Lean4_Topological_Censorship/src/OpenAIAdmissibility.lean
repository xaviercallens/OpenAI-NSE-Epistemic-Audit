import NavierStokes.ProblemStatement
import NavierStokes.PeriodicIntegration
import NavierStokes.PeriodicUniqueness
import Mathlib.Analysis.Calculus.FDeriv.Comp
import Mathlib.Analysis.Calculus.FDeriv.Prod
import Mathlib.Analysis.Calculus.FDeriv.Add
import Mathlib.Analysis.Calculus.TangentCone.Prod
import Mathlib.Topology.Algebra.Order.Floor

/-!
# Admissibility on OpenAI's own proof objects

**Build.** This file does NOT compile with this folder's own lakefile, because it
imports OpenAI's `NavierStokes.ProblemStatement`, `NavierStokes.PeriodicIntegration`
and `NavierStokes.PeriodicUniqueness`. Compile it inside OpenAI's project:

    cd NavierStokesAndEuler
    lake build NavierStokes.PeriodicUniqueness   # 3 files: ProblemStatement,
                                                 # PeriodicIntegration, PeriodicUniqueness
    lake env lean <path>/OpenAIAdmissibility.lean

Do not build the full `NavierStokes` library (~580 files); nothing else is needed.
(If those three oleans already exist, the `lake build` step is a no-op.)

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

## The former hypothesis is now PROVED: every result is unconditional

`BKMHypothesis` is a `Prop`: *for OpenAI's candidate objects, a uniformly bounded
velocity gradient on `[0, 1)` excludes `SpeedUnboundedAtOne`.* It is proved here as
`bkmHypothesis_holds : BKMHypothesis` (the periodic mean-velocity bound), with no
`sorry` and no axiom beyond `propext`, `Classical.choice`, `Quot.sound`.

The name is kept for continuity with the paper, but the content is **weaker than
Beale–Kato–Majda** and, for these objects, holds by an elementary argument rather
than by BKM. On the unit periodic cell, the mean velocity satisfies
`d/dt ⟨u⟩ = ⟨f⟩`: the Laplacian and pressure gradient of periodic fields integrate
to zero, and `∫(u·∇)u = ∫∇·(u⊗u) = 0` because `∇·u = 0`. The force is smooth and
periodic on `[0, ∞)`, so `⟨f⟩` is bounded on `[0, 1]`, and `u(0) = 0` gives a bounded
mean. A uniform gradient bound `C` then bounds the oscillation over the cell by
`√3·C`, so `|u| ≤ |⟨u⟩| + √3·C` everywhere. The periodic-cell integration by parts
(a torus divergence theorem for the `fderiv`-defined operators of `ProblemStatement`)
is taken from OpenAI's own `NavierStokes.PeriodicIntegration` and
`NavierStokes.PeriodicUniqueness`. The formal steps, along any fixed direction `e`:

* `mean_rate`: `∫⟪e, ∂ₜu⟫ = ∫⟪e, f⟫` over the cube (advection, Laplacian and pressure
  terms integrate to zero by periodicity and `∇·u = 0`);
* `mean_hasDerivAt`: the cell mean `∫⟪e, u(t,·)⟫` has that derivative on `(0, 1)`;
* `mean_le`: with `u(0) = 0` and `‖f‖ ≤ K` on `[0,1] × cube`, the mean is `≤ ‖e‖·K`;
* `bkmHypothesis_holds`: the mean-value inequality gives oscillation `≤ √3·C`, and
  taking `e = u(t,x)` yields `‖u‖ ≤ K + √3·C`, contradicting `speed_unbounded`.

## What is proved

The primed theorems `candidate_violates_every_gradient_bound'`,
`candidate_not_admissible'`, `candidate_not_admissibleScaled'` and
`exits_admissible_near_one'` are the unconditional forms (no hypothesis argument);
the unprimed ones keep their original statement taking `BKMHypothesis` as input.

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
paper constructs; since `bkmHypothesis_holds` is proved, unconditionally.
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

/-- **Periodic mean-velocity bound — proved** (as `bkmHypothesis_holds` below). For
OpenAI's candidate objects, a uniformly bounded velocity gradient on `[0, 1)` excludes
`SpeedUnboundedAtOne`. Named for continuity with the paper, but weaker than
Beale–Kato–Majda: for these periodic, forced, zero-initial-data objects it follows
from the mean-velocity identity `d/dt ⟨u⟩ = ⟨f⟩` plus the oscillation bound `√3·C`
(see the module docstring). The unprimed theorems below take it as an argument; the
primed ones discharge it with `bkmHypothesis_holds`. -/
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

/-! ### `BKMHypothesis` is a theorem: the periodic mean-velocity bound

Everything below uses OpenAI's own periodic-cell integration library
(`NavierStokes.PeriodicIntegration`: cube integrals, the periodic divergence
theorem, differentiation under the integral; `NavierStokes.PeriodicUniqueness`:
periodic integration by parts for the `ProblemStatement` operators). -/

section PeriodicMean

open MeasureTheory
open scoped InnerProductSpace
open NavierStokes.PeriodicIntegration (toSpace cubeIntegral cubeMeasure UnitPeriods spatialPartial
  cubeIntegral_sub cubeIntegral_add cubeIntegral_sum cubeIntegral_zero
  cubeIntegral_mono_on_cube cubeIntegral_continuousOn_Icc hasDerivAt_cubeIntegral_of_contDiffOn)
open NavierStokes.PeriodicUniqueness (slab spatial_smooth exists_cube_representative
  cubeIntegral_fderiv_apply_zero cubeIntegral_inner_partial inner_pressureGradient fderiv_inner
  spatial_partial_contDiff spatial_partial_periodic time_differentiable_at_interior
  spatialLaplacian_contDiff pressureGradient_contDiff)

private theorem nat_le_infty' (n : ℕ) : (n : WithTop ℕ∞) ≤ ∞ :=
  (ENat.natCast_lt_of_coe_top_le_withTop le_rfl n).le

private theorem infty_add_one_le' : (∞ : WithTop ℕ∞) + 1 ≤ ∞ := by
  exact le_of_eq (by rfl)

theorem cubeIntegral_const (c : ℝ) : cubeIntegral (fun _ : Space => c) = c := by
  simp [cubeIntegral, cubeMeasure, NavierStokes.PeriodicIntegration.cube, measureReal_def,
    Real.volume_Icc_pi]

lemma unitPeriods_const (e : Space) : UnitPeriods (fun _ : Space => e) := fun _ _ => rfl

lemma spatialPartial_const (e : Space) (i : Fin 3) (x : Space) :
    spatialPartial i (fun _ : Space => e) x = 0 := by
  simp [spatialPartial]

lemma slab_sub_pre {t : ℝ} (ht : t ∈ Ico (0:ℝ) 1) : slab t t ⊆ preSingularDomain :=
  fun _ hz => ⟨⟨ht.1.trans hz.1.1, hz.1.2.trans_lt ht.2⟩, hz.2⟩

lemma slab_sub_future {t : ℝ} (ht : 0 ≤ t) : slab t t ⊆ futureDomain :=
  fun _ hz => ⟨ht.trans hz.1.1, hz.2⟩

/-- Integrated momentum balance: along a fixed direction `e`, the time derivative of
the velocity has the same cube integral as the force. -/
theorem mean_rate (h : CandidateProperties u p f) (e : Space) {t : ℝ} (ht : t ∈ Ioo (0:ℝ) 1) :
    cubeIntegral (fun x => ⟪e, temporalDerivative u t x⟫_ℝ) =
      cubeIntegral (fun x => ⟪e, f (t, x)⟫_ℝ) := by
  have ht' : t ∈ Ico (0:ℝ) 1 := ⟨ht.1.le, ht.2⟩
  have hmem : t ∈ Icc t t := ⟨le_rfl, le_rfl⟩
  have hU : ContDiff ℝ ∞ (fun x : Space => u (t, x)) :=
    spatial_smooth (h.velocity_smooth.mono (slab_sub_pre ht')) hmem
  have hP : ContDiff ℝ ∞ (fun x : Space => p (t, x)) :=
    spatial_smooth (h.pressure_smooth.mono (slab_sub_pre ht')) hmem
  have hF : ContDiff ℝ ∞ (fun x : Space => f (t, x)) :=
    spatial_smooth (h.force_smooth.mono (slab_sub_future ht.1.le)) hmem
  have hpU : UnitPeriods (fun x : Space => u (t, x)) := fun x i => h.velocity_periodic t ht' x i
  have hpP : UnitPeriods (fun x : Space => p (t, x)) := fun x i => h.pressure_periodic t ht' x i
  have he : ContDiff ℝ ∞ (fun _ : Space => e) := contDiff_const
  have hpt : ∀ x, ⟪e, temporalDerivative u t x⟫_ℝ =
      ⟪e, f (t, x)⟫_ℝ - ⟪e, advection u t x⟫_ℝ + ⟪e, spatialLaplacian u t x⟫_ℝ -
        ⟪e, pressureGradient p t x⟫_ℝ := by
    intro x
    have hns := h.navier_stokes t ht x
    unfold navierStokesResidual at hns
    rw [← hns]
    simp only [inner_add_right, inner_sub_right]
    ring
  -- advection: `⟪e, (u·∇)u⟫ = (u·∇)⟪e, u⟫` integrates to zero since `∇·u = 0`
  have hA : cubeIntegral (fun x => ⟪e, advection u t x⟫_ℝ) = 0 := by
    have hfun : (fun x => ⟪e, advection u t x⟫_ℝ) =
        (fun x => fderiv ℝ (fun y => ⟪e, u (t, y)⟫_ℝ) x (u (t, x))) := by
      funext x
      rw [fderiv_inner he hU x (u (t, x))]
      simp [advection, spatialDerivative]
    have hpe : UnitPeriods (fun y : Space => ⟪e, u (t, y)⟫_ℝ) := by
      intro y i
      simp only [hpU y i]
    rw [hfun]
    exact cubeIntegral_fderiv_apply_zero (he.inner ℝ hU) hU hpe hpU
      (fun x => h.divergence_free t ht' x)
  -- viscous term: each `⟪e, ∂ᵢ∂ᵢu⟫` is a total derivative
  have hL : cubeIntegral (fun x => ⟪e, spatialLaplacian u t x⟫_ℝ) = 0 := by
    have hsum : cubeIntegral (fun x => ⟪e, spatialLaplacian u t x⟫_ℝ) =
        ∑ i : Fin 3, cubeIntegral (fun x =>
          ⟪e, spatialPartial i (spatialPartial i (fun y => u (t, y))) x⟫_ℝ) := by
      simp only [spatialLaplacian, inner_sum]
      exact cubeIntegral_sum Finset.univ _ (fun i _ =>
        (he.inner ℝ (spatial_partial_contDiff (spatial_partial_contDiff hU i) i)).continuous)
    rw [hsum]
    apply Finset.sum_eq_zero
    intro i _
    have hi := cubeIntegral_inner_partial he (spatial_partial_contDiff hU i) (unitPeriods_const e)
      (spatial_partial_periodic hpU i) i
    simp only [spatialPartial_const, inner_zero_left, cubeIntegral_zero, neg_zero] at hi
    exact hi
  -- pressure: `⟪e, ∇p⟫ = ∂ₑp` integrates to zero
  have hPr : cubeIntegral (fun x => ⟪e, pressureGradient p t x⟫_ℝ) = 0 := by
    have hfun : (fun x => ⟪e, pressureGradient p t x⟫_ℝ) =
        (fun x => fderiv ℝ (fun y => p (t, y)) x ((fun _ : Space => e) x)) := by
      funext x
      exact inner_pressureGradient p t x e
    rw [hfun]
    exact cubeIntegral_fderiv_apply_zero hP he hpP (unitPeriods_const e)
      (fun x => by simp [spatialPartial_const])
  have c1 := (he.inner ℝ hF).continuous
  have c2 : Continuous (fun x => ⟪e, advection u t x⟫_ℝ) := (he.inner ℝ ((hU.fderiv_right infty_add_one_le').clm_apply hU)).continuous
  have c3 := (he.inner ℝ (spatialLaplacian_contDiff hU)).continuous
  have c4 := (he.inner ℝ (pressureGradient_contDiff hP)).continuous
  rw [show (fun x => ⟪e, temporalDerivative u t x⟫_ℝ) = _ from funext hpt,
    cubeIntegral_sub ((c1.fun_sub c2).fun_add c3) c4, cubeIntegral_add (c1.fun_sub c2) c3,
    cubeIntegral_sub c1 c2]
  rw [hA, hL, hPr]
  ring

/-- The directional cell mean `t ↦ ∫_cube ⟪e, u(t,·)⟫` has derivative `∫_cube ⟪e, f(t,·)⟫`. -/
theorem mean_hasDerivAt (h : CandidateProperties u p f) (e : Space) {t : ℝ}
    (ht : t ∈ Ioo (0:ℝ) 1) :
    HasDerivAt (fun s => cubeIntegral (fun x => ⟪e, u (s, x)⟫_ℝ))
      (cubeIntegral (fun x => ⟪e, f (t, x)⟫_ℝ)) t := by
  have hF : ContDiffOn ℝ 1 (fun z : SpaceTime => ⟪e, u z⟫_ℝ) (Ioo (0:ℝ) 1 ×ˢ univ) :=
    ((contDiffOn_const.inner ℝ h.velocity_smooth).of_le (nat_le_infty' 1)).mono
      (fun z hz => ⟨⟨hz.1.1.le, hz.1.2⟩, hz.2⟩)
  have hd := hasDerivAt_cubeIntegral_of_contDiffOn
    (F := fun z : SpaceTime => ⟪e, u z⟫_ℝ) isOpen_Ioo hF ht
  have hb : t < (t + 1) / 2 := by linarith [ht.2]
  have hsub : slab 0 ((t + 1) / 2) ⊆ preSingularDomain :=
    fun _ hz => ⟨⟨hz.1.1, hz.1.2.trans_lt (by linarith [ht.2])⟩, hz.2⟩
  have hrate : (fun x => deriv (fun s => ⟪e, u (s, x)⟫_ℝ) t) =
      (fun x => ⟪e, temporalDerivative u t x⟫_ℝ) := by
    funext x
    have hu' := (time_differentiable_at_interior (h.velocity_smooth.mono hsub)
      ⟨ht.1, hb⟩ x).hasDerivAt
    exact ((innerSL ℝ e).hasFDerivAt.comp_hasDerivAt t hu').deriv
  rw [hrate, mean_rate h e ht] at hd
  exact hd

/-- Mean-velocity bound: the directional cell mean is at most `‖e‖·K` on `(0, 1)`. -/
theorem mean_le (h : CandidateProperties u p f) :
    ∃ K : ℝ, 0 ≤ K ∧ ∀ e : Space, ∀ t ∈ Ioo (0:ℝ) 1,
      cubeIntegral (fun x => ⟪e, u (t, x)⟫_ℝ) ≤ ‖e‖ * K := by
  have hK : IsCompact (Icc (0:ℝ) 1 ×ˢ (toSpace '' NavierStokes.PeriodicIntegration.cube)) :=
    isCompact_Icc.prod ((show IsCompact NavierStokes.PeriodicIntegration.cube from
      isCompact_Icc).image toSpace.continuous)
  obtain ⟨K0, hK0⟩ := hK.exists_bound_of_continuousOn
    (h.force_smooth.continuousOn.mono (fun z hz => ⟨hz.1.1, mem_univ _⟩))
  refine ⟨max K0 0, le_max_right _ _, fun e t ht => ?_⟩
  set K := max K0 0
  have hforce : ∀ s ∈ Ioo (0:ℝ) 1, cubeIntegral (fun x => ⟪e, f (s, x)⟫_ℝ) ≤ ‖e‖ * K := by
    intro s hs
    have hF : ContDiff ℝ ∞ (fun x : Space => f (s, x)) :=
      spatial_smooth (h.force_smooth.mono (slab_sub_future hs.1.le)) ⟨le_rfl, le_rfl⟩
    calc cubeIntegral (fun x => ⟪e, f (s, x)⟫_ℝ) ≤ cubeIntegral (fun _ : Space => ‖e‖ * K) :=
          cubeIntegral_mono_on_cube (contDiff_const.inner ℝ hF).continuous continuous_const
            (fun y hy => (real_inner_le_norm _ _).trans (mul_le_mul_of_nonneg_left
              ((hK0 (s, toSpace y) ⟨⟨hs.1.le, hs.2.le⟩, y, hy, rfl⟩).trans (le_max_left _ _))
              (norm_nonneg _)))
      _ = ‖e‖ * K := cubeIntegral_const _
  set m : ℝ → ℝ := fun s => cubeIntegral (fun x => ⟪e, u (s, x)⟫_ℝ) with hm
  have hcont : ContinuousOn m (Icc 0 t) :=
    cubeIntegral_continuousOn_Icc (F := fun z : SpaceTime => ⟪e, u z⟫_ℝ)
      ((continuousOn_const.inner h.velocity_smooth.continuousOn).mono
        (fun _ hz => ⟨⟨hz.1.1, hz.1.2.trans_lt ht.2⟩, hz.2⟩))
  obtain ⟨c, hc, hceq⟩ := exists_hasDerivAt_eq_slope m
    (fun s => cubeIntegral (fun x => ⟪e, f (s, x)⟫_ℝ)) ht.1 hcont
    (fun s hs => mean_hasDerivAt h e ⟨hs.1, hs.2.trans ht.2⟩)
  have hm0 : m 0 = 0 := by
    simp [hm, h.zero_initial_velocity]
  rw [hm0, sub_zero, sub_zero, eq_div_iff ht.1.ne'] at hceq
  have hfc := hforce c ⟨hc.1, hc.2.trans ht.2⟩
  have hK0' : 0 ≤ ‖e‖ * K := mul_nonneg (norm_nonneg _) (le_max_right _ _)
  change m t ≤ _
  nlinarith [ht.1, ht.2]

/-- **Periodic mean-velocity bound — proved** (the statement formerly assumed as
`BKMHypothesis`; the name is kept for continuity). For OpenAI's candidate objects, a
uniformly bounded velocity gradient on `[0, 1)` excludes `SpeedUnboundedAtOne`:
the directional cell mean is at most `‖e‖·K` (`mean_le`), the oscillation over the
cell is at most `√3·C`, so `‖u‖ ≤ K + √3·C` on `(0, 1) × ℝ³`. -/
theorem bkmHypothesis_holds : BKMHypothesis := by
  rintro u p f h ⟨C, hC⟩ hsp
  obtain ⟨K, hK0, hK⟩ := mean_le h
  have hC0 : 0 ≤ C := (norm_nonneg _).trans (hC 0 ⟨le_rfl, one_pos⟩ 0)
  have h3 : 0 ≤ Real.sqrt 3 * C := mul_nonneg (Real.sqrt_nonneg _) hC0
  obtain ⟨t, x, ht, -, hbig⟩ := hsp (K + Real.sqrt 3 * C + 1) (by positivity) 1 one_pos
  have ht' : t ∈ Ico (0:ℝ) 1 := ⟨ht.1.le, ht.2⟩
  have hU : ContDiff ℝ ∞ (fun y : Space => u (t, y)) :=
    spatial_smooth (h.velocity_smooth.mono (slab_sub_pre ht')) ⟨le_rfl, le_rfl⟩
  obtain ⟨z, hz, hzx⟩ := exists_cube_representative (f := fun y : Space => u (t, y))
    (fun i y => h.velocity_periodic t ht' y i) x
  have hlip : ∀ a b : Space, ‖u (t, a) - u (t, b)‖ ≤ C * ‖a - b‖ := fun a b =>
    convex_univ.norm_image_sub_le_of_norm_fderiv_le
      (fun y _ => hU.differentiable (by simp) y) (fun y _ => hC t ht' y) (mem_univ b) (mem_univ a)
  have hdist : ∀ y ∈ NavierStokes.PeriodicIntegration.cube, ‖z - toSpace y‖ ≤ Real.sqrt 3 := by
    intro y hy
    rw [EuclideanSpace.norm_eq]
    apply Real.sqrt_le_sqrt
    have hi : ∀ i, ‖(z - toSpace y) i‖ ^ 2 ≤ 1 := by
      intro i
      have h1 := hz i
      have h2 := hy.1 i
      have h3 := hy.2 i
      have hcoord : (z - toSpace y) i = z i - y i := rfl
      rw [hcoord, Real.norm_eq_abs, sq_abs]
      simp only [Pi.zero_apply, Pi.one_apply] at h2 h3
      nlinarith [h1.1, h1.2]
    calc ∑ i, ‖(z - toSpace y) i‖ ^ 2 ≤ ∑ _i : Fin 3, (1:ℝ) := Finset.sum_le_sum fun i _ => hi i
      _ = 3 := by simp
  set e := u (t, z) with he
  have hosc : ⟪e, e⟫_ℝ - ‖e‖ * (Real.sqrt 3 * C) ≤ cubeIntegral (fun y => ⟪e, u (t, y)⟫_ℝ) := by
    calc ⟪e, e⟫_ℝ - ‖e‖ * (Real.sqrt 3 * C)
        = cubeIntegral (fun _ : Space => ⟪e, e⟫_ℝ - ‖e‖ * (Real.sqrt 3 * C)) :=
          (cubeIntegral_const _).symm
      _ ≤ _ := by
        apply cubeIntegral_mono_on_cube continuous_const (contDiff_const.inner ℝ hU).continuous
        intro y hy
        have h1 : ⟪e, e⟫_ℝ - ⟪e, u (t, toSpace y)⟫_ℝ ≤ ‖e‖ * (Real.sqrt 3 * C) := by
          rw [← inner_sub_right]
          refine (real_inner_le_norm _ _).trans (mul_le_mul_of_nonneg_left ?_ (norm_nonneg _))
          calc ‖e - u (t, toSpace y)‖ ≤ C * ‖z - toSpace y‖ := hlip z (toSpace y)
            _ ≤ C * Real.sqrt 3 := mul_le_mul_of_nonneg_left (hdist y hy) hC0
            _ = Real.sqrt 3 * C := mul_comm _ _
        linarith
  have hmean := hK e t ht
  rw [real_inner_self_eq_norm_sq] at hosc
  have hnorm : ‖u (t, x)‖ = ‖e‖ := by rw [he]; exact congrArg norm hzx.symm
  rw [hnorm] at hbig
  nlinarith [norm_nonneg e]

end PeriodicMean

/-! ### Unconditional corollaries -/

/-- (1, unconditional) A candidate has no uniform gradient bound on `[0, 1)`. -/
theorem candidate_violates_every_gradient_bound' (hc : CandidateProperties u p f) :
    ∀ C : ℝ, ¬ GradientBoundedOn u 1 C :=
  candidate_violates_every_gradient_bound bkmHypothesis_holds hc

/-- (2, unconditional) A candidate is not admissible for any fluid. -/
theorem candidate_not_admissible' (hc : CandidateProperties u p f) :
    ∀ c nu : ℝ, ¬ Admissible c nu u :=
  candidate_not_admissible bkmHypothesis_holds hc

/-- (2', unconditional) A candidate is not admissible for any fluid in any system of units. -/
theorem candidate_not_admissibleScaled' (hc : CandidateProperties u p f) :
    ∀ L U c nu : ℝ, 0 < L → 0 < U → 0 < c → 0 < nu → ¬ AdmissibleScaled L U c nu u :=
  candidate_not_admissibleScaled bkmHypothesis_holds hc

/-- (3, unconditional) Every gradient bound is exceeded arbitrarily close to `t = 1`. -/
theorem exits_admissible_near_one' (hc : CandidateProperties u p f) :
    ∀ C δ : ℝ, 0 < δ → ∃ t ∈ Ioo (1 - δ) 1, ∃ x : Space, C < ‖spatialDerivative u t x‖ :=
  exits_admissible_near_one bkmHypothesis_holds hc

end OpenAIAdmissibility

#print axioms OpenAIAdmissibility.admissibleScaled_iff
#print axioms OpenAIAdmissibility.candidate_violates_every_gradient_bound
#print axioms OpenAIAdmissibility.candidate_not_admissible
#print axioms OpenAIAdmissibility.candidate_not_admissibleScaled
#print axioms OpenAIAdmissibility.spatialDerivative_eq_fderivWithin
#print axioms OpenAIAdmissibility.gradient_bounded_before
#print axioms OpenAIAdmissibility.exits_admissible_near_one
#print axioms OpenAIAdmissibility.mean_rate
#print axioms OpenAIAdmissibility.mean_hasDerivAt
#print axioms OpenAIAdmissibility.mean_le
#print axioms OpenAIAdmissibility.bkmHypothesis_holds
#print axioms OpenAIAdmissibility.candidate_violates_every_gradient_bound'
#print axioms OpenAIAdmissibility.candidate_not_admissible'
#print axioms OpenAIAdmissibility.candidate_not_admissibleScaled'
#print axioms OpenAIAdmissibility.exits_admissible_near_one'
