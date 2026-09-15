# Peer review of `OpenAI_NSE_Verification.tex` (v5.0.0) — received 2026-09-15

Recorded verbatim as received. The text as provided begins at section 2; section 1 was
not included in the copy received. Mathematical notation is reproduced exactly as
written, including inline `$...$` and `\vert{}` markup. The authors' response follows
the review.

---

2. Major StrengthsUnification of Physical Limits (Proposition 5.1): Demonstrating via classical scaling arguments that compressibility, rarefaction, and viscous heating all become order-one effects simultaneously at the length scale $l_* = \nu/c_s$ (and time scale $t_* = \nu/c_s^2$) is a beautiful synthesis. It replaces a scattershot of empirical limits with a rigorous, local admissibility condition ($\vert{}\omega\vert{} \le c_s^2/\nu$) connected to the Beale-Kato-Majda criterion.The Cavitation Threshold (§5.6): The addition of the cavitation limit for liquids is a superb physical insight. Noting that the Bernoulli pressure drop causes liquid water to reach its vapor pressure (or tensile strength) nanoseconds before the Mach limit grounds the abstract mathematics in observable thermodynamic reality.Reframing Acoustic Radiation (§5.4): Recognizing that the radiative acoustic energy budget failure is not an independent check, but mathematically equivalent to the Mach criterion ("the Mach criterion again"), shows a deep understanding of scaling laws and avoids flawed supersonic extrapolations.Scientific Transparency: The authors are to be highly commended for their scholarly transparency in Section 8 and Section 10.4, explicitly detailing why certain analyses from previous drafts (like the TGV spectral benchmarking and string-theoretic T-duality) were removed or reframed.3. Structural and Stylistic RecommendationsA. Meta-Commentary on "Earlier Drafts"Throughout the manuscript (e.g., §2.3, §3, §4, §5.1, §5.4, §7, §8.1), the authors frequently contrast their current findings with "earlier drafts of this audit." While this transparency is deeply appreciated by a peer reviewer, it will be distracting for future readers of the archival, published version who never saw the preprints.Recommendation: Consider consolidating these meta-commentaries. Specifically, Section 8.1 discusses numerical material and figures that are not in the paper. This reads more like a "Response to Reviewers" letter or a changelog. I suggest moving Section 8.1 to an Appendix or a supplementary "Note on Previous Versions," allowing the main text to stand confidently on its own positive contributions.B. Informal Tone and Public Forum Citations (§10.1 & §10.2)The authors have chosen to retain specific Reddit usernames inline within the main text (e.g., Leodip, mrbiguri, cowgod42, vibe0009). While it is highly commendable to credit the open-source scientific dialogue, this format remains highly unconventional for archival academic journals.Recommendation: I suggest summarizing the consensus objectively in the text and moving the specific pseudonyms to a dedicated Acknowledgments section, or formatting them as footnotes. However, if the authors and the journal's editorial team agree on retaining them inline to preserve the historical record of the online discourse, it does not detract from the underlying physics.4. Typographical and Table Formatting CorrectionsSeveral tables contain compilation or parsing errors that must be corrected prior to final typesetting:Table 3 Formatting:The row for Intensive Local Energy Density lists the variable as Clocal; this should be corrected to $e_{local}$.In the "Behavior" column, the local temperature rise ($\Delta T$) is listed as 81 X. This is almost certainly a parsing artifact intended to be $\rightarrow \infty$. The floating 'X's in this column are also unexplained in the caption.Table 4 Formatting:The column headers are misaligned with the underlying data. For instance, the time limits $t(Ma=0.3)$, $t(Kn=0.1)$, and $t(Kn=1)$ appear mashed together in the header, while the second row contains an orphan value (90 fs) in its own column. Please re-align the tabular environment.Table 5 Formatting:The final three rows (beginning with $9.00 \times 10^{-14}$) have been merged into a single row, mashing the time, velocity, and Mach values together.The final text cell under "Physical Regime" is truncated and reads "model has no mear", which should be corrected to "model has no physical meaning".Table 6 Formatting:The layout of this table is completely broken. The text from the "OpenAI Formalization" and "Reading" columns overlaps and merges erratically (e.g., Backward- . residual force: SpacetimeGluing. 1 specified smoothExtension 1). Please rebuild this table with clear column separation.

