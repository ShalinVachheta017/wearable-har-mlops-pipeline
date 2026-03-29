# Archive Duplicate Action Plan

**Created:** 2026-03-06  
**Branch:** `chore/repo-cleanup`  
**Based on:** `ARCHIVE_DUPLICATES_REPORT.md` (506 PDFs scanned, 95 duplicate groups)

> **Safety guarantee:** this document defines rules and candidates only.
> No files have been deleted, moved, or renamed.

---

## 1. Canonical Rules (effective immediately)

| Location | Role | Action |
|----------|------|--------|
| `thesis/refs/papers_all/` | **Canonical thesis reading library** | Keep all, never delete |
| `archive/` | Historical / original source storage | Preserve as-is until Phase 2 |
| `archive/papers/papers needs to read/` | Temporary intake staging folder | Keep as staging bucket for now |
| `archive/papers/research_papers/76 papers/` | **Candidate canonical archive copy** | See Section 3 |
| `archive/research_papers/76 papers/` | Mirror of the above — redundant | Mark as candidate for later removal |

**Rule:** when a paper exists in both `archive/` and `thesis/refs/papers_all/`, the
`thesis/refs/papers_all/` copy is authoritative. The `archive/` copy is historical context only.

---

## 2. Bucket Classification

### Bucket A — Safe later-removal candidates (75 groups)

Definition: exact same SHA-256 hash, copy present in `thesis/refs/papers_all/`
(canonical location already has the file).

These 75 groups represent papers whose thesis-canonical copy already exists.
The extra archive copies are candidates for removal **in a future controlled phase**
after explicit human review.

**Pattern observed:**  
Most Bucket A copies live in these archive folders:
- `archive/papers/research_papers/76 papers/`
- `archive/research_papers/76 papers/`
- `archive/papers/papers needs to read/`
- `archive/misc_papers/`

**Do not delete yet.** Phase 2 will produce a proposal file listing each
`(keep path | remove path | reason)` row before any deletion occurs.

---

### Bucket B — Keep for now (20 groups)

Definition: exact duplicate exists only inside `archive/`, no copy in `thesis/`.

These papers have not yet been promoted to the canonical thesis library.
Removing any of them now would be premature.

| # | Hash (short) | Filenames | Paths | Size |
|---|--------------|-----------|-------|------|
| 1 | `228ed5f9` | `3380985 (1).pdf` = `3380985.pdf` | `archive/old_docs/paper_for_questions/` (×2) | 12.86 MB |
| 2 | `f83f0da7` | `3448112.pdf` = `SelfHAR.pdf` | `old_docs/paper_for_questions/` ↔ `old_docs/papers_jan25/` | 4.80 MB |
| 3 | `f224625f` | `sensors-21-01669-v2.pdf` (×2) | `old_docs/paper_for_questions/` ↔ `papers/new paper/` | 3.65 MB |
| 4 | `cb654a65` | `1706.04599v2 (1).pdf` = `1706.04599v2.pdf` | `papers/by_topic/evaluation_metrics/` (×2) | 1.29 MB |
| 5 | `87c71b92` | `Building-Scalable-MLOps-…pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 285.1 KB |
| 6 | `100fec3e` | `Demystifying MLOps….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 605.8 KB |
| 7 | `8928bb1e` | `Developing a Scalable MLOps….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 319.0 KB |
| 8 | `5db7ac08` | `Essential_MLOps_….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 2.97 MB |
| 9 | `acdff726` | `From_Development_to_Deployment_….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 1.31 MB |
| 10 | `cdcac11d` | `MLOps A Step Forward….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 1.00 MB |
| 11 | `417d8adb` | `MLOps and LLMOps….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 1.24 MB |
| 12 | `b5720603` | `Practical-mlops-….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 19.98 MB |
| 13 | `82f2facb` | `Research Roadmap_….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 143.7 KB |
| 14 | `8890d4b7` | `Resilience-aware MLOps….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 1.86 MB |
| 15 | `f7d08b85` | `Roadmap for a Scalable MLOps….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 113.6 KB |
| 16 | `0d01c8cb` | `The Role of MLOps in Healthcare….pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 442.9 KB |
| 17 | `c37a319e` | `Thesis_MLOps_FullPlan_with_GanttChart.pdf` (×2) | `by_topic/mlops_reproducibility/` ↔ `papers needs to read/` | 18.3 KB |
| 18 | `c03c52e6` | `preprints202601.0069.v1 (1).pdf` = `preprints202601.0069.v1.pdf` | `papers/new paper/` (×2) | 2.53 MB |
| 19 | `539ed987` | `Passive Sensing….pdf` = `Passive Sensing… Machine.pdf` (truncated name) | `papers needs to read/` (×2) | 2.03 MB |
| 20 | `fbe71988` | `Summarize papers and create file.pdf` (×2) | `papers/research_papers/` ↔ `research_papers/` | 42.3 KB |

