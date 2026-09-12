# Lessons Learned (LL.md)

## Core Philosophy: Intellectual Modesty & The Inquirer's Stance

> *"I do not know enough about the subject to pretend. I am a curious explorer asking questions, not an authority delivering a verdict."*

---

### 1. Vocabulary & Tone: Banned vs. Adopted Terminology

To avoid being perceived as a fringe claimant, crackpot, or aggressive debunker, strictly eliminate pretentious or adversarial language from all public posts, communications, and agent prompts.

| ❌ Banned Pretentious Terms | ✅ Adopted Modest Terms |
| :--- | :--- |
| **"Proof" / "Counter-proof" / "Refutation"** | *"Preliminary numerical observation" / "Question on the scaling"* |
| **"Epistemic Audit" / "Epistemic Falsification"** | *"Curious exploration" / "Toy check of the parameters"* |
| **"Debunking" / "Exposing flaws"** | *"Trying to understand the boundary cases"* |
| **"Tautological Syringe" / "Adversarial Attack"** | *"Interesting mathematical artifact" / "Curious behavior"* |
| **"Our lab proved / demonstrated that..."** | *"I'm not from the field, but I was curious about..."* |

---

### 2. The "Wait for the Discussion" Protocol

Never push code, links, or conclusions onto a community. Let the conversation organically pull elements from you.

1. **Top-Level Posts (OP) Must Have Zero Links:**
   * Never include GitHub, Zenodo, preprints, or personal websites in the opening post.
   * A link in an OP immediately triggers spam filters and makes the post look like self-promotion.
2. **Start with a Modest, Genuine Question:**
   * Focus on a single technical curiosity or question rather than a broad manifesto.
   * *Example:* "I was reading about the moment-matching step in Lemma 8.7 and was curious: how do fluid dynamicists usually handle condition numbers this high in practice?"
3. **Offer Links Only When Explicitly Requested:**
   * Only share code or telemetry if another user asks: *"Do you have the code for that?"* or *"Where did you see those numbers?"*
   * *Response:* *"I ran a small mpmath script to check the matrix condition number; happy to share the GitHub link if anyone wants to check if I made an error in the implementation."*
4. **Bring Elements Step-by-Step:**
   * Do not dump an entire paper or 5-point thesis in one comment.
   * Share one observation at a time, in response to what the other person is actually discussing.

---

### 3. Handling Community Pushback & Feedback

* **Always Concede and Validate First:**
  * When a specialist points out that Navier-Stokes is an idealized continuum (e.g., Leodip, Dihedralman), agree immediately and wholeheartedly:
    > *"You are completely right, and that makes total sense. I'm not from the field, so I really appreciate you clarifying that distinction."*
* **Never Argue or Defend a "Thesis":**
  * You are not defending a thesis; you are having a conversation and learning from domain experts.
  * Turn disagreements into learning opportunities: *"That's a great point. How do people in the field usually think about that transition?"*
* **Spot the Gems (e.g., u/babainottawa):**
  * When someone offers a constructive perspective (e.g., *"the journey/trajectory before the breakdown is what's useful"*), latch onto that and explore it together.

---

### 4. Protecting Against Moderator Bans (r/math, r/Physics)

* **Why the r/math ban happened:**
  * Academic moderators see dozens of amateur "proofs" and "audits" of Millennium Prize problems every week.
  * Combining words like *"Audit of Millennium Prize"* + *GitHub links* + *Zenodo links* triggers automatic bans for crackpot/fringe math and self-promotion.
* **The Golden Rule for Academic Subs:**
  * Be a student, not a professor. Ask questions about specific equations. Let the community provide the answers.