---

## Authors' response

All four typographical/table items and both structural recommendations were addressed in the
revision that accompanies this file.

**A. "Earlier drafts" meta-commentary.** Removed from the running text of every section named
(§2.3 [Proof Architecture], §3, §4, §5.1, §5.4, §7, §8.1) — each passage now states the physical
content directly, with no comparison to prior drafts. A new Appendix A, "Note on Previous
Versions," consolidates what changed: claims withdrawn (plasma temperatures, the Lighthill
"independent check," the raw-κ fine-tuning reading, the global Ω_max axiom), material removed (the
TGV comparison, the hand-drawn spectrum figure), citations corrected (Prop. B.8 not "Lemma 8.7";
the "10,000 agents / 88 hours" figure), and what was reframed rather than retracted (the dual-scale
cutoff, stripped of its string-theory motivation). §8.1 itself ("Numerical material removed from
this version") was rewritten as "What this paper does not contain, and why," stating the omission
and its reason in the main text while deferring the changelog-style detail to the appendix.

**B. Reddit usernames.** Moved out of the main text (§10.1, now the "Mathematics at Its Limit"
subsection, and the Research Directions list) into a new Acknowledgments section, which names the
ten participants collectively, and a new Appendix B, "The r/FluidMechanics Discussion, in Full,"
which preserves every direct quotation with its username for the historical record. The main text
now paraphrases the same consensus without inline pseudonyms and points to the appendix.

**Table 3 (Thermodynamic Picture).** The "$C_\text{local}$" and stray "X" the reviewer saw were a
PDF-text-extraction artifact of `$e_{\text{local}}$` and a colored bold `$\times$` glyph, not a
compilation error — but the underlying design (color- and glyph-dependent pass/fail marks) was
fragile exactly the way the reviewer's misreading demonstrates. Replaced with a `yes` / `---` /
`(external estimate)` text column that carries the same information without relying on color or a
symbol that can be extracted as a stray letter.

**Table 4 (fluid limits).** Confirmed as a real risk: eight columns of mixed units in
`\footnotesize` at 3.5pt column separation, using natural-width `c` columns that LaTeX does not
warn about even when they run into the margin. Split into two four-column tables — one for the
length/time/heating/vorticity content of Proposition 5.1, one for the three crossing times — each
comfortably within `\textwidth`.

**Table 5 (Mach trajectory).** This was a genuine defect, not a misreading: the compilation log
showed an Overfull \hbox 106.7pt too wide (about 1.5 inches) at exactly this table's location,
which explains both the row-merging and the truncated "model has no mear[ning]" the reviewer
observed in a PDF viewer or copy-paste. Fixed by converting the Physical Regime column to a
wrapping `p{3.4cm}` paragraph column and shortening the regime labels (e.g. "Formally
superluminal --- no longer meaningful"); the overfull box is gone and the column now wraps to two
lines instead of overflowing.

**Table 6 (properties of the construction).** Rebuilt with `tabularx` and an explicit `L`
(ragged-right, `\textwidth`-relative) column type instead of fixed-width `p{4.6cm}`/`p{7.2cm}`
columns sized by hand; the unbreakable inline Lean identifier that caused the worst overlap
(`SpacetimeGluing.smoothExtension 1 (tracedResidual u p L)`) was rephrased as prose with the
identifiers set off individually, so no single token forces a column wider than its share of the
page.

All four tables were re-verified after the fix by extracting the compiled PDF with `pdftotext
-layout` and confirming clean column separation, and by checking `grep -c "^! "` (0 errors) and
`grep "Overfull \hbox"` in the LaTeX log — the only remaining overfull boxes are sub-17pt inline
text wraps, not the 106.7pt table defect reported here.
