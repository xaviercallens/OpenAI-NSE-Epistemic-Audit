import Mathlib.Tactic
import Mathlib.Analysis.InnerProductSpace.Basic

/-!
# AlphaEnergyIdentity — "the lock is a gate, not a drain", algebraic skeleton

The Leray-α nonlinearity `N(u) = −P[(ū·∇)u]` does no work on `u`: `⟪u, N u⟫ = 0`,
because the advection operator `(ū·∇)` is skew-adjoint on solenoidal fields when
`∇·ū = 0`, and the Leray projector `P` is an orthogonal projection. That single
identity is why inviscid Leray-α conserves `½∫|u|²` exactly while suppressing peak
vorticity — the "gate, not drain" measurement of the flagship paper's §9.

WHAT IS PROVED (finite-dimensional linear algebra over a real inner product space):
  (a) `skew_self_inner`          ⟪x, A x⟫ = 0 for skew-adjoint A
  (b) `gate_no_work`             u = P u  ⇒  ⟪u, P (A u)⟫ = 0
  (c) `energy_conserved_discrete` ‖u + h•P(A u)‖² = ‖u‖² + h²‖P(A u)‖²
                                  (no first-order energy change: the gate)
  (d) `drain_is_first_order`     for dissipative D (⟪x, D x⟫ < 0 for x ≠ 0) there is
                                  h > 0 with ‖u + h•D u‖² < ‖u‖²  (the drain), and
      `drain_decreases_of_small` the explicit small-h condition.

WHAT IS NOT PROVED: that the continuum operator `(ū·∇)` is skew-adjoint on the
solenoidal subspace — that analytic fact enters as the HYPOTHESIS `IsSkew A`; and
nothing about the well-posedness of Leray-α or Navier–Stokes.
Inner products are written `inner ℝ x y` (this Mathlib's `⟪·,·⟫_ℝ` notation lives in
the `InnerProductSpace` scope). No `sorry`, no `axiom`; see `#print axioms` at the end.
-/
namespace AlphaEnergyIdentity


variable {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]

/-- Skew-adjointness: `⟪A x, y⟫ = −⟪x, A y⟫`. Models the advection operator on
solenoidal fields. -/
def IsSkew (A : V →ₗ[ℝ] V) : Prop := ∀ x y : V, (inner ℝ (A x) (y)) = -(inner ℝ (x) (A y))

/-- Orthogonal projection: idempotent and self-adjoint. Models the Leray projector. -/
def IsOrthProj (P : V →ₗ[ℝ] V) : Prop :=
  (∀ x : V, P (P x) = P x) ∧ (∀ x y : V, (inner ℝ (P x) (y)) = (inner ℝ (x) (P y)))

/-- Dissipative operator: strictly negative quadratic form off the origin. Models
`ν Δ` (or a hyperviscous barrier). -/
def IsDissipative (D : V →ₗ[ℝ] V) : Prop := ∀ x : V, x ≠ 0 → (inner ℝ (x) (D x)) < 0

/-- (a) A skew-adjoint operator does no work: `⟪x, A x⟫ = 0`. -/
theorem skew_self_inner (A : V →ₗ[ℝ] V) (hA : IsSkew A) (x : V) : (inner ℝ (x) (A x)) = 0 := by
  have h := hA x x
  rw [real_inner_comm x (A x)] at h
  linarith

/-- (b) The projected skew term does no work on a field already in the range of `P`. -/
theorem gate_no_work (A P : V →ₗ[ℝ] V) (hA : IsSkew A) (hP : IsOrthProj P)
    (u : V) (hu : P u = u) : (inner ℝ (u) (P (A u))) = 0 := by
  rw [← hP.2 u (A u), hu]
  exact skew_self_inner A hA u

/-- (c) One explicit-Euler step of the gated dynamics changes the energy only at
second order in `h`: there is no first-order term. This is the discrete form of
`d/dt ½‖u‖² = 0`. -/
theorem energy_conserved_discrete (A P : V →ₗ[ℝ] V) (hA : IsSkew A) (hP : IsOrthProj P)
    (u : V) (hu : P u = u) (h : ℝ) :
    ‖u + h • P (A u)‖ ^ 2 = ‖u‖ ^ 2 + h ^ 2 * ‖P (A u)‖ ^ 2 := by
  rw [norm_add_sq_real, real_inner_smul_right, gate_no_work A P hA hP u hu, norm_smul,
    Real.norm_eq_abs, mul_pow, sq_abs]
  ring

/-- Contrast, explicit condition: for a dissipative `D` and `0 < h` with
`h ‖D u‖² < −2⟪u, D u⟫`, one Euler step strictly decreases the energy. -/
theorem drain_decreases_of_small (D : V →ₗ[ℝ] V) (hD : IsDissipative D)
    (u : V) (hu : u ≠ 0) (h : ℝ) (hh : 0 < h) (hsmall : h * ‖D u‖ ^ 2 < -2 * (inner ℝ (u) (D u))) :
    ‖u + h • D u‖ ^ 2 < ‖u‖ ^ 2 := by
  have hneg := hD u hu
  rw [norm_add_sq_real, real_inner_smul_right, norm_smul, Real.norm_eq_abs, mul_pow, sq_abs]
  have key : 2 * (h * (inner ℝ (u) (D u))) + h ^ 2 * ‖D u‖ ^ 2 = h * (2 * (inner ℝ (u) (D u)) + h * ‖D u‖ ^ 2) := by
    ring
  have hlt : 2 * (inner ℝ (u) (D u)) + h * ‖D u‖ ^ 2 < 0 := by linarith
  have := mul_neg_of_pos_of_neg hh hlt
  linarith

/-- (d) The drain is first order: for dissipative `D` and `u ≠ 0` there is a step
`h > 0` after which the energy has strictly decreased. -/
theorem drain_is_first_order (D : V →ₗ[ℝ] V) (hD : IsDissipative D) (u : V) (hu : u ≠ 0) :
    ∃ h : ℝ, 0 < h ∧ ‖u + h • D u‖ ^ 2 < ‖u‖ ^ 2 := by
  have hneg := hD u hu
  have hDu : D u ≠ 0 := by
    intro h0
    rw [h0, inner_zero_right] at hneg
    exact lt_irrefl _ hneg
  have hs : 0 < ‖D u‖ ^ 2 := pow_pos (norm_pos_iff.mpr hDu) 2
  refine ⟨-(inner ℝ (u) (D u)) / ‖D u‖ ^ 2, div_pos (by linarith) hs, ?_⟩
  apply drain_decreases_of_small D hD u hu _ (div_pos (by linarith) hs)
  rw [div_mul_cancel₀ _ hs.ne']
  linarith

#print axioms skew_self_inner
#print axioms gate_no_work
#print axioms energy_conserved_discrete
#print axioms drain_decreases_of_small
#print axioms drain_is_first_order

end AlphaEnergyIdentity
