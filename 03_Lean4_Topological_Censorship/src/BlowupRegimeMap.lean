import Mathlib.Tactic
import Mathlib.Analysis.SpecificLimits.Basic
import Mathlib.Analysis.SpecialFunctions.Sqrt

/-!
# The regime map of blow-up scenarios: which physics a collapsing scale meets first

For a flow feature of velocity `u` and size `ℓ` in a fluid of kinematic viscosity `ν` and sound
speed `c` (all positive) put

* `Re = u ℓ / ν`  (local Reynolds number),
* `Ma = u / c`    (local Mach number),
* `Kn = ℓ* / ℓ`, with `ℓ* = ν / c` (the validity length of the paper; for a dilute gas `ℓ*` is the
  mean free path up to the kinetic constant `0.67`).

## What is proved

1. `kn_eq_ma_div_re` — the von Kármán relation `Kn = Ma / Re`. Everything below is a corollary.
2. `admissible_iff` — the paper's local admissibility bound `u/ℓ ≤ c²/ν` is exactly `Ma² ≤ Re`.
3. Three routes to a singularity sit in three different places on this map:
   * `diffusive_route` (OpenAI's Navier–Stokes construction, `Re = 1`): `Kn = Ma`, so compressibility
     and rarefaction fail together, at `ℓ = ℓ*` — Proposition 5.1 of the paper as one line;
   * `inertial_route_sonic_in_continuum` (`Re > 1`, as in Tao's averaged-equation blow-up, where
     `Re → ∞`): at `Ma = 1` one still has `Kn < 1`; the first model to fail is incompressibility,
     inside the continuum, at `ℓ = Re · ℓ*` (`sonic_scale`);
   * `bounded_velocity_route` (`Ma < 1` fixed, as in the forced Euler blow-up with bounded velocity and
     unbounded gradients): the scale at which viscosity matters, `Re = 1`, is `ℓ*/Ma > ℓ*`
     (`viscous_scale`, `viscous_scale_gt`), so the neglected viscosity acts before the continuum ends.
4. `tao_route_reynolds_unbounded` — along a cascade whose stages shrink by `s²` and speed up by `s⁵`
   (`s > 1`; Tao's `(1+ε₀)` and `(1+ε₀)^{5/2}` with `s² = 1+ε₀`), velocity grows as `s³ⁿ`, the local
   Reynolds number is `Re₀ sⁿ → ∞` and `Kn/Ma = 1/Re → 0`.
5. `hole_feedback_sign` — for a fluid whose dynamic viscosity does not depend on density, forced per
   unit mass by the incompressible residual `-(5/4) ν Δu`, the net diffusion coefficient at relative
   density `ρ̂` is `ν (1/ρ̂ - 5/4)`: negative (collapse continues) iff `ρ̂ > 4/5`.

6. `atomistic_speed_bound` — the only unconditional "lock" in the hierarchy of models: for finitely many
   particles of mass `m` whose kinetic energy is at most `E`, every particle has `|v| ≤ √(2E/m)`.
   No continuum model (incompressible, compressible, kinetic) carries such a bound; a finite-energy
   particle system cannot avoid it.

Nothing here is a statement about solutions of any PDE. These are the algebraic facts that decide which
physical assumption a given blow-up scenario violates first, stated so they cannot be misquoted.
-/

namespace BlowupRegimeMap

/-- local Reynolds number -/
noncomputable def Re (u l nu : ℝ) : ℝ := u * l / nu
/-- local Mach number -/
noncomputable def Ma (u c : ℝ) : ℝ := u / c
/-- validity length `ℓ* = ν / c` -/
noncomputable def lstar (nu c : ℝ) : ℝ := nu / c
/-- local Knudsen number in units of `ℓ*` -/
noncomputable def Kn (l nu c : ℝ) : ℝ := lstar nu c / l

variable {u l nu c : ℝ}

/-- von Kármán relation. -/
theorem kn_eq_ma_div_re (hu : 0 < u) (hl : 0 < l) (hnu : 0 < nu) (hc : 0 < c) :
    Kn l nu c = Ma u c / Re u l nu := by
  unfold Kn lstar Ma Re
  field_simp

/-- The local admissibility bound `u/ℓ ≤ c²/ν` is `Ma² ≤ Re`. -/
theorem admissible_iff (hu : 0 < u) (hl : 0 < l) (hnu : 0 < nu) (hc : 0 < c) :
    u / l ≤ c ^ 2 / nu ↔ Ma u c ^ 2 ≤ Re u l nu := by
  unfold Ma Re
  rw [div_le_div_iff₀ hl hnu, div_pow, div_le_div_iff₀ (by positivity) hnu]
  constructor <;> intro h <;> nlinarith [mul_pos hu hl, mul_pos hu hnu, mul_pos hl hnu]

/-- Diffusive route (`Re = 1`): rarefaction and compressibility fail together. -/
theorem diffusive_route (hu : 0 < u) (hl : 0 < l) (hnu : 0 < nu) (hc : 0 < c)
    (hRe : Re u l nu = 1) : Kn l nu c = Ma u c := by
  rw [kn_eq_ma_div_re hu hl hnu hc, hRe, div_one]

/-- On the diffusive route the sonic point is exactly `ℓ = ℓ*`. -/
theorem diffusive_route_sonic_at_lstar (hu : 0 < u) (hl : 0 < l) (hnu : 0 < nu) (hc : 0 < c)
    (hRe : Re u l nu = 1) (hMa : Ma u c = 1) : l = lstar nu c := by
  have h := diffusive_route hu hl hnu hc hRe
  rw [hMa] at h
  unfold Kn at h
  have hl' : l ≠ 0 := hl.ne'
  field_simp at h
  linarith

/-- Inertial route (`Re > 1`): rarefaction lags compressibility, `Kn < Ma`. -/
theorem inertial_route (hu : 0 < u) (hl : 0 < l) (hnu : 0 < nu) (hc : 0 < c)
    (hRe : 1 < Re u l nu) : Kn l nu c < Ma u c := by
  rw [kn_eq_ma_div_re hu hl hnu hc]
  have hMa : 0 < Ma u c := div_pos hu hc
  exact div_lt_self hMa hRe

/-- Inertial route: at the sonic point the flow is still a continuum. -/
theorem inertial_route_sonic_in_continuum (hu : 0 < u) (hl : 0 < l) (hnu : 0 < nu) (hc : 0 < c)
    (hRe : 1 < Re u l nu) (hMa : Ma u c = 1) : Kn l nu c < 1 := by
  have := inertial_route hu hl hnu hc hRe
  rwa [hMa] at this

/-- The sonic scale is `Re · ℓ*`: larger than `ℓ*` by the local Reynolds number. -/
theorem sonic_scale (hu : 0 < u) (_hl : 0 < l) (hnu : 0 < nu) (hc : 0 < c)
    (hMa : Ma u c = 1) : l = Re u l nu * lstar nu c := by
  unfold Ma at hMa
  have huc : u = c := by field_simp at hMa; linarith
  unfold Re lstar
  subst huc
  field_simp

/-- Bounded-velocity route: the viscous scale (`Re = 1`) is `ℓ*/Ma`. -/
theorem viscous_scale (hu : 0 < u) (_hl : 0 < l) (hnu : 0 < nu) (hc : 0 < c)
    (hRe : Re u l nu = 1) : l = lstar nu c / Ma u c := by
  unfold Re at hRe
  unfold lstar Ma
  field_simp at hRe ⊢
  linarith

/-- Bounded-velocity route, subsonic: viscosity acts at a scale larger than `ℓ*`. -/
theorem viscous_scale_gt (hu : 0 < u) (hl : 0 < l) (hnu : 0 < nu) (hc : 0 < c)
    (hRe : Re u l nu = 1) (hMa : Ma u c < 1) : lstar nu c < l := by
  have hM : 0 < Ma u c := div_pos hu hc
  have hL : 0 < lstar nu c := div_pos hnu hc
  rw [viscous_scale hu hl hnu hc hRe, lt_div_iff₀ hM]
  nlinarith

/-- Tao-type cascade: stage `n` has size `ℓ₀ s^{-2n}` and velocity `u₀ s^{3n}` (each stage `s²` smaller
and `s⁵` faster). Its Reynolds number is `Re₀ sⁿ`. -/
theorem tao_route_reynolds (u0 l0 : ℝ) (hnu : 0 < nu) {s : ℝ} (hs : 0 < s) (n : ℕ) :
    Re (u0 * s ^ (3 * n)) (l0 / s ^ (2 * n)) nu = Re u0 l0 nu * s ^ n := by
  unfold Re
  have : s ^ (3 * n) = s ^ (2 * n) * s ^ n := by rw [← pow_add]; congr 1; ring
  rw [this]
  have h2 : s ^ (2 * n) ≠ 0 := (pow_pos hs _).ne'
  field_simp

/-- ... which is unbounded: dissipation becomes negligible, and `Kn/Ma = 1/Re → 0`. -/
theorem tao_route_reynolds_unbounded (u0 l0 : ℝ) (hnu : 0 < nu) {s : ℝ} (hs : 1 < s)
    (hRe0 : 0 < Re u0 l0 nu) :
    Filter.Tendsto (fun n : ℕ => Re (u0 * s ^ (3 * n)) (l0 / s ^ (2 * n)) nu) Filter.atTop Filter.atTop := by
  have hs0 : 0 < s := lt_trans zero_lt_one hs
  simp_rw [tao_route_reynolds u0 l0 hnu hs0]
  exact Filter.Tendsto.const_mul_atTop hRe0 (tendsto_pow_atTop_atTop_of_one_lt hs)

/-- Density-hole feedback. With dynamic viscosity independent of density the local kinematic
viscosity is `ν/ρ̂`; against a per-unit-mass force that supplies anti-diffusion `(5/4) ν`, the net
diffusion coefficient is `ν (1/ρ̂ − 5/4)`, negative (collapse continues) iff `ρ̂ > 4/5`. -/
theorem hole_feedback_sign (hnu : 0 < nu) {rho : ℝ} (hrho : 0 < rho) :
    nu * (1 / rho - 5 / 4) < 0 ↔ 4 / 5 < rho := by
  rw [mul_neg_iff]
  constructor
  · rintro (⟨-, h⟩ | ⟨h, -⟩)
    · rw [sub_neg, div_lt_iff₀ hrho] at h; linarith
    · linarith
  · intro h
    left
    refine ⟨hnu, ?_⟩
    rw [sub_neg, div_lt_iff₀ hrho]; linarith

/-- Atomistic lock: with total kinetic energy `∑ ½ m vᵢ² ≤ E`, each speed is at most `√(2E/m)`. -/
theorem atomistic_speed_bound {N : ℕ} {m E : ℝ} (hm : 0 < m) (v : Fin N → ℝ)
    (hE : ∑ i, (1 / 2) * m * v i ^ 2 ≤ E) (i : Fin N) : |v i| ≤ Real.sqrt (2 * E / m) := by
  have hterm : (1 / 2) * m * v i ^ 2 ≤ ∑ j, (1 / 2) * m * v j ^ 2 :=
    Finset.single_le_sum (f := fun j => (1 / 2) * m * v j ^ 2) (fun j _ => by positivity) (Finset.mem_univ i)
  have h2 : v i ^ 2 ≤ 2 * E / m := by
    rw [le_div_iff₀ hm]; nlinarith
  calc |v i| = Real.sqrt (v i ^ 2) := (Real.sqrt_sq_eq_abs _).symm
    _ ≤ Real.sqrt (2 * E / m) := Real.sqrt_le_sqrt h2

end BlowupRegimeMap

#print axioms BlowupRegimeMap.kn_eq_ma_div_re
#print axioms BlowupRegimeMap.admissible_iff
#print axioms BlowupRegimeMap.diffusive_route
#print axioms BlowupRegimeMap.diffusive_route_sonic_at_lstar
#print axioms BlowupRegimeMap.inertial_route
#print axioms BlowupRegimeMap.inertial_route_sonic_in_continuum
#print axioms BlowupRegimeMap.sonic_scale
#print axioms BlowupRegimeMap.viscous_scale
#print axioms BlowupRegimeMap.viscous_scale_gt
#print axioms BlowupRegimeMap.tao_route_reynolds
#print axioms BlowupRegimeMap.tao_route_reynolds_unbounded
#print axioms BlowupRegimeMap.hole_feedback_sign
#print axioms BlowupRegimeMap.atomistic_speed_bound
