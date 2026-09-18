# Lessons Learned — what went wrong when this project first posted in public

> **Status (2026-09-18).** Rewritten. The previous version of this file was a playbook for
> managing how the project *appeared* rather than for how it should *behave*, and the section
> below on what was removed explains why that was a mistake. The phrases quoted as anti-patterns
> ("physically vacuous", "censorship", "telemetry") are quoted **as mistakes**; none is a current
> claim. Current position: [`README.md`](README.md) and [`CHANGELOG.md`](CHANGELOG.md).

---

## 0. The rule that replaces the old version of this file

**Disclose how the work was done, link the source, and let the work carry it.**

This project is AI-assisted throughout, its commit history is mixed human and agent, and its
subject is an AI-generated proof. Every one of those facts is interesting and none of them is
embarrassing. Concealing any of them would be, and concealment is also the thing most likely to
be noticed.

Anything that follows is subordinate to that rule. If a lesson below ever conflicts with it, the
rule wins.

---

## 1. What actually went wrong in the first public posts

### 1.1 Arguing that a pure mathematical proof is "physically vacuous"

The strongest and most immediate pushback. The objection came back in several forms and it was
correct every time: the proof is about mathematics, the Millennium problem was never about
understanding real fluids, and everyone in the room already knows Navier–Stokes is an idealised
model.

**The lesson.** Arguing that a correct PDE proof is useless because real water has molecules is a
non-starter, and it deserves to be. It also was not what the project had actually found.

**The rule.** A physical-validity layer **labels** a result as a theorem about a model. It does
not reject a correct proof. Where the mathematics is right, say so first and without hedging.
This is now the project's stated position and it is a better position than the one it replaced.

### 1.2 Asking strangers to run code

Telling people to clone a repository and run scripts to "reproduce the telemetry" triggers an
entirely reasonable security reflex.

**The rule.** Publish the numbers and the figures. Link the source so anyone can read it. Never
make reading the argument conditional on executing anything.

### 1.3 Writing that nobody wanted to read

Long, dense, jargon-heavy posts written in a register borrowed from consulting. "Physical
Verification", "telemetry", "syntactic purity". The style obscured the content, and where the
content was thin the style made that worse rather than better.

**The rule.** Write plainly because plain writing is clearer and because unclear writing hides
errors from its own author. That is the reason. Writing plainly in order to seem like a different
kind of author than you are is the mistake this file used to recommend.

### 1.4 A single figure beats a page of prose

Repeatedly asked for, and correct. A plot of Mach number against time to singularity carries more
than ten paragraphs.

**The rule.** Lead with the figure. Keep the prose for what a figure cannot say.

### 1.5 Community mechanics are not a verdict

An early submission was removed automatically for insufficient community karma, not by a human
judging the content. Unreviewed AI-related posts are routed to a dedicated megathread.

**The rule.** Read a venue's rules before posting in it. An automated removal is information about
the venue, not about the work.

### 1.6 Post where the argument belongs

The mathematical content belongs where mathematicians discuss formalisation, not on a general
forum where the first hundred readers have no way to check anything. Choose the venue by who can
falsify the claim.

---

## 2. What was removed from this file, and why

Recorded rather than deleted, because this project's rule is that corrections are written down.

The previous version contained:

- **A "Terminology Blacklist"** mapping accurate descriptions of the work to casual substitutes,
  so that "We conducted a Physical Verification" would be presented as "I was playing around with
  the equations". That is a table for misrepresenting how the work was done.
- **A rule of zero links in an initial post**, and an instruction to say nothing about the
  repository unless directly asked. Withholding the source is the opposite of what this project
  is for.
- **An instruction to agree immediately with anyone who challenged the work**, regardless of
  whether they were right. Conceding a correct point is honest. Conceding in advance as a policy
  is not, and it wastes the one thing a public thread is good for.
- **An adopted persona** of a curious explorer asking simple questions rather than someone
  presenting an audit. The project is an audit. Saying otherwise is a false statement about its
  own nature.
- **Named accounts of individual people**, quoted by handle. Their substantive points are kept
  above; their handles are not, because they did not post them here.

The common thread is that the file optimised for how the project would be received rather than
for whether it was right. In a project whose entire subject is the gap between a claim that looks
correct and a claim that is correct, that was the wrong instinct, and it is the sort of thing that
would fairly be read as bad faith by anyone who found it.

---

## 3. Before posting anything

- [ ] The claim being posted is currently standing, not one of the withdrawn items in
      `CHANGELOG.md`.
- [ ] The AI assistance is disclosed in the post itself, not only in the repository.
- [ ] The source is linked.
- [ ] Nothing asks the reader to run anything.
- [ ] Any number quoted is traceable to a committed artefact, and the artefact is committed.
- [ ] Where the mathematics under discussion is correct, the post says so explicitly.
