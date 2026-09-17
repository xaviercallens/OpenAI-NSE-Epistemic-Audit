# 🌌 Projet : Audit Épistémique des Équations de Navier-Stokes par OpenAI
## 🛸 Section "Tout Public" & Citizen Science

> 🇺🇸 *"Artificial intelligence reveals the perfection of mathematics, but physics dictates reality."*
> 🇫🇷 *"L'intelligence artificielle révèle la perfection des mathématiques, mais c'est la physique qui dicte la réalité."*
> 🇨🇳 *"人工智能揭示了数学的完美，但物理学决定了现实。"*

![Neuro-Symbolic AI](assets/neuro_symbolic_brain_1789311430590.jpg)

> **Note (mise à jour v5.5.0, 2026-09-17) :** ce mémo a été corrigé lors de la révision générale du projet (v5.0.0), qui a abandonné le cadrage « vacuité physique »/« censure » ainsi que les prétentions liées à la théorie des cordes (T-dualité, K3×T²), après retours de la communauté et relecture scientifique, puis mis à jour avec les résultats de v5.4 et v5.5.0 (section « Où en est le projet ? »). v5.5.0 retire aussi l'idée qu'un filtre de Leray-α réglé sur $\ell_*$ représenterait le fluide à sa limite continue. Position actuelle : `01_Verification_Paper/OpenAI_NSE_Verification.pdf` ; liste complète des corrections, retraits et prévisions non confirmées : `CHANGELOG.md` ; version publiée : [v5.5.0](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/releases/tag/v5.5.0) ; DOI : [10.5281/zenodo.22696717](https://doi.org/10.5281/zenodo.22696717) (v5.5.0 : [10.5281/zenodo.22806767](https://doi.org/10.5281/zenodo.22806767)).
>
> *(EN) This memo was corrected at v5.0.0 and updated for v5.5.0. Earlier claims — plasma temperatures, a "censorship" principle, the condition-number figure read as physical fragility, the string-theory material, and (v5.5.0) the idea that a Leray-α filter tuned to $\ell_*$ represents the fluid at its continuum limit — have been corrected or withdrawn; see `CHANGELOG.md`.*
>
> *(中文) 本备忘录已在 v5.0.0 修订并更新至 v5.5.0。早期说法——等离子体温度、“审查”原理、把条件数解读为物理脆弱性、弦论相关内容，以及（v5.5.0）“把 Leray-α 滤波宽度设为 $\ell_*$ 即可代表连续介质极限处的流体”——均已更正或撤回，详见 `CHANGELOG.md`。*

### 🇫🇷 1. L'Héritage Français & Origine des Équations
Les équations de Navier-Stokes décrivent le mouvement de tous les fluides (eau, air, gaz) :
- 🇫🇷 **Claude-Louis Navier (1822)** : Illustre ingénieur français formé à l'*École Nationale des Ponts et Chaussées*, qui a introduit le premier les forces de frottement visqueux dans la dynamique des fluides.
- 🇬🇧 **George Gabriel Stokes (1845)** : Physicien anglo-irlandais qui a complété et formalisé les équations de transport de quantité de mouvement.

---

### ✈️ 2. Pourquoi Navier-Stokes Régit Notre Monde ?
- ✈️ **Aéronautique & Avions** : Calculer la portance des ailes ($C_L$), réduire la traînée ($C_D$) et garantir la sécurité des avions de ligne à Mach 0.85.
- 🌍 **Climat & Océans** : Modéliser la circulation atmosphérique, prévoir les ouragans et calculer le transport thermique des courants océaniques comme le Gulf Stream.

---

### ❓ 3. Le Problème du Prix du Millénaire & L'Annonce d'OpenAI
- En 2000, le *Clay Mathematics Institute* a classé la régularité de Navier-Stokes parmi les 7 **Problèmes du Prix du Millénaire** (1 million $).
- En septembre 2026, **OpenAI** a annoncé une preuve formalisée en Lean 4 (produite par un système multi-agents ; les chiffres circulant sur sa taille, « 10 000 agents », n'apparaissent dans aucune des deux publications techniques et ne sont donc pas repris ici) : un fluide peut développer une « singularité », c'est-à-dire une vitesse qui devient infinie en un point ($\vec{u} \to \infty$) alors que l'énergie totale reste bornée.
- **Notre lecture physique, en mots simples** : la preuve d'OpenAI est mathématiquement correcte, et l'énoncé du Clay autorise explicitement la force lisse qu'elle utilise. La question intéressante n'est donc pas « est-ce faux ? » mais « où le modèle continu cesse-t-il de décrire un vrai fluide ? ». Réponse : à *une seule* échelle. Comme le cœur du tourbillon garde un nombre de Reynolds d'ordre 1, sa taille suit $\ell_r \simeq \sqrt{\nu t}$ et sa vitesse $u \simeq \sqrt{\nu/t}$ ; les trois limites du modèle — compressibilité (Mach), raréfaction (Knudsen) et échauffement visqueux — deviennent importantes **ensemble** à $\ell_* = \nu/c_s$, soit $\approx 0{,}67$ nm dans l'eau et $\approx 45$ nm dans l'air. Cela arrive quelques picosecondes avant la singularité dans l'eau, quelques nanosecondes dans l'air, et *presque indépendamment de la taille initiale du tourbillon*.
- **L'échauffement** vaut exactement $\Delta T = u^2/c_p$ : environ 48 K à Mach 0,3 et 540 K à Mach 1. L'eau bout vers Mach 0,37, environ 4 ps avant la singularité — c'est chaud, ce n'est pas un plasma. Aucune loi de la thermodynamique n'est violée : c'est l'hypothèse de température découplée qui tombe.
- **Dans un liquide, la cavitation arrive en premier** : avec l'estimation usuelle de la dépression au cœur ($\tfrac12\rho u^2$), la pression de vapeur est atteinte dès $u \approx 14$ m/s, soit environ 5–6 ns avant la singularité, alors que le cœur mesure encore 70–80 nm — trois décades avant la limite de Mach. Pour un cœur gaussien, le coefficient exact est $1{,}70\,\rho u^2$, ce qui avance le seuil à $u \approx 7{,}6$ m/s (cœur ≈ 130 nm, ≈ 17 ns avant). (Même la résistance à la traction de l'eau, ~30 MPa, est atteinte vers 20 ps.)
- **Une seule condition d'admissibilité** résume tout cela : $|\omega| \lesssim c_s^2/\nu$ (soit $\approx 2{,}2 \times 10^{12}\ \mathrm{s^{-1}}$ dans l'eau), ce qui équivaut à Mach $\lesssim 1$ *et* Knudsen $\lesssim 1$. Avec cette borne, « rester admissible $\Rightarrow$ rester régulier » n'est pas un axiome mais le théorème de Beale–Kato–Majda.

