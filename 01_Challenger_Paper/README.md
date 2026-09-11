# 01_Challenger_Paper

## Certified Publication & Theoretical Refutation
**The MechanicaFluidorum Program | Socrate AI Lab**  
*Non-Profit Research Organization (French Association Loi 1901 for Neuro-Symbolic Scientific AI)*

*   **Preprint (PDF):** `OpenAI_NSE_EpistemicAudit.pdf`
*   **Source (LaTeX):** `OpenAI_NSE_EpistemicAudit.tex`
*   **Verification Script:** `verify-physical-vacuity.sh` (Audits Lean 4 files for MMS residual and UV divergence)
*   **Audit Script:** `audit_openai.py` (Clones/locates pinned OpenAI repo and extracts lines)
*   **Reproduction Protocol:** `REPRODUCTION_PROTOCOL.md` (Step-by-step verification protocol)
*   **Zenodo Automated Retriever:** `zenodo_retriever.py` (NIST SHA-256 cryptographic verifier)

### Certified Zenodo Open-Science Archive

This publication and its verification assets are certified on Zenodo:
- **DOI:** [`10.5281/zenodo.22696718`](https://doi.org/10.5281/zenodo.22696718)
- **Record ID:** `22696718`
- **GitHub Repository:** [`github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit`](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit)

To cryptographically verify all local files against the certified SHA-256 manifest:
```bash
python3 zenodo_retriever.py --verify
```
