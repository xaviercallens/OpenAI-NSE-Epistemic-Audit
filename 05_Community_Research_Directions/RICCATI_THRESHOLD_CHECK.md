# Does the OpenAI construction sit at the dyadic Riccati threshold?

**Date:** 2026-09-16
**Question:** `DyadicRiccati.lean` formalises a threshold at `α = 1/2`. Our flagship paper reports
integrated enstrophy `Ω ~ τ^{-1/2-3h}`. Are these the same `1/2`?

**Verdict: no — coincidence.** The two `1/2`s are different objects in different slots of the same
formula. But the check turned up an exact correspondence that is more interesting than the one
asked about, and it is stated in §4.

---

## 1. What `α` actually is in `DyadicRiccati.lean`

`α` is **not** a temporal blow-up exponent. It is the **dissipation index** of the dyadic
(Katz–Pavlović / Cheskidov) shell model — the power of the Stokes operator in the model's
dissipation term — and it enters through a bilinear estimate quoted from
Cheskidov (arXiv:math/0601074). From the file's own header:

```
    pExp α = 1/α − 1      exponent of |Au| in  |(B(u,u),Au)| ≤ c_b |Au|^p ‖u‖^q   [source]
    qExp α = 4 − 1/α      exponent of ‖u‖ there;  pExp + qExp = 3  (homogeneity)
    Young absorption against −ν|Au|² is possible  ⟺  pExp α < 2  ⟺  α > 1/3       [source]
    rExp α = 2·qExp/(2 − pExp) = (8α−2)/(3α−1)    post-Young exponent of ‖u‖      [source]
    sExp α = rExp/2 = (4α−1)/(3α−1)               Riccati:  y′ ≤ C y^s,  y = ‖u‖²
    rhoExp α = 1/(sExp − 1) = 3 − 1/α             rate:  y ≥ c (t*−t)^{−ρ}        [derived]
```

So the chain is `α` (a fixed model parameter) → `ρ(α)` (a temporal rate). The quantity that lives
in the same slot as our enstrophy exponent is **`ρ`, not `α`**.

"Non-integrable" means non-integrable **in time, near the singularity**:

```lean
theorem rate_integrableOn_iff (ρ : ℝ) {T : ℝ} (hT : 0 < T) :
    IntegrableOn (fun x : ℝ => x ^ (-ρ)) (Ioo 0 T) ↔ ρ < 1
```

and the threshold theorem is:

```lean
/-- **The dyadic regularity threshold is an integrability threshold.** -/
theorem blowupRate_not_integrable_iff {a : ℝ} (ha : 0 < a) {T : ℝ} (hT : 0 < T) :
    ¬ IntegrableOn (fun x : ℝ => x ^ (-(rhoExp a))) (Ioo 0 T) ↔ 1 / 2 ≤ a
```

with the arithmetic half isolated in the file's single use of `1/2`:

```lean
theorem rhoExp_one_le_iff {a : ℝ} (ha : 0 < a) : 1 ≤ rhoExp a ↔ 1 / 2 ≤ a
```

Read carefully: **`α ≥ 1/2` ⟺ `ρ ≥ 1`.** The threshold in the temporal exponent is at `ρ = 1`,
and `α = 1/2` is merely the model parameter that produces it. The file's own non-vacuity example
makes this explicit:

```lean
/-- At `α = 1/2` the rate exponent is exactly `1`: the borderline case. -/
example : rhoExp (1 / 2 : ℝ) = 1 := by unfold rhoExp; norm_num
```

The file is also scrupulous about its own limits, and that scope note should be honoured by
anyone citing it:

> This is **not** a formalisation of Cheskidov's Theorem 4.4 … Claiming the theorem whole on the
> strength of this file would be exactly the D1-class overstatement the external audit of
> 2026-08-13 killed this programme's headline for.

## 2. `EnstrophyProductionBound.lean`

```
      S_N := Σ_{n=0}^{N-1} k_n³ a_n² a_{n+1}
      Ω_N := ½ Σ_{n=0}^{N} k_n² a_n²
      S_N² ≤ 2 · Ω_N³          under dyadic doubling  k_{n+1} = 2 k_n
```

`a_n` is the shell amplitude, `k_n` the shell wavenumber, `Ω_N` the enstrophy analogue, `S_N` the
production/flux. The result is sorry-free with standard axioms and carries negative controls
(it genuinely fails for `k_n = n+1` and `k_n = 1`).

Note this bound is **super-linear**: `S ≤ √2 · Ω^{3/2}` *permits* Riccati blowup. It is not an
enstrophy ceiling, and must not be cited as one.

## 3. The scaling dictionary

Our exponents (paper §4, `h = 1/200`), with `τ` the time to blow-up:

| quantity | scaling | exponent |
|---|---|---|
| core radius `ℓ_r` | `τ^{1/2}` | +0.5 |
| axial scale `ℓ_z` | `τ^{1/2−h}` | +0.495 |
| velocity `u` | `τ^{−1/2−h}` | −0.505 |
| vorticity `|ω| ~ u/ℓ_r` | `τ^{−1−h}` | −1.005 |
| core volume `V ~ ℓ_r² ℓ_z` | `τ^{3/2−h}` | +1.495 |
| **integrated enstrophy** `Ω = ∫|ω|²dx ~ |ω|²V` | `τ^{−1/2−3h}` | **−0.515** |

Dictionary used: `y = ‖u‖²` in Cheskidov's Riccati is the `H¹`-norm squared, i.e. the **enstrophy
analogue**, matching `Ω_N`. So the comparable pair is

```
    Cheskidov/Lean:   Ω ~ (t*−t)^{−ρ(α)}
    Ours:             Ω ~ τ^{−(1/2+3h)}
```

giving an **implied dissipation index** `α = 1/(3 − ρ)`:

| | `ρ` | implied `α` |
|---|---|---|
| our construction, `h = 1/200` | `103/200 = 0.515` | `200/497 ≈ 0.4024` |
| our construction, `h → 0` | `1/2` | `2/5` exactly |
| the Lean threshold | `1` | `1/2` |

**Assumptions this requires**, all of which are real limitations: (i) that a one-scale shell model
is comparable to a two-scale anisotropic construction with `ℓ_r ≠ ℓ_z`; (ii) that `‖u‖²` in the
bilinear estimate corresponds to integrated enstrophy in the same normalisation; (iii) that
Cheskidov's α ↔ NSE correspondence, which is itself heuristic in the source, transfers.

## 4. The verdict, and the thing worth keeping

**Literal question — coincidence.** Our `1/2` is a *temporal* enstrophy exponent `ρ`. The Lean
file's `1/2` is a *dissipation index* `α`. The threshold in the temporal variable is at `ρ = 1`,
and our `ρ ≈ 0.515` is nowhere near it. Reaching `ρ = 1` would require `h = 1/6 ≈ 0.167`, while
the construction requires `h < 1/100`. **The construction is confined to `α ∈ [0.400, 0.4024]`,
firmly inside the band where the Riccati argument is provably powerless** — which is exactly
consistent with a genuine blowup living there, and is the correct reading.

**The exact correspondence that did turn up.** In the Lean file:

```lean
/-- At `α = 2/5` — the case Cheskidov singles out as carrying the *same* enstrophy estimate as
3-D Navier–Stokes — the rate exponent is `1/2`, so the rate IS integrable and the argument
yields nothing. -/
example : rhoExp (2 / 5 : ℝ) = 1 / 2 := by unfold rhoExp; norm_num
```

`rhoExp(2/5) = 1/2` **exactly**, and our enstrophy exponent at `h → 0` is **exactly** `1/2`. The
`α = 2/5` value is not arbitrary: it is the one the source identifies as carrying the same
enstrophy estimate as 3D Navier–Stokes. At that `α`, `rExp = 6` and `sExp = 3`, i.e. the Riccati
is `Ω′ ≲ Ω³`, whose saturating rate is `Ω ~ τ^{−1/2}`.

So the reading with some claim to being structural is: **the OpenAI construction blows up at
precisely the rate that saturates the NSE-critical dyadic bilinear estimate**, and the anomalous
exponent `h > 0` is the small excess above that saturating rate. That is a genuine and checkable
statement about where the construction sits, and it explains the `1/2` in our own table as
something other than an accident of the ansatz.

## 5. What this does **not** show

- **It is not a proof of anything.** Two derivations producing `1/2` is a numerical agreement, not
  a theorem. Establishing it would require showing that the self-similar scaling and the
  post-Young Riccati chain are computing the same quantity — which the shell model's single length
  scale versus the construction's `ℓ_r ≠ ℓ_z` actively obstructs.
- **It does not transfer the Lean result to NSE.** `DyadicRiccati.lean` is about a shell model and
  says so at length. Nothing here imports OpenAI's definitions or touches a function space.
- **It is not the ESS marginality restated.** Those are independent. The `L³`/Escauriaza–Seregin–
  Šverák marginality is a knife-edge *at* `h = 0`: `‖u‖_{L³} ~ τ^{−4h/3}` diverges only because
  `h > 0`, and at `h = 0` ESS would forbid the blowup outright. The Riccati threshold is at
  `h = 1/6`, sixteen times outside the permitted range. `h → 0` is where the construction becomes
  *exactly* Riccati-critical but *fails* ESS; the two constraints pull in opposite directions,
  which is itself worth noting.
- **It does not support any "regularity certified in Lean" claim.** `S² ≤ 2Ω³` is super-linear and
  permits blowup (§2).

## 6. Suggested disposition

Worth one remark in the paper's discussion of `h`-marginality — the existing sentence "That the
construction sits so close to the critical Serrin threshold is itself informative" is the natural
home — phrased as an observation with the `h → 0` limit made explicit, and explicitly *not* as a
result about NSE. It should cite Cheskidov for `α = 2/5`, not the Lean file, since the Lean file
formalises the exponent algebra rather than the fluid statement.