---

### 🌪️ Singularity vs Turbulence / Singularité vs Turbulence / 奇点与湍流

<div align="center">
  <img src="assets/cyber_singularity_turbulence_1789311421687.jpg" alt="Cyberpunk Singularity" width="48%">
  <img src="../dataset/animations/pre_singularity_vortex.gif" alt="Vortex Core Contraction" width="48%">
</div>

**🇺🇸** In abstract mathematics, the velocity and the energy *density* concentrate without bound while the total energy stays bounded (as seen in the vortex contraction animation). This collapse is not turbulence: it is a single, forced, slowly-rotating core. In a real fluid the incompressible model stops applying before it ends — compressibility, heating and (in water) cavitation arrive first — and what happens next belongs to other physics, which the project has started to simulate.
**🇫🇷** Dans les mathématiques abstraites, la vitesse et la densité d'énergie se concentrent sans limite, l'énergie totale restant bornée. Cet effondrement n'est pas de la turbulence : c'est un seul cœur de tourbillon, entretenu par une force. Dans un fluide réel, le modèle incompressible cesse de s'appliquer avant la fin — compressibilité, échauffement et (dans l'eau) cavitation arrivent d'abord — et la suite relève d'une autre physique, que le projet a commencé à simuler.
**🇨🇳** 在抽象数学中，速度和能量密度无限集中，而总能量保持有界。这种坍缩并不是湍流，而是一个由外力维持的单一涡核。在真实流体中，不可压缩模型会在坍缩结束之前失效——可压缩性、粘性加热以及（在水中）空化会先出现——此后的过程属于其他物理，本项目已开始对其进行模拟。

---

### 🧠 Neuro-Symbolic AI: labelling theorems about models / L'IA Neuro-Symbolique : étiqueter les théorèmes / 神经符号人工智能：为模型定理加标注

![Neuro-symbolic gateway illustration](assets/thermo_censorship_portal_1789311439557.jpg)

