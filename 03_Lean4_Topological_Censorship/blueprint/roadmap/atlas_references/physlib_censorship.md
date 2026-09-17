---
declaration: theorem
origin: cited
statement: draft
proof: withdrawn
lean: PhysLib.NavierStokes.Censorship.physlib_master_censorship_theorem
---
# PhysLib Thermodynamic Censorship Master Theorem

> **Withdrawn (see `../../../../CHANGELOG.md`; status 2026-09-17, v5.5.0).** This page documents a *draft* from the
> project's earlier "thermodynamic censorship" framing, which has been withdrawn. It is not a verified result and
> must not be cited as one:
> - the Lean declaration lives in `src/drafts/`, outside the verified set;
> - `src/drafts/PhysLibThermodynamicCensorship.lean` declares a **custom axiom** (`physlib_admissible_non_vacuous`)
>   and has a `True` placeholder, so "formally rejected with zero `sorry`" overstates it; no `physlib` integration
>   was completed;
> - the argument rests on a **global enstrophy bound with a chosen constant** `Ω_max`, which the paper replaced by the
>   local, dimensionally derived bound `|∇u| ≲ c_s²/ν`; a "rejection" derived from an assumed bound is a restatement
>   of that assumption, not a physical result;
> - OpenAI's proof is correct and is not "rejected" by anything: the project's position is a physical *reading* of
>   a theorem about a mathematical model.
>
> What replaced it, verified with standard axioms only: `src/OpenAIAdmissibility.lean` (on OpenAI's own definitions,
> every candidate exceeds every velocity-gradient bound arbitrarily close to the singular time) and
> `src/BlowupRegimeMap.lean` (`Kn = Ma/Re`: which physical assumption a blow-up scenario violates first).

This theorem links the leanprover-community `physlib` physics library to our Navier-Stokes Epistemic Audit.

## Formal Theorem

```lean
theorem physlib_master_censorship_theorem
    (v : PhysLibVelocityField) (T_blowup : Time) (hT : 0 < T_blowup) (c_s : ℝ) (hc : 0 < c_s) (Ω_max : ℝ)
    (h_div : Tendsto (fun t => physLibGlobalEnstrophy v t) (𝓝[<] T_blowup) atTop) :
    ¬ PhysLibAdmissibleFluid v T_blowup c_s Ω_max
```

Under `physlib` fluid-dynamic abstractions (`PhysLibVelocityField`, `PhysLibAdmissibleFluid`), any enstrophy-divergent manufactured singularity was claimed to be formally rejected by the Lean 4 kernel with zero `sorry` keywords *(claim withdrawn — see the note above)*.
