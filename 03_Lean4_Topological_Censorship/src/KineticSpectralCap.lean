import Mathlib.Tactic
import Mathlib.Analysis.InnerProductSpace.Basic

/-!
# Kinetic spectral cap: relaxation never exceeds the collision rate

Linearised discrete-velocity BGK at a Fourier wavenumber `k` has the form

  `L = A − (1/τ)(1 − P)`,

where `A` (streaming, `f_i ↦ −i k c_i f_i`) is skew-adjoint and `P` (projection onto the
collision invariants) is an orthogonal projection in the equilibrium-weighted inner product.

## WHAT IS PROVED

* `re_inner_skew_zero`       : `A` skew-adjoint ⇒ `Re⟪x, A x⟫ = 0`.
* `numerical_range_cap`      : `−(1/τ)‖x‖² ≤ Re⟪x, L x⟫ ≤ 0`.
* `eigenvalue_damping_cap`   : `L x = μ x`, `x ≠ 0` ⇒ `−1/τ ≤ Re μ ≤ 0`.
* `streaming_skew`           : the streaming multiplier `−i k c_i` is skew-adjoint for the
  weighted form `⟪f, g⟫_w = ∑ w_i conj(f_i) g_i` (real `k`, `c_i`, `w_i`).
* `meanProj_idem`, `meanProj_selfAdj` : the weighted-mean projection
  `(P f)_i = ∑_j w_j f_j` is idempotent when `∑ w = 1` and `w`-self-adjoint for any real `w`.

This is why every eigenvalue computed in `experiments/lock_k_kinetic_spectrum.py` lies in the
strip `−1/τ ≤ Re λ ≤ 0`: kinetic relaxation is capped by the collision rate at every `k`.

## WHAT IS NOT PROVED

* Nothing about the termination point `kλ = √(π/2)` of the hydrodynamic branch, nor the
  Burnett correction; those are properties of a specific (continuous-velocity) spectrum.
* The concrete streaming/projection statements are given as explicit weighted sums on
  `Fin n → ℂ`, not as an `InnerProductSpace` instance; the abstract theorems apply to them
  after the change of variables `f ↦ √w f` (which turns the weighted form into the standard one).
* Only the full-rank (single-invariant, mass) projection is instantiated concretely; the
  abstract theorems hold for any orthogonal projection `P`.

No sorry, no axiom.
-/

namespace KineticSpectralCap

open ComplexConjugate

variable {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℂ V]

/-- Skew-adjointness of a linear map. -/
def IsSkew (A : V →ₗ[ℂ] V) : Prop := ∀ x y : V, inner ℂ (A x) y = -inner ℂ x (A y)

/-- Orthogonal projection: idempotent and self-adjoint. -/
def IsOrthProj (P : V →ₗ[ℂ] V) : Prop :=
  (∀ x, P (P x) = P x) ∧ (∀ x y, inner ℂ (P x) y = inner ℂ x (P y))

/-- The linearised BGK operator `L = A − (1/τ)(1 − P)`. -/
noncomputable def Lop (A P : V →ₗ[ℂ] V) (τ : ℝ) (x : V) : V := A x - ((1 / τ : ℝ) : ℂ) • (x - P x)

theorem re_inner_skew_zero (A : V →ₗ[ℂ] V) (hA : IsSkew A) (x : V) :
    (inner ℂ x (A x)).re = 0 := by
  have h1 : inner ℂ (A x) x = -inner ℂ x (A x) := hA x x
  have h2 : conj (inner ℂ x (A x)) = inner ℂ (A x) x := inner_conj_symm _ _
  have h3 : (conj (inner ℂ x (A x))).re = (inner ℂ x (A x)).re := Complex.conj_re _
  rw [h2, h1, Complex.neg_re] at h3
  linarith

/-- `Re⟪x, P x⟫ = ‖P x‖²` and `‖P x‖² ≤ ‖x‖²` for an orthogonal projection. -/
theorem proj_facts (P : V →ₗ[ℂ] V) (hP : IsOrthProj P) (x : V) :
    (inner ℂ x (P x)).re = ‖P x‖ ^ 2 ∧ ‖P x‖ ^ 2 ≤ ‖x‖ ^ 2 := by
  have e : inner ℂ x (P x) = inner ℂ (P x) (P x) := by
    rw [hP.2 x (P x), hP.1 x]
  have hre : (inner ℂ x (P x)).re = ‖P x‖ ^ 2 := by
    rw [e]; exact inner_self_eq_norm_sq (𝕜 := ℂ) (P x)
  refine ⟨hre, ?_⟩
  have hle : ‖P x‖ ^ 2 ≤ ‖x‖ * ‖P x‖ := by
    rw [← hre]
    exact (Complex.re_le_norm _).trans (norm_inner_le_norm _ _)
  rcases eq_or_lt_of_le (norm_nonneg (P x)) with h0 | hpos
  · rw [← h0]; simp only [ne_eq, OfNat.ofNat_ne_zero, not_false_eq_true, zero_pow]; positivity
  · have : ‖P x‖ ≤ ‖x‖ := by nlinarith
    exact pow_le_pow_left₀ (norm_nonneg _) this 2