**🇺🇸 Our Proposal:** proof assistants that handle physically motivated equations should carry an explicit *model-validity* layer, so that a kernel-checked result is labelled as a theorem about a model rather than a statement about fluids. The predicates are simple and dimensionally derived (Mach, Knudsen, Eckert, and the vorticity bound above). Such a layer should label, never block, a correct theorem, and a regularized solver is not a substitute for it: a Leray-α filter tuned to $\ell_*$ does not represent the fluid at that scale (the filter width does not even appear in the linearized dynamics). To be clear about status: in this repository one Lean file is stated on OpenAI's own definitions and proves, with no extra hypothesis, that their blow-up candidate must exceed every velocity-gradient bound near the singular time (in plain words: if the velocity blows up, so do its gradients). That is a first bridge; the validity layer inside a prover is still a proposal, not a built system.

**🇫🇷 Notre Proposition :** les assistants de preuve qui manipulent des équations issues de la physique devraient embarquer une couche explicite de *validité du modèle*, afin qu'un résultat vérifié par le noyau soit étiqueté comme un théorème *sur un modèle*, et non comme un énoncé sur les fluides. Les prédicats sont simples et obtenus par analyse dimensionnelle (Mach, Knudsen, Eckert, et la borne de vorticité ci-dessus). Une telle couche doit étiqueter, jamais bloquer, un théorème correct, et un solveur régularisé ne la remplace pas : un filtre de Leray-α réglé sur $\ell_*$ ne représente pas le fluide à cette échelle (la largeur du filtre n'apparaît même pas dans la dynamique linéarisée). Précision honnête : dans ce dépôt, un fichier Lean est énoncé sur les définitions mêmes d'OpenAI et démontre, sans hypothèse supplémentaire, que leur candidat dépasse toute borne sur le gradient de vitesse à l'approche de l'instant singulier (en clair : si la vitesse explose, ses gradients aussi). C'est un premier pont ; la couche de validité intégrée à un assistant de preuve reste une proposition, pas un système achevé.

**🇨🇳 我们的建议：** 处理物理方程的证明助手应当包含明确的**模型有效性**层，使经内核验证的结果被标注为关于某个模型的定理，而非关于真实流体的陈述。相关判据简单且可由量纲分析导出（马赫数、克努森数、埃克特数，以及上述涡量上界）。这样的有效性层只应加标注，绝不应阻挡正确的定理；正则化求解器也不能替代它：把 Leray-α 滤波宽度设为 $\ell_*$ 并不能代表该尺度下的流体（滤波宽度甚至不出现在线性化动力学中）。需要说明：本仓库中有一个 Lean 文件直接基于 OpenAI 自己的定义，在不附加任何假设的情况下证明：其爆破候选解在奇点时刻附近必然超出任何速度梯度上界（通俗地说：速度爆破必然伴随梯度爆破）。这只是第一座桥梁；集成在证明助手中的有效性层仍属提案。

---

### 🌐 Citizen Science / Science Citoyenne / 公民科学

![Citizen Science Terminal](assets/citizen_science_terminal_1789311449916.jpg)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/xaviercallens/OpenAI-NSE-Epistemic-Audit/blob/main/07_Tout_Public_Memo/Citizen_Science_Exploration.ipynb)

**🇺🇸 Experiment:** We created an interactive Google Colab Notebook (link above). Test our small numerical solver and understand physical limits yourself!
**🇫🇷 Expérimentez :** Nous avons créé un Notebook Colab interactif (lien ci-dessus). Testez notre petit solveur numérique !
**🇨🇳 实验：** 我们创建了一个交互式 Google Colab 笔记本（上方链接）。测试我们的小型数值求解器！

---

### 📌 Où en est le projet ? / Project status

