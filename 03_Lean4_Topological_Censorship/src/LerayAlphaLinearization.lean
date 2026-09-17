import Mathlib.Tactic
import Mathlib.Analysis.Calculus.FDeriv.Bilinear
import Mathlib.Analysis.Calculus.FDeriv.Add

/-!
# Leray-α is invisible to linear dynamics — so it cannot encode the scale where the continuum ends

The Leray-α and LANS-α models keep the viscous term of Navier–Stokes and change only the quadratic
term: `∂ₜu = L u + B (F_α u) u`, with `L = νΔ`, `B` the (projected) transport bilinear form and
`F_α = (1 − α²Δ)⁻¹` the Helmholtz filter. The claim examined in the paper is:

> "If you set the filter width α equal to the physical breakdown scale ℓ* = ν/c_s, the Leray-α model
> becomes a mathematically sound representation of the fluid hitting its continuum limit."

A model represents the fluid at `ℓ*` only if small disturbances of scale `ℓ*` relax in it the way they
relax in the fluid. For a dilute gas that relaxation is known exactly (`KineticSpectralCap.lean`, and
§9.2 of the paper): the damping rate is `ν k² [1 − (kλ)² + …]`, it never exceeds the collision rate
`1/τ`, and the shear mode ends at `kλ = √(π/2)`.

## What is proved

* `filtered_quadratic_hasFDerivAt_zero` — for *any* continuous bilinear `B` and *any* continuous linear
  filter `F`, the map `u ↦ B (F u) u` has derivative `0` at `u = 0`.
* `linearization_independent_of_filter` — hence the linearization of `u ↦ L u + B (F u) u` at rest is
  `L`, whatever `F` is. Leray-α, LANS-α (also quadratic in `u`) and Navier–Stokes itself have the *same*
  linearization at rest, for every `α`: the filter width does not appear.
* `viscous_rate_exceeds_any_cap` — the rate `ν k²` of that common linearization exceeds any finite cap
  `1/τ` for `k` large enough, whereas the kinetic rate never does. So for no value of `α` does Leray-α
  relax a small disturbance at scale `ℓ*` the way the gas does.

This does not say Leray-α is a bad model: it is a well-posed turbulence closure with a proved global
regularity theorem. It says the specific claim above is false: the filter width cannot be calibrated to
the continuum limit, because the part of the dynamics that the continuum limit changes first — linear
relaxation — does not contain `α` at all.
-/

open scoped Topology

namespace LerayAlphaLinearization

variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]

/-- A filtered quadratic nonlinearity has zero derivative at rest, for every filter. -/
theorem filtered_quadratic_hasFDerivAt_zero (B : E →L[ℝ] E →L[ℝ] E) (F : E →L[ℝ] E) :
    HasFDerivAt (fun u : E => B (F u) u) (0 : E →L[ℝ] E) 0 := by
  have hF : HasFDerivAt (fun u : E => F u) F 0 := F.hasFDerivAt
  have h := B.hasFDerivAt_of_bilinear hF (hasFDerivAt_id (0 : E))
  have e : B.precompR E (F 0) (ContinuousLinearMap.id ℝ E) + B.precompL E F (id 0) = 0 := by
    ext v
    simp
  rw [e] at h
  exact h

/-- The linearization at rest of `u ↦ L u + B (F u) u` is `L`: the filter does not appear. -/
theorem linearization_independent_of_filter (L : E →L[ℝ] E) (B : E →L[ℝ] E →L[ℝ] E) (F : E →L[ℝ] E) :
    HasFDerivAt (fun u : E => L u + B (F u) u) L 0 := by
  have hL : HasFDerivAt (fun u : E => L u) L 0 := L.hasFDerivAt
  have h := HasFDerivAt.add hL (filtered_quadratic_hasFDerivAt_zero B F)
  rw [add_zero] at h
  exact h

/-- Two filters give the same linearization at rest. -/
theorem same_linearization (L : E →L[ℝ] E) (B : E →L[ℝ] E →L[ℝ] E) (F G : E →L[ℝ] E) :
    ∃ D : E →L[ℝ] E, HasFDerivAt (fun u : E => L u + B (F u) u) D 0 ∧
      HasFDerivAt (fun u : E => L u + B (G u) u) D 0 :=
  ⟨L, linearization_independent_of_filter L B F, linearization_independent_of_filter L B G⟩

/-- The viscous rate `ν k²` exceeds any finite cap: there is a wavenumber beyond which the common
linearization damps faster than the collision rate `1/τ`, which the kinetic rate never exceeds. -/
theorem viscous_rate_exceeds_any_cap {nu tau : ℝ} (hnu : 0 < nu) (htau : 0 < tau) :
    ∃ k0 : ℝ, 0 < k0 ∧ ∀ k : ℝ, k0 < k → 1 / tau < nu * k ^ 2 := by
  refine ⟨1 / (nu * tau) + 1, by positivity, fun k hk => ?_⟩
  have hx : 0 < 1 / (nu * tau) := by positivity
  have hk1 : 1 < k := by linarith
  have hk2 : k < k ^ 2 := by nlinarith
  have : 1 / (nu * tau) < k ^ 2 := by linarith
  calc 1 / tau = nu * (1 / (nu * tau)) := by field_simp
    _ < nu * k ^ 2 := by exact mul_lt_mul_of_pos_left this hnu

end LerayAlphaLinearization

#print axioms LerayAlphaLinearization.filtered_quadratic_hasFDerivAt_zero
#print axioms LerayAlphaLinearization.linearization_independent_of_filter
#print axioms LerayAlphaLinearization.same_linearization
#print axioms LerayAlphaLinearization.viscous_rate_exceeds_any_cap