**Observation:** Groups 5–17 are all in `by_topic/mlops_reproducibility/` and
`papers needs to read/` simultaneously — the file was sorted into a topic folder
but the original intake copy was not cleaned up. These are the natural first
consolidation candidates once the canonical archive folder is chosen.

---

### Bucket C — Manual review required (1 case)

Definition: same filename, **different** SHA-256 hash (different content).  
**Never auto-delete.**

| Filename | Variant | Hash (short) | Size | Location |
|----------|---------|--------------|------|----------|
| `1-s2.0-S1574119223000755-main.pdf` | A | `(see report)` | — | archive copy |
| `1-s2.0-S1574119223000755-main.pdf` | B | `(see report)` | — | thesis or archive copy |

**Action required:** manually open both PDFs, compare content, determine which
is the correct/complete version, then decide which path to keep.  
See full hashes and paths in `ARCHIVE_DUPLICATES_REPORT.md` → Section 3.

---

## 3. The 76-Papers Folder Decision

Two archive folders contain the same 76-paper set (exact mirrors):

```
archive/papers/research_papers/76 papers/    ← nested (deeper path)
archive/research_papers/76 papers/           ← flat (shallower path)
```

Additionally, **all 75 Bucket A cross-tree pairs** include at least one copy from
one of these two folders. Both folders are redundant relative to `thesis/refs/papers_all/`.

**Decision needed (choose one):**

- [ ] Keep `archive/research_papers/76 papers/` as the single canonical archive copy  
- [ ] Keep `archive/papers/research_papers/76 papers/` as the single canonical archive copy  
- [ ] Keep neither (thesis is canonical, archive copies are all redundant)

> Once a decision is made, document it here and proceed to Phase 2.

---

## 4. Phased Cleanup Plan

### Phase 1 — Decide canonical archive `76 papers/` folder *(next task)*

- Pick one of the two 76-papers folders as canonical historical archive.
- Record the decision in this file (checkbox above).
- Do not delete anything yet.

### Phase 2 — Generate proposal file *(after Phase 1)*

Run a scoped version of `find_duplicate_papers.py` that outputs a
**proposal-only** CSV with columns:

```
canonical_keep_path | duplicate_remove_path | hash | reason | bucket
```

No deletion occurs — this file is reviewed before anything is removed.

### Phase 3 — Controlled deletion commit *(after Phase 2 is reviewed)*

- Delete only files listed in the approved proposal.
- Commit as a single atomic commit titled `cleanup: remove approved archive duplicates`.
- Keep all Bucket B and Bucket C files untouched.
- Keep `archive/papers/papers needs to read/` as staging bucket until all
  papers in it have been reviewed and either promoted to `thesis/refs/papers_all/`
  or explicitly discarded.

---

## 5. What Must Never Be Auto-Deleted

- Any file in `thesis/refs/papers_all/` (canonical reading library)
- The Bucket C file (`1-s2.0-S1574119223000755-main.pdf`) in either location
- Any Bucket B paper until a canonical archive folder is confirmed
- The `papers needs to read/` intake folder contents until manually promoted

---

## 6. Summary of Today's Status

| Item | Status |
|------|--------|
| Duplicate scan complete | ✅ `ARCHIVE_DUPLICATES_REPORT.md` committed |
| Canonical rule defined | ✅ `thesis/refs/papers_all/` = canonical |
| Archive duplicates classified | ✅ Buckets A / B / C defined |
| 76-papers folder choice | ⏳ Pending decision |
| Proposal CSV generated | ⏳ Pending Phase 1 decision |
| Any file deleted | ✅ None (zero deletions today) |
