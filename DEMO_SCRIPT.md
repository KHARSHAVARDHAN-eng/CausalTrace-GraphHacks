# CausalTrace — 2–3 Minute Judge Demo Narration & Walkthrough Script

**Hackathon Track:** Agents That Act on Connected Data  
**Live Application URL:** [http://localhost:5173](http://localhost:5173)  
**Estimated Run Time:** 2 minutes 30 seconds  
**Speaker Stance:** Technical, objective, evidence-grounded Site Reliability Engineer.

---

## Preparation Checklist Before Recording
- [ ] Docker container `causaltrace-falkordb` is running (`docker start causaltrace-falkordb`).
- [ ] Backend is running on port 8000 (`uvicorn app.main:app --reload --port 8000` in `backend/`).
- [ ] Frontend Vite server is running on port 5173 (`npm run dev` in `frontend/`).
- [ ] Browser window sized to 1920x1080 or standard 16:9 full-screen at [http://localhost:5173](http://localhost:5173).
- [ ] Health badge in top navigation bar reads **"FalkorDB: Connected"** with low millisecond latency.

---

## Video Walkthrough Sequence

```
 ┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
 │ Part 1: Intro  │ ──> │ Part 2: Normal │ ──> │ Part 3: Duel   │ ──> │ Part 4: Safety │
 │ Problem Framing│     │ inc-01 (Top-1) │     │ inc-08 (Comp.) │     │ inc-07 (Abst.) │
 └────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
```

---

### Part 1: Introduction & Problem Statement [0:00 – 0:30]
**On-Screen Action:**
- Show the CausalTrace workbench home view at `http://localhost:5173`.
- Highlight the FalkorDB connectivity badge and the incident selection bar.

**Voiceover Narration:**
> *"When a high-severity incident strikes a distributed microservice architecture, Site Reliability Engineers face a wall of fragmented signals. An edge service like checkout starts throwing 500 errors and p99 latency spikes, while the underlying trigger could be a database pool exhaustion or a bad configuration change two, three, or four hops away.*
>
> *Relational tables and isolated log streams make traversing multi-hop dependency chains cumbersome during high-stress triage. We built **CausalTrace** for the Graph Hacks hackathon to model microservice topologies, deployments, alerts, and log events as a unified property graph in **FalkorDB**, using native Cypher to compute deterministic, evidence-corroborated root causes in milliseconds."*

---

### Part 2: Baseline Root-Cause Traversal (`inc-01-payment-pool-exhaustion`) [0:30 – 1:15]
**On-Screen Action:**
1. In the Incident dropdown, select **`inc-01-payment-pool-exhaustion`** (High 5xx error rate on checkout).
2. Point cursor to the **Incident Overview & Blast Radius**: Note `svc-checkout-web` affected, with 7 services in the blast radius.
3. Scroll to **Ranked Root-Cause Hypotheses**: Point out **`dep-payment-v2.4.1`** ranked **#1** with a **95.5% heuristic score**.
4. Click to expand the **Evidence Chain**: Show the 2-hop critical call path (`Checkout Web` ➔ `Order Orchestration` ➔ `Payment Processing Service`).
5. Point out the corroborating evidence: active alert `DbConnectionPoolExhaustion` (CRITICAL) and matching log trace `trc-checkout-881` (`PoolTimeoutException`).
6. Point to the **Evidence-Guided Next Diagnostic Check** card on the right column with status `RECOMMENDED (NOT EXECUTED)`.

**Voiceover Narration:**
> *"Here in scenario 1, our checkout web frontend is failing. Rather than treating every service as equally suspect, CausalTrace uses FalkorDB to traverse the dependency graph and temporal event horizon.*
>
> *Within 4 milliseconds of warm traversal, the engine isolates `dep-payment-v2.4.1` on the Payment Processing Service as the primary culprit with a 95.5% confidence score. It traces the exact 2-hop synchronous critical call chain, corroborates it with a critical connection pool exhaustion alert, and matches the distributed trace ID from application error logs.*
>
> *Notice on the right: CausalTrace synthesizes an **Evidence-Guided Next Diagnostic Check**, clearly marked as `RECOMMENDED (NOT EXECUTED)`. It advises engineers to inspect latency and connection pool saturation metrics before executing any remediation."*

---

### Part 3: Competing Hypotheses & Distractor Demotion (`inc-08-dual-competing-deployments`) [1:15 – 1:55]
**On-Screen Action:**
1. In the Incident dropdown (or filter bar), select **`inc-08-dual-competing-deployments`** (Checkout stalls with dual simultaneous fraud and tax deployments).
2. Point cursor to the two competing hypotheses listed:
   - **Hypothesis #1:** `dep-fraud-v2.1` on `Fraud Risk Evaluator` (Score 1.0, Relative Confidence 76.9%).
   - **Hypothesis #2:** `dep-tax-v1.9` on `Realtime Tax Engine` (Score 0.70, Relative Confidence 23.1%).
3. Point out the difference: Fraud evaluator is on a synchronous blocking RPC path with critical NullPointerException logs; tax engine is on a non-critical async path without error logs.
4. Highlight the **Evidence-Guided Next Diagnostic Check**: Read the discriminating value explaining how inspecting canary error metrics distinguishes the two simultaneous releases.

**Voiceover Narration:**
> *"Now let's examine a harder scenario: competing hypotheses. In scenario 8, two separate teams deployed code within the same 10-minute window before checkout stalled.*
>
> *Rather than guessing or surfacing only one arbitrary result, CausalTrace displays both competing explanations. It ranks the fraud evaluator deployment higher because it sits on a synchronous blocking RPC path and has matching runtime exception logs, whereas the tax engine deployment sits on a non-critical asynchronous branch.*
>
> *Crucially, the diagnostic recommendation explicitly describes its discriminating value: inspecting p99 RPC latency on the fraud evaluator against canary baselines to definitively confirm which release caused the stall."*

---

### Part 4: Safe Abstention Under Telemetry Gaps (`inc-07-insufficient-evidence-abstain`) [1:55 – 2:30]
**On-Screen Action:**
1. In the Incident dropdown, select **`inc-07-insufficient-evidence-abstain`** (Billing service latency spike with missing telemetry).
2. Point to the amber banner: **`INSUFFICIENT EVIDENCE DETECTED — ABSTENTION MODE`**.
3. Point to **0 Root-Cause Hypotheses**: Show that the engine outputs no candidate entities.
4. Point to the **Insufficient Evidence Flags**:
   - *Highest candidate score is below confidence threshold (< 0.60).*
   - *Telemetry gap: Zero error or fatal logs recorded across the blast radius.*
   - *Zero code deployment events detected within the investigation window.*
5. Highlight the targeted diagnostic check: Recommending a read-only audit of local application logs and change registries on the Billing Ledger API without claiming missing evidence proves guilt.

**Voiceover Narration:**
> *"In production, the most dangerous AI behavior is hallucinating confidence when data is missing. In scenario 7, a billing service suffered latency degradation, but telemetry was dropped and no recent deployments occurred.*
>
> *Instead of inventing a plausible-sounding culprit, CausalTrace enters **Safe Abstention Mode**. It produces zero candidate hypotheses and surfaces explicit epistemic uncertainty flags: confidence fell below our 0.60 threshold, zero error logs were captured, and no deployments were found.*
>
> *It then generates a targeted, read-only diagnostic recommendation guiding engineers to audit local logs and change records on the billing service without treating the observability gap as proof of failure."*

---

### Part 5: FalkorDB Architecture & Synthetic Benchmark Summary [2:30 – 2:50]
**On-Screen Action:**
1. Switch to terminal or show the benchmark output from `python backend/scripts/evaluate_investigation.py`.
2. Point to the 100% metrics across all 10 synthetic benchmark scenarios.
3. Conclude by showing the CausalTrace header.

**Voiceover Narration:**
> *"Under the hood, CausalTrace queries FalkorDB via native Cypher. Graph queries traverse up to 4 hops with warm traversals averaging around 4 milliseconds. In our reproducible 10-scenario synthetic benchmark, the engine achieves 100% Top-1 accuracy, 100% distractor demotion, and 100% safe abstention.*
>
> *CausalTrace delivers evidence-first, graph-native incident intelligence that SREs can trust when seconds count. Thank you."*

---

## Exact Recording Instructions on macOS (QuickTime Player)

If you are recording locally on Mac:
1. Open **QuickTime Player** (`Command + Space` -> type `QuickTime Player`).
2. Go to **File -> New Screen Recording**.
3. In the recording options toolbar at the bottom:
   - Select **Record Selected Portion** and drag across the browser window (or choose full screen).
   - Under **Options**, select your microphone (e.g. **MacBook Pro Microphone** or headset).
4. Make sure `http://localhost:5173` is loaded in your browser.
5. Click **Record**.
6. Follow the script above (aim for 2:15 to 2:45 total duration).
7. When finished, click the **Stop Recording** icon in the macOS menu bar (top right).
8. Save the file: **File -> Save...** -> name it `causaltrace-demo.mov` or `causaltrace-demo.mp4`.
9. Upload the video to **YouTube** (set visibility to **Unlisted** or **Public**) or to **Loom**.
10. Copy the shareable link and add it to `README.md` and `SUBMISSION.md`.
