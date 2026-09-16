import Mathlib.Analysis.SpecialFunctions.Sqrt
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Tactic

/-!
# CoreScaling — Proposition 5.1 of the flagship paper as a formal scaling theorem

WHAT IS PROVED. Given a core on the *diffusive scaling* at time-to-blowup `t > 0`,
    ℓ t = √(ν t),   u t = √(ν / t),
the following are elementary identities of real arithmetic:
  (a) `Re_core`        u·ℓ/ν = 1                       (the premise is Re = 1, exactly)
  (b) `mach_time`      u = Ma·c  ↔  t = ν/(Ma² c²);  and then ℓ = ν/(Ma·c)
  (c) `knudsen_time`   λ/ℓ = Kn  ↔  t = λ²/(Kn² ν)
  (d) `heating`        ε·t/cp = u²/cp with ε = ν (u/ℓ)²  (Eckert number one)
  (e) `one_scale`      at t* = ν/c²:  ℓ = ℓ* = ν/c,  u = c  (Mach 1),  and with the
                       kinetic relation ν = ½ c̄ λ, c̄ = c, the Knudsen number λ/ℓ* = 2.

WHAT IS NOT PROVED. Nothing here is about the Navier–Stokes equations, about OpenAI's
`VelocityField`, or about any PDE. The "coincidence of the three validity limits at ℓ*"
is *this equality chain and nothing deeper*: it is what the diffusive-scaling
hypotheses force, and the hypotheses are inputs, not conclusions. The O(1) prefactors of
the physical estimates are absent by construction (the scalings are taken with unit
constants). The intermolecular length is written `lam` because `λ` is a Lean keyword.
No `sorry`, no `axiom`; see `#print axioms` at the end.
-/
namespace CoreScaling

/-- Core radius on the diffusive scaling: ℓ(t) = √(ν t). -/
noncomputable def ℓ (ν t : ℝ) : ℝ := Real.sqrt (ν * t)

/-- Core velocity on the diffusive scaling: u(t) = √(ν / t). -/
noncomputable def u (ν t : ℝ) : ℝ := Real.sqrt (ν / t)

/-- Viscous dissipation per unit mass at the core scale: ε = ν (u/ℓ)². -/
noncomputable def ε (ν t : ℝ) : ℝ := ν * (u ν t / ℓ ν t) ^ 2

/-- The validity length ℓ* = ν / c. -/
noncomputable def ℓstar (ν c : ℝ) : ℝ := ν / c

/-- The validity time t* = ν / c². -/
noncomputable def tstar (ν c : ℝ) : ℝ := ν / c ^ 2

variable {ν c cp Ma Kn lam cbar t : ℝ}

/-- ℓ(t)² = ν t. -/
theorem ℓ_sq (hν : 0 < ν) (ht : 0 < t) : (ℓ ν t) ^ 2 = ν * t := by
  unfold ℓ; exact Real.sq_sqrt (by positivity)

/-- ℓ(t) > 0. -/
theorem ℓ_pos (hν : 0 < ν) (ht : 0 < t) : 0 < ℓ ν t := by
  unfold ℓ; exact Real.sqrt_pos.mpr (by positivity)

/-- u(t)² = ν / t. -/
theorem u_sq (hν : 0 < ν) (ht : 0 < t) : (u ν t) ^ 2 = ν / t := by
  unfold u; exact Real.sq_sqrt (by positivity)

/-- (a) The core Reynolds number is exactly one: u ℓ / ν = 1. This is the *premise* of
the cutoff law, not a consequence of anything. -/
theorem Re_core (hν : 0 < ν) (ht : 0 < t) : u ν t * ℓ ν t / ν = 1 := by
  unfold u ℓ
  rw [← Real.sqrt_mul (by positivity)]
  have h : ν / t * (ν * t) = ν ^ 2 := by
    have := ht.ne'
    field_simp
  rw [h, Real.sqrt_sq hν.le]
  exact div_self hν.ne'