- **Version publiée : v5.5.0** (17 septembre 2026) — [notes de version](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/releases/tag/v5.5.0). Depuis la révision scientifique complète de v5.0.0, chaque affirmation est soit dérivée, soit vérifiée contre les publications d'OpenAI et leur code Lean, soit explicitement étiquetée comme hypothèse. Les retraits — et les prévisions qui ne se sont pas confirmées — sont listés dans `CHANGELOG.md`. Chaque chiffre est régénéré automatiquement (`BENCHMARKS.md`).
- **Ce que v5.4 a testé : « les molécules arrêtent-elles le tourbillon ? »** Pour un gaz, l'échelle $\ell_*$ est le libre parcours moyen à une constante près ($\ell_*/\lambda = 0{,}67$ dans l'air). La théorie cinétique exacte (modèle BGK) montre qu'à ces échelles l'amortissement est *plus faible* que la viscosité et que le mode « fluide » cesse d'exister à $k\lambda = \sqrt{\pi/2}$. Une simulation cinétique non linéaire d'un effondrement entretenu **n'a montré aucun arrêt**. À $\ell_*$, la description fluide *se termine*, mais les molécules n'arrêtent pas le cœur.
- **Ce que v5.5.0 a testé : la compressibilité et la chaleur.** Une simulation compressible avec équation de l'énergie, entretenue par la même force : sur la route suivie par la construction d'OpenAI (nombre de Reynolds du cœur ≈ 1), **rien n'arrête le cœur avant $\ell_*$** (il est seulement ralenti de 14 à 25 % ; une prédiction d'arrêt que nous avions faite a échoué). En revanche, pour un effondrement « inertiel » à grand nombre de Reynolds (du type étudié par Terence Tao en 2016), l'air **ne suit plus la rotation au-delà d'un Mach local ≈ 0,70** : la chaleur et l'évacuation du cœur absorbent le travail de la force. C'est un verrou sur le nombre de Mach, pas sur la vitesse ni sur la taille, dans un modèle simplifié (1D), dont les équations ont elles-mêmes des singularités démontrées.
- **Une carte des régimes** : la relation $\mathrm{Kn}=\mathrm{Ma}/\mathrm{Re}$ (démontrée en Lean) montre que chaque scénario d'explosion rencontre une physique différente en premier — l'échelle moléculaire pour la construction d'OpenAI, la compressibilité pour un effondrement inertiel, la viscosité pour la récente preuve d'explosion d'Euler forcée à vitesse bornée.
- **Une idée retirée** : régler un filtre de Leray-α sur $\ell_*$ ne représente pas le fluide à sa limite continue (démontré en Lean : la largeur du filtre n'apparaît pas dans la dynamique linéarisée). La régularité globale de Leray-α reste un théorème — sur une autre équation.
- **Des prévisions démenties, publiées comme telles** : une simulation 96³ où nous attendions qu'une régularisation l'emporte sur le forçage (aucun des six calculs ; les cœurs ralentissent vers $1{,}2$–$1{,}5\sqrt{\alpha'}$, sans convergence), et la prédiction d'arrêt compressible ci-dessus.
- *(EN) v5.4 showed that molecular (kinetic) physics does not stop a driven collapse at the mean free path: the fluid description ends there, nothing more. v5.5.0 tested compressibility and heat: on OpenAI's route (core Reynolds number ≈ 1) nothing stops the core before $\ell_*$ (a prediction of ours failed); on a high-Reynolds inertial route air stops following the driven swirl at a local Mach number ≈ 0.70 — a lock on Mach number, not on velocity or size, in a simplified 1D model. The relation Kn = Ma/Re (proved in Lean) shows which physics each blow-up scenario meets first. The idea that a Leray-α filter tuned to $\ell_*$ represents the fluid at its continuum limit is withdrawn. All numbers are regenerated by `BENCHMARKS.md`.*
- *(中文) v5.4 表明：分子（动理学）物理并不能在平均自由程处阻止被驱动的坍缩——流体描述在那里终止，仅此而已。v5.5.0 检验了可压缩性与热效应：在 OpenAI 构造所走的路径上（涡核雷诺数约为 1），在 $\ell_*$ 之前没有任何机制使涡核停止（我们此前的一个预测未被证实）；在高雷诺数的惯性路径上，空气在局部马赫数约 0.70 处不再跟随被驱动的旋转——这是对马赫数的锁定，而非对速度或尺寸的限制，且仅在简化的一维模型中得到。关系式 Kn = Ma/Re（已在 Lean 中证明）说明了每种爆破情形首先遇到哪种物理。“把 Leray-α 滤波宽度设为 $\ell_*$ 即可代表连续介质极限处的流体”这一观点已撤回。所有数值均由 `BENCHMARKS.md` 重新生成。*
- **Relecture externe reçue le 15 septembre 2026** (texte intégral : `01_Verification_Paper/PEER_REVIEW_2026-09-15.md`). Le relecteur retient comme points forts l'unification des limites à l'échelle $\ell_*$ et la borne locale reliée au critère de Beale–Kato–Majda, le seuil de cavitation, la requalification de l'argument acoustique (qui n'est qu'une reformulation du critère de Mach), et la transparence sur les éléments retirés. Il demande des changements de présentation — commentaires sur les versions antérieures déplacés en annexe, pseudonymes de la communauté déplacés dans les remerciements, tableaux reconstruits : **ces révisions ont été faites en v5.1.0**.
- **Merci à la discussion r/FluidMechanics**, dont les objections ont directement façonné plusieurs sections du projet. / *Thanks to the r/FluidMechanics discussion, whose objections shaped several parts of this work.*
- Pour écrire au projet : [GitHub Discussions](https://github.com/xaviercallens/OpenAI-NSE-Epistemic-Audit/discussions). *(EN) To reach the project, use GitHub Discussions.*
