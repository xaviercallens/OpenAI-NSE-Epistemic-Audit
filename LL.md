# Lessons Learned (LL.md) — Comprehensive Field Feedback & Anti-Pattern Playbook

> **Status (2026-09-17, v5.5.0).** Lessons from the first public posts (Sept 2026). The phrases quoted as
> anti-patterns below ("physically vacuous", "censorship", "telemetry") are quoted *as mistakes*; none is a
> current claim of this project. Current position: [`README.md`](README.md) and [`CHANGELOG.md`](CHANGELOG.md).

> *"I do not know enough about the subject to pretend. I am a curious explorer asking simple questions, not an authority delivering an audit or distributing code."*

---

## 1. The Five Lethal Traps Identified from Real Community Reactions

### Trap 1: The "AI-Generated Spaghetti" Style (Fatal on Reddit)
* **What happened:** 
  * `u/_padla_`: *"À juger par ton style de conversation, tu utilises probablement de l'IA pour communiquer et tu n'es pas vraiment intéressé par la discussion."*
  * `u/Elementary_drWattson`: *"Pourquoi ça se lit comme des spaghettis trop verbeux avec une touche de prétentieux ? « A mené un audit dans la construction »... c'est quoi ce délire."*
* **The Lesson:** Online technical communities have zero tolerance for AI-generated cadence (overly polite, corporate bullet points, consultant jargon like *"Physical Verification"*, *"telemetry"*, *"syntactic purity"*). It immediately brands the poster as disingenuous or a bot.
* **The Rule:** Write like a real human. Short, conversational sentences. No corporate buzzwords. Plain language.

### Trap 2: The "Run My Code" Security Red Flag
* **What happened:**
  * `u/Wintervacht`: *"S'attendre à ce que les gens exécutent du code aléatoire trouvé sur Internet sans poser de questions.. Ton ordinateur aurait brûlé dans les années 90."*
* **The Lesson:** Asking strangers to pull GitHub repos and run arbitrary Python scripts triggers basic cybersecurity warnings.
* **The Rule:** Never tell people to *"reproduce the telemetry"* or *"run our scripts"*. Share the numbers or screenshots directly. Only provide a link if someone explicitly asks *"where can I see the code?"*.

### Trap 3: Pushing "Physics" on Pure Mathematicians
* **What happened:**
  * `u/how_tall_is_imhotep`: *"La preuve concerne les mathématiques. Que la solution puisse être réalisée physiquement n'est pas du tout pertinent."*
  * `u/Leodip` & `u/ClearlyCylindrical`: *"Le but du prix du millénaire n'était jamais de comprendre quoi que ce soit sur les fluides réels."*
* **The Lesson:** Arguing that a pure PDE proof is "physically vacuous" is a non-starter in mathematics forums. They already know Navier-Stokes is an idealized model.
* **The Rule:** Concede immediately. Never argue that the math is "useless because real water has molecules". Focus strictly on the mathematics of the breakdown or the pre-singularity trajectory.

### Trap 4: Karma Limits vs. Bans (r/math Reality Check)
* **What happened:**
  * AutoModerator removed the post automatically: *"Votre soumission a été supprimée parce que vous êtes nouveau sur /r/math et que vous n'avez pas suffisamment de karma communautaire."*
* **The Lesson:** You weren't banned by a human moderator—your account simply lacks the minimum community karma to post top-level threads in `r/math`, and unreviewed AI posts are strictly routed to the *[Fil sur l'IA en mathématiques]* megathread.
* **The Rule:** Build karma by participating in normal comment threads first. Use the weekly megathreads for AI discussions.

### Trap 5: Text Walls vs. Visual Demand
* **What happened:**
  * `u/RiseBasic9254`: *"Peux-tu faire une vidéo de son fonctionnement... des visualisations de l'erreur seraient probablement utiles..."*
* **The Lesson:** People do not want to read dense text walls; they want to see plots, trajectories, and animations.
* **The Rule:** A single clear plot (e.g. Mach number vs. time to singularity) is worth 10 paragraphs of text.

---

## 2. Terminology Blacklist & Replacements

| ❌ Banned (Sounds like AI / Arrogant) | ✅ Adopted (Human, Casual, Honest) |
| :--- | :--- |
| **"We conducted an Physical Verification"** | *"I was playing around with the equations..."* |
| **"Our team's telemetry proves..."** | *"I computed the numbers and got..."* |
| **"Syntactically flawless but physically vacuous"** | *"The math holds, but the numbers get wild..."* |
| **"Tautological Syringe / Manufactured Singularity"** | *"The fine-tuning required in Lemma 8.7"* |
| **"Pull our repo to reproduce"** | *(Say nothing about the repo unless asked)* |
| **"Reward hacking / Adversarial example"** | *"Curious edge-case in the definitions"* |

---

## 3. The New Action Protocol for Future Posts

1. **Length:** Max 3 to 5 short sentences per comment. Keep it conversational.
2. **Goal:** Ask a question, don't lecture. Learn, don't teach.
3. **Links:** ZERO links in the initial post or top comments.
4. **Media:** Prefer an image or graph over long explanations.
5. **Engagement:**
   * When someone agrees (e.g., `u/Little-Name9809`): Be brief, thankful, and say you'll look into it.
   * When someone challenges (e.g., `u/babainottawa`, `u/Dihedralman`): Agree with them immediately: *"100% agreed, good point."*