/-- (b) Mach number Ma is reached exactly at t = ν / (Ma² c²). -/
theorem mach_time (hν : 0 < ν) (hc : 0 < c) (hMa : 0 < Ma) (ht : 0 < t) :
    u ν t = Ma * c ↔ t = ν / (Ma ^ 2 * c ^ 2) := by
  have hMc : 0 < Ma ^ 2 * c ^ 2 := by positivity
  constructor
  · intro h
    have h2 : ν / t = (Ma * c) ^ 2 := by
      rw [← h]; exact (u_sq hν ht).symm
    rw [div_eq_iff ht.ne'] at h2
    rw [eq_div_iff hMc.ne', h2]
    ring
  · intro h
    unfold u
    rw [h]
    have h2 : ν / (ν / (Ma ^ 2 * c ^ 2)) = (Ma * c) ^ 2 := by
      have := hν.ne'
      have := hMa.ne'
      have := hc.ne'
      field_simp
    rw [h2, Real.sqrt_sq (by positivity)]

/-- (b′) At the Mach-Ma time the core radius is ν / (Ma c). -/
theorem mach_radius (hν : 0 < ν) (hc : 0 < c) (hMa : 0 < Ma) :
    ℓ ν (ν / (Ma ^ 2 * c ^ 2)) = ν / (Ma * c) := by
  unfold ℓ
  have h : ν * (ν / (Ma ^ 2 * c ^ 2)) = (ν / (Ma * c)) ^ 2 := by
    have := hMa.ne'
    have := hc.ne'
    field_simp
  rw [h, Real.sqrt_sq (by positivity)]

/-- (c) Knudsen number Kn (with molecular length `lam`) is reached exactly at
t = lam² / (Kn² ν). -/
theorem knudsen_time (hν : 0 < ν) (hlam : 0 < lam) (hKn : 0 < Kn) (ht : 0 < t) :
    lam / ℓ ν t = Kn ↔ t = lam ^ 2 / (Kn ^ 2 * ν) := by
  have hs : 0 < ℓ ν t := ℓ_pos hν ht
  have hK : 0 < Kn ^ 2 * ν := by positivity
  constructor
  · intro h
    rw [div_eq_iff hs.ne'] at h            -- lam = Kn * ℓ
    have h1 : ℓ ν t = lam / Kn := by
      rw [eq_div_iff hKn.ne', h]; ring
    have h2 : ν * t = (lam / Kn) ^ 2 := by
      rw [← h1]; exact (ℓ_sq hν ht).symm
    rw [eq_div_iff hK.ne']
    calc t * (Kn ^ 2 * ν) = Kn ^ 2 * (ν * t) := by ring
      _ = Kn ^ 2 * (lam / Kn) ^ 2 := by rw [h2]
      _ = lam ^ 2 := by
          have := hKn.ne'
          field_simp
  · intro h
    unfold ℓ
    rw [h]
    have h2 : ν * (lam ^ 2 / (Kn ^ 2 * ν)) = (lam / Kn) ^ 2 := by
      have := hν.ne'
      have := hKn.ne'
      field_simp
    rw [h2, Real.sqrt_sq (by positivity)]
    have := hlam.ne'
    have := hKn.ne'
    field_simp

/-- (d) Eckert number one: the heat released over the remaining time equals the local
kinetic energy per unit mass, ε t / cp = u² / cp. This is why ΔT = u²/cp in §5. -/
theorem heating (hν : 0 < ν) (hcp : 0 < cp) (ht : 0 < t) :
    ε ν t * t / cp = (u ν t) ^ 2 / cp := by
  unfold ε
  rw [div_pow, ℓ_sq hν ht]
  have := hν.ne'
  have := ht.ne'
  have := hcp.ne'
  field_simp

/-- (e) At t* the core radius is ℓ*. -/
theorem radius_at_tstar (hν : 0 < ν) (hc : 0 < c) : ℓ ν (tstar ν c) = ℓstar ν c := by
  unfold ℓ tstar ℓstar
  have h : ν * (ν / c ^ 2) = (ν / c) ^ 2 := by
    have := hc.ne'
    field_simp
  rw [h, Real.sqrt_sq (by positivity)]

/-- (e) At t* the core velocity is the sound speed. -/
theorem velocity_at_tstar (hν : 0 < ν) (hc : 0 < c) : u ν (tstar ν c) = c := by
  unfold u tstar
  have h : ν / (ν / c ^ 2) = c ^ 2 := by
    have := hν.ne'
    have := hc.ne'
    field_simp
  rw [h, Real.sqrt_sq hc.le]

/-- (e) Hence the Mach number at t* is exactly one. -/
theorem mach_at_tstar (hν : 0 < ν) (hc : 0 < c) : u ν (tstar ν c) / c = 1 := by
  rw [velocity_at_tstar hν hc]; exact div_self hc.ne'

/-- (e) With the kinetic-theory relation ν = ½ c̄ λ and c̄ = c (both explicit hypotheses),
the Knudsen number at t* is exactly 2: the three validity limits meet at ℓ* because ℓ* is,
up to this factor, the molecular length. -/
theorem knudsen_at_tstar (hν : 0 < ν) (hc : 0 < c) (hlam : 0 < lam)
    (hkin : ν = (1 / 2) * cbar * lam) (hcbar : cbar = c) :
    lam / ℓ ν (tstar ν c) = 2 := by
  rw [radius_at_tstar hν hc]
  unfold ℓstar
  rw [hkin, hcbar]
  have := hc.ne'
  have := hlam.ne'
  field_simp

/-- (e) The three limits at one scale, packaged: at t* the radius is ℓ*, Mach = 1, and the
Eckert identity (d) holds. This is the whole content of "one scale": an equality chain. -/
theorem one_scale (hν : 0 < ν) (hc : 0 < c) (hcp : 0 < cp) :
    ℓ ν (tstar ν c) = ℓstar ν c ∧ u ν (tstar ν c) / c = 1 ∧
    ε ν (tstar ν c) * tstar ν c / cp = (u ν (tstar ν c)) ^ 2 / cp := by
  have ht : 0 < tstar ν c := by unfold tstar; positivity
  exact ⟨radius_at_tstar hν hc, mach_at_tstar hν hc, heating hν hcp ht⟩

end CoreScaling

#print axioms CoreScaling.Re_core
#print axioms CoreScaling.mach_time
#print axioms CoreScaling.mach_radius
#print axioms CoreScaling.knudsen_time
#print axioms CoreScaling.heating
#print axioms CoreScaling.radius_at_tstar
#print axioms CoreScaling.velocity_at_tstar
#print axioms CoreScaling.mach_at_tstar
#print axioms CoreScaling.knudsen_at_tstar
#print axioms CoreScaling.one_scale
