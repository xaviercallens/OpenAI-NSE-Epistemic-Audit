import Lake
open Lake DSL

package «nse-topological-censorship» {}

lean_lib «NSECensorship» {}

require mathlib from git "https://github.com/leanprover-community/mathlib4.git"

-- Importation directe du dépôt d'OpenAI pour l'audit épistémique
require NavierStokesAndEuler from git "https://github.com/openai/NavierStokesAndEuler" @ "main"