theorem re_inner_L (A P : V →ₗ[ℂ] V) (hA : IsSkew A) (hP : IsOrthProj P) (τ : ℝ) (x : V) :
    (inner ℂ x (Lop A P τ x)).re = -(1 / τ) * (‖x‖ ^ 2 - ‖P x‖ ^ 2) := by
  unfold Lop
  rw [inner_sub_right, inner_smul_right, inner_sub_right, Complex.sub_re,
    re_inner_skew_zero A hA x, Complex.re_ofReal_mul, Complex.sub_re,
    (proj_facts P hP x).1]
  have hx : (inner ℂ x x).re = ‖x‖ ^ 2 := inner_self_eq_norm_sq (𝕜 := ℂ) x
  rw [hx]
  ring

theorem numerical_range_cap (A P : V →ₗ[ℂ] V) (hA : IsSkew A) (hP : IsOrthProj P)
    (τ : ℝ) (hτ : 0 < τ) (x : V) :
    -(1 / τ) * ‖x‖ ^ 2 ≤ (inner ℂ x (Lop A P τ x)).re ∧
      (inner ℂ x (Lop A P τ x)).re ≤ 0 := by
  rw [re_inner_L A P hA hP τ x]
  have h := (proj_facts P hP x).2
  have hτ' : 0 < 1 / τ := by positivity
  have hPn : 0 ≤ ‖P x‖ ^ 2 := by positivity
  constructor <;> nlinarith

theorem eigenvalue_damping_cap (A P : V →ₗ[ℂ] V) (hA : IsSkew A) (hP : IsOrthProj P)
    (τ : ℝ) (hτ : 0 < τ) (x : V) (hx : x ≠ 0) (μ : ℂ) (hμ : Lop A P τ x = μ • x) :
    -(1 / τ) ≤ μ.re ∧ μ.re ≤ 0 := by
  have hcap := numerical_range_cap A P hA hP τ hτ x
  have hre : (inner ℂ x (Lop A P τ x)).re = μ.re * ‖x‖ ^ 2 := by
    rw [hμ, inner_smul_right, inner_self_eq_norm_sq_to_K (𝕜 := ℂ) x]
    simp [Complex.mul_re, sq]
  rw [hre] at hcap
  have hn : 0 < ‖x‖ ^ 2 := by have := norm_pos_iff.mpr hx; positivity
  obtain ⟨h1, h2⟩ := hcap
  constructor
  · by_contra hc; push Not at hc; nlinarith
  · by_contra hc; push Not at hc; nlinarith

/-! ## Concrete discrete-velocity instance (weighted sums) -/

/-- Weighted sesquilinear form `⟪f, g⟫_w = ∑ w_i conj(f_i) g_i`. -/
def winner {n : ℕ} (w : Fin n → ℝ) (f g : Fin n → ℂ) : ℂ :=
  ∑ i, (w i : ℂ) * conj (f i) * g i

/-- Streaming at wavenumber `k`: `(A f)_i = −i k c_i f_i`. -/
def stream {n : ℕ} (k : ℝ) (c : Fin n → ℝ) (f : Fin n → ℂ) : Fin n → ℂ :=
  fun i => -(Complex.I * k * c i) * f i

theorem streaming_skew {n : ℕ} (w : Fin n → ℝ) (k : ℝ) (c : Fin n → ℝ) (f g : Fin n → ℂ) :
    winner w (stream k c f) g = -winner w f (stream k c g) := by
  unfold winner stream
  rw [← Finset.sum_neg_distrib]
  refine Finset.sum_congr rfl fun i _ => ?_
  simp only [map_mul, map_neg, Complex.conj_I, Complex.conj_ofReal]
  ring

/-- Weighted-mean projection `(P f)_i = ∑_j w_j f_j`. -/
def meanProj {n : ℕ} (w : Fin n → ℝ) (f : Fin n → ℂ) : Fin n → ℂ :=
  fun _ => ∑ j, (w j : ℂ) * f j

theorem meanProj_idem {n : ℕ} (w : Fin n → ℝ) (hw : ∑ i, w i = 1) (f : Fin n → ℂ) :
    meanProj w (meanProj w f) = meanProj w f := by
  funext i
  unfold meanProj
  rw [← Finset.sum_mul]
  have : (∑ j, (w j : ℂ)) = 1 := by exact_mod_cast hw
  rw [this, one_mul]

theorem meanProj_selfAdj {n : ℕ} (w : Fin n → ℝ) (f g : Fin n → ℂ) :
    winner w (meanProj w f) g = winner w f (meanProj w g) := by
  unfold winner meanProj
  simp only [map_sum, map_mul, Complex.conj_ofReal]
  have e1 : ∀ i, (w i : ℂ) * (∑ j, (w j : ℂ) * conj (f j)) * g i
      = (∑ j, (w j : ℂ) * conj (f j)) * ((w i : ℂ) * g i) := fun i => by ring
  simp only [e1]
  rw [← Finset.mul_sum, ← Finset.sum_mul]

end KineticSpectralCap

#print axioms KineticSpectralCap.re_inner_skew_zero
#print axioms KineticSpectralCap.numerical_range_cap
#print axioms KineticSpectralCap.eigenvalue_damping_cap
#print axioms KineticSpectralCap.streaming_skew
#print axioms KineticSpectralCap.meanProj_idem
#print axioms KineticSpectralCap.meanProj_selfAdj
