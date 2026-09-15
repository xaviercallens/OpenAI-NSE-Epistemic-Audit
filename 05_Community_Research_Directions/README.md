# 🌐 Community Research Directions

Following the highly engaging discussion on `r/FluidMechanics` (30,000+ views), this section is dedicated to exploring the high-impact ideas, questions, and intuitions brought forward by the community. 

*Rendons à César ce qui appartient à César* — this work is driven by the collective curiosity of mathematicians, fluid dynamicists, and engineers. Thank you to everyone who contributed to the discussion, specifically `u/cowgod42`, `u/vibe0009`, `u/babainottawa`, `u/Little-Name9809`, and `u/brokebeany` for your sharp insights.

## Work Streams

### 1. The "Augmented Navier-Stokes" & Entropy Condition (Inspired by `u/cowgod42`)
Exploring the idea that 3D Navier-Stokes requires an augmented admissibility condition (similar to the Lax entropy condition for inviscid Burgers) to filter out unphysical weak solutions.
* [WorkStream 1 Folder](./WorkStream1_EntropyCondition) (Includes Lean 4 formalization and LaTeX proofs)

### 2. Deriving the Thermal Energy Equation (Inspired by `u/vibe0009` & `u/Little-Name9809`)
Addressing how viscous heating follows from the scalings: because the core keeps Re ≈ 1, $\Delta T = u^2/c_p$ — about 48 K at Ma 0.3 and 540 K at Ma 1 (boiling a few picoseconds before blow-up; a few hundred kelvins at most, not plasma).
* [WorkStream 2 Folder](./WorkStream2_ThermalEquation) (Includes Python visualizations and LaTeX derivation)

### 3. Pre-Singularity Journey & Turbulence (Inspired by `u/babainottawa`)
Analyzing the trajectory *before* incompressibility breaks ($Ma < 0.3$) to extract insights for Large Eddy Simulation (LES) and subgrid-scale stress models.
* [WorkStream 3 Folder](./WorkStream3_Turbulence) 

### 4. The Dual-Framework for AI PDE Verification
We introduce a "Dual-Framework" combining mathematical validity (Sobolev spaces) and physical validity (Mach, Knudsen and Eckert bounds — equivalently the local vorticity bound $|\omega| \lesssim c^2/\nu$). This framework lets researchers label AI-generated mathematical-physics results as theorems about a model versus statements about real fluids.
* **Guide**: See the [Physical Censorship Audit Skill](../autoform-bot/skills/physical-censorship/SKILL.md) (name kept for history) and the only Lean 4 file that compiles against OpenAI's own definitions without `sorry`: [`lean_formalization/Validity/ModelValidity.lean`](../../lean_formalization/Validity/ModelValidity.lean). The older `03_Lean4_Topological_Censorship` drafts are not verified physics (see `REVIEW_AND_NEW_DIRECTION.md` §2).

### 5. Positive Scientific Roadmap: Leveraging OpenAI's Formalization
We outline how the mathematical community can directly leverage OpenAI's Lean 4 Sobolev estimation libraries, Gevrey bounds, and multi-agent proof tactics for positive breakthroughs in sub-critical PDEs, CFD model certification, and physics-informed AI.
* **Document**: See [Positive Scientific Directions & Roadmap](./POSITIVE_FUTURE_DIRECTIONS.md)

---
*We invite further PRs, issues, and discussions. The gap between pure math and physical fluids is an open frontier!*
