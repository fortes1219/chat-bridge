---
layout: research
slideId: cover
locale: en
theme: default
routerMode: hash
colorSchema: light
aspectRatio: 16/9
fonts:
  provider: none
title: chat-bridge · Portfolio research
appearance: ink
composition: cover
---

# Which market news<br>matters to <span class="cover-accent">my holdings?</span>

<p class="lead">Ask about Taiwan and US markets, check the sources, and see how a proposed allocation change would affect your weights.</p>

---
layout: research
slideId: workflow
locale: en
---

# From one question to an allocation comparison

> What do recent rate decisions and AI spending mean for my positions in TSMC and 0050?

<div class="summary-grid">
<section><h2>Ask about your holdings</h2><p>The chat brings your current positions and rules into the question.</p></section>
<section><h2>Follow the evidence</h2><p>Open a citation to see the document, its date, and the passage retrieved.</p></section>
<section><h2>Review a proposal</h2><p>Ask for target weights when you need them. Inspect the changes and decide whether to apply them.</p></section>
</div>

---
layout: research
slideId: corpus
locale: en
---

# One event per file, with sources attached

<div class="case-grid">

<div>

<div class="display-stat"><span>71</span><p>market events in the original evaluation corpus</p></div>

<p class="caption">The sample import produced 316 sections.</p>
</div>

<div>

**Metadata** records the event date, tickers, categories, keywords, and sources.

**Sections** separate what happened, reported market impact, and affected assets.

**Market tables** provide closes and percentage moves. Reported explanations remain attributed.

</div>
</div>

---
layout: research
slideId: normalization
locale: en
---

# Make Taiwan market terms searchable

| Source wording | How the system handles it |
| --- | --- |
| NT$1774.18 億 | Write NT$177.418 billion and retain the precision. |
| 升息 1 碼 | Write 0.25 percentage points and retain the source's context. |
| 費半 | Also search for SOX and its full Chinese name. |
| 央行 | Keep the original. The question and sources identify the central bank. |

<p class="caption">Aliases group verified names for one entity. Ambiguous terms stay as written.</p>

---
layout: research
slideId: ingest
locale: en
composition: diagram
---

# A retrieved passage still points to its source

Keep Markdown and Word headings and PDF page labels. Skip unchanged files using SHA-256.

---
layout: research
slideId: hybrid
locale: en
composition: diagram
---

# Semantic matching and keyword search work together

Use bge-m3 and pgvector for meaning, and jieba and PostgreSQL for company names, tickers, and aliases. Standard search takes 20 candidates per path and combines their ranks with RRF.

---
layout: research
slideId: failure
locale: en
appearance: ink
composition: scene
---

# One question, six topics, no rate decisions

The question covered **rates, AI spending, TSMC, 0050, US tech indexes, and institutional views**.

All six competed for the same eight slots. None of the expected rate-policy evidence reached the answer.

---
layout: research
slideId: retrieval
locale: en
appearance: ink
composition: scene
---

# Let each subtopic find its own evidence

Keep the original top eight and fetch another 30. Search up to eight subtopics and take eight passages per subtopic.

**Deduplicate the merged results.** Each subquery keeps the evidence it found.

<p class="caption">Select Split queries to reveal the recovered rate-policy sources.</p>

---
layout: research
slideId: evaluation
locale: en
composition: diagram
---

# More evidence on held-out questions

The original held-out labels include 25 news targets and three market tables. This page counts evidence delivered to the model.

---
layout: research
slideId: tradeoffs
locale: en
composition: diagram
---

# What the retrieval experiments changed

The experiments compared total hits, recovery on the rate-policy case, and added latency.

---
layout: research
slideId: grounding
locale: en
---

# Retrieval and answer quality need separate checks

<div class="case-grid">

<div>

<div class="display-stat"><span>14</span><p>answers across seven questions and two CLIs</p></div>

</div>

<div>

**Check for omissions.** Ten answers covered every expected point. Four missed one item each, traceable to documents absent from retrieval.

**Check the figures.** About 200 values were checked against cited sources. No transcription errors were found. One answer reversed the order of two reporting periods.

</div>
</div>

---
layout: research
slideId: proposal
locale: en
---

# Preview the change before approval

1. The model proposes weights for existing assets and cites its sources.
2. The backend checks the 100% total, calculates the change in percentage points, and evaluates the rules.
3. The user confirms before target weights change.

---
layout: research
slideId: controls
locale: en
---

# The backend and the user control portfolio changes

<div class="summary-grid">
<section><h2>Input</h2><p>The CLI receives the question, retrieved passages, and portfolio context. The chat runner sets tool restrictions per CLI.</p></section>
<section><h2>Validation</h2><p>The backend provides sources, disclosure, and computed values. A malformed proposal can leave the text answer available.</p></section>
<section><h2>Approval</h2><p>The backend checks that the proposal is pending. Approval commits the target weights in a transaction.</p></section>
</div>

---
layout: research
slideId: operations
locale: en
composition: diagram
---

# Quotes and chat responses travel separately

Users sign into their own Claude Code or Codex. FinMind and exchange open data supplement Taiwan previous closes.

<p class="caption">oRPC and Zod check frontend contracts. TanStack Query manages server state.</p>

---
layout: research
slideId: delivery
locale: en
---

# How I made AI-assisted development reviewable

<div class="summary-grid">
<section><h2>Before coding</h2><p>Record requirements, the plan, dependency evidence, and acceptance criteria in Spec Kit.</p></section>
<section><h2>During implementation</h2><p>Use Claude Code hooks for enforceable checks, including blocking code edits when the specification is missing.</p></section>
<section><h2>Before handoff</h2><p>Run fixed regression and held-out questions, review samples, and let the maintainer decide what to commit.</p></section>
</div>

<p class="caption">Inputs, retrieved evidence, and answers are available for tracing a case.</p>

---
layout: research
slideId: limits
locale: en
---

# What to show in the demo

1. Ask a question about rates, AI spending, and your holdings.
2. Open the citations and check the evidence and its date.
3. Preview an allocation proposal, then approve or decline it.

<p class="caption">This is a local, single-user demo. The held-out set is small and some Chinese rate queries miss relevant documents. Date filters use the event date, and a file may include later prices.</p>

<code class="shortcut">uv run chat-bridge</code>
