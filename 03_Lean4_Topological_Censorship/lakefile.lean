import Lake
open Lake DSL

package «nse-topological-censorship» {}

lean_lib «NSECensorship» {}

require mathlib from git "https://github.com/leanprover-community/mathlib4.git"

-- Direct import of the OpenAI repository for epistemic audit
require NavierStokesAndEuler from git "https://github.com/openai/NavierStokesAndEuler" @ "main"
