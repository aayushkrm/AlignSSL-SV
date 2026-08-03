# Adversarial internal review — AlignSSL-SV

**Reviewer role:** simulated critical referee for *Bioinformatics* / *Briefings in Bioinformatics*.
**Date:** 2026-07-25
**Material reviewed:** `docs/AlignSSL_SV_manuscript.md`, the full codebase in this
repository, all per-seed result JSONs under `results/json/`, and the derived tables
under `results/`.
**Method:** every manuscript number was recomputed from the canonical per-seed JSONs
by `analysis/aggregate_all.py`; every comparative claim was subjected to the
hypothesis test it implies; and one control experiment was run to test the
benchmark itself.

---

## Recommendation

**Reject in present form** (as a methods paper). The manuscript is arithmetically
accurate, the pipeline is honestly built, and there is no data leakage. But the
central claim does not survive the control experiment a referee would demand
first, and the evaluation task is not the task the paper says it is.

The work is salvageable, and Section 5 below states how. What it cannot be is a
paper claiming that self-supervised pretraining yields a *useful* deletion caller.

---

## 1. Major — the benchmark is separable by a single hand-crafted feature

This is the finding that governs everything else.

`scripts/extract_tensors.py::build_items` centres positive windows on truth
deletions, and draws negatives **uniformly at random from the chromosome**,
rejecting a draw only if it overlaps or abuts a truth deletion:

```python
s = int(rng.integers(0, max(1, clen - span)))
if not any(s < de and s + span > ds for ds, de, _ in dels) and \
   not any(abs(s - ps) < span for ps, _ in pos_spans):
    items.append((chrom, s, win_width, bs, 0, 0, np.nan, np.nan, 0))
```

A uniformly-drawn genomic window does not look like a deletion. So the task the
paper measures is not "is this candidate a real deletion" but "is there a
coverage dip at this locus".

I ran the control (`scripts/classical_baseline_eval.py`): twelve hand-crafted
alignment features — depth profile shape, discordant-pair rate, soft-clip rate,
insert-size deviation, mapping quality — into logistic regression and a
gradient-boosted tree, on the **identical shards, split, label fractions and
seeds** as the deep arms.

| Labels | 1% | 5% | 10% | 25% | 50% | 100% |
|---|---|---|---|---|---|---|
| Classical GBT (12 features) | **0.894** | **0.917** | **0.924** | 0.931 | 0.937 | 0.939 |
| Classical logistic | 0.877 | 0.878 | 0.869 | 0.866 | 0.872 | 0.871 |
| AlignSSL (combined SSL) | 0.514 | 0.655 | 0.813 | 0.847 | 0.913 | 0.934 |
| AlignSSL (no pretraining) | 0.050 | 0.734 | 0.763 | 0.854 | 0.912 | 0.944 |
| DeepSV-style representation | 0.434 | 0.591 | 0.662 | 0.834 | 0.856 | 0.707 |

The 12-feature model **leads significantly where labels are scarce (1%, 5%) and matches the deep arms elsewhere** (Table 14; the earlier "every budget" claim is withdrawn)
under the fixed 0.5 cut used here, and at 1% of labels (210 windows) it exceeds
the best deep arm by 0.31 F1. Under the corrected, threshold-free comparison
(`results/table14_control_vs_deep.csv`) the control's lead is significant only
in the two label-scarce cells and *reverses* at full supervision — a weaker but
better-founded version of the same finding.

Worse, no training is needed at all. Single-feature discrimination on the
held-out test set (n = 9,196; 2,299 positive):

| Feature | ROC-AUC |
|---|---|
| centre-vs-flank depth ratio | **0.955** |
| soft-clip rate | 0.802 |
| discordant-pair rate | 0.732 |
| insert-size deviation (max) | 0.694 |
| depth s.d. | 0.686 |

**Consequence for the paper's thesis.** The headline result — pretrained F1 0.514
vs from-scratch 0.050 at 1% labels — is reproducible and statistically solid
*as a fixed-threshold measurement* (paired *t* = 13.27, *p* = 9.2 × 10⁻⁴). Its
interpretation collapses on two independent grounds. The first is the control
documented in this section. The second, found later and recorded in §8 below,
is that the measurement itself is threshold-dependent: under threshold-free
scoring the gap disappears entirely (AUPRC ratio 1.23, *p* = 0.35), so the
claim is **withdrawn** rather than merely reinterpreted.
It does not show that pretraining buys label efficiency for deletion calling. It
shows that a randomly-initialised CNN needs more than 210 labels to learn a
depth-ratio threshold, and pretraining supplies that inductive bias sooner. A
decision stump on one feature would have done better than both. The manuscript
currently sells this as the method's central contribution; a referee will find
the control in one afternoon and the paper will not recover.

**This is not a presentational fix.** The task must change.

---

## 2. Major — statistical claims are asserted without tests, and several are false

The manuscript reports mean ± s.d. across seeds and then uses
significance-flavoured language ("indistinguishable", "clearly best", "leads")
with no hypothesis test anywhere. I ran them; results are now in
`results/stats_tests.csv`. Verdicts:

| Manuscript claim | Test | Verdict |
|---|---|---|
| Low-label gain, combined vs scratch @1% | paired *t* = 13.27, *p* = 9.2e-04 | **Holds** (10.4×) |
| Same, MAM-only / VICReg-only @1% | Welch *p* = 1.7e-02 / 4.2e-05 | **Holds** |
| "Statistically indistinguishable at 100% labels" | paired *t* = −4.20, *p* = 0.025 | **False** — from-scratch is *higher* by 0.010, consistently, on every seed |
| Combined objective best at 100% (ablation) | Welch *p* = 0.209 | **Not significant** |
| MAM-only leads at 1% | Welch *p* = 0.477 | **Not significant** |
| Pretraining "nearly eliminates" the ancestry gap | significant at 1 of 6 fractions (*p* = 0.028 @10%) | **Overstated**, and the gap *inverts* — from-scratch has the smaller gap at 1% and 50% |

The ablation section ranks three objectives off means whose seed spreads overlap.
At n = 3–4 seeds those orderings are not established. Either raise the seed count
until they are, or report the ablation as "no separable difference detected".

---

## 3. Major — the calibration claim rests on one outlier seed

Table 2 quotes the DeepSV-representation baseline at ECE = 0.072 ± 0.068 against
AlignSSL's 0.0078, an order-of-magnitude gap. Per-seed values are
**0.0327, 0.1683, 0.0163** — median 0.0327. One seed carries the mean. The honest
statement is "roughly 4× on the median, with one unstable run at 20×", and the
instability of that arm is itself the more interesting observation.

Separately: AlignSSL-combined ECE 0.0078 ± 0.0017 vs from-scratch 0.0072 ± 0.0004.
Pretraining does **not** improve calibration here. Temperature scaling does the
work in both arms. The abstract implies otherwise.

---

## 4. Moderate

**4.1 Provenance — now verified, previously unverifiable.** The committed
aggregation script had drifted from the committed CSVs (different filenames and
schemas) and computed neither the calibration nor the length-stratified table.
The committed results were therefore not reproducible from committed code. Fixed:
`analysis/aggregate_all.py` is now the single source of truth, derives all five
tables plus the test table from `results/json/`, and hard-asserts the two
provenance invariants below.

**4.2 Error bars — verified sound.** Each seed of each pretrained arm genuinely
uses a distinct pretraining encoder (`encoder_ssl_seed{0..3}.pt` and the
per-objective ablation encoders), so the reported spread covers the whole
self-supervised pipeline, not fine-tuning noise. Fine-tuning batch size is 96 in
every arm. Both are now runtime assertions.

**4.3 Pretraining corpus size is understated** in Methods — a stale figure from
an earlier two-sample era. The corpus is 120,000 windows over 60 shards from
three samples.

**4.4 Cross-ancestry design is underpowered.** One held-out population (CEU),
three seeds, and an inversion in the middle of the label range cannot support a
claim about ancestry robustness. Either add held-out populations or drop the
claim to an observation.

**4.5 No external gold standard.** Evaluation is direct genotype concordance
against the 1000 Genomes phase-3 integrated SV callset, which is itself a
short-read consensus callset — not an orthogonal truth set. GIAB HG002 with
Truvari matching is the benchmark a referee expects. Deferred by decision; must
be named plainly in Limitations.

**4.6 Deletions only**, single coverage regime, no repeat/segmental-duplication
stratification. The length-stratified table shows recall falling from 0.91
(50–200 bp) to 0.63 (>5 kb), which is the honest and useful part of the results.

---

## 5. What the work actually is, and how to publish it

The engineering is sound and the negative results are informative. Three viable
routes, in order of preference:

**Route A — fix the task (best, and what I recommend).** Replace uniform negatives
with the false positives of a depth-based candidate generator: score a large pool
of non-truth windows by centre/flank depth ratio and keep the most
deletion-like. The classification problem becomes the one a caller actually
faces — "given a depth dip was proposed here, is it real?" — on which the
shortcut feature is, by construction, uninformative. `scripts/extract_tensors_hardneg.py`
implements this. **Blocker:** the beegfs dataset workspace holding the reference
FASTA, truth VCF, and five of six panel BAMs has been deleted from the cluster;
only NA12878 and NA20845 survive. Full re-extraction is not currently possible.
A partial version — reselecting the hardest negatives from the *existing*
tensors — is possible and is being measured.

**Route B — publish it as a negative/benchmarking result.** "Hand-crafted
alignment features match deep representation learning on random-negative deletion
benchmarks" is a genuinely useful contribution, because the random-negative
protocol is common in this literature and this paper would be the one that
measured it. Retitle, lead with the control, keep the SSL arms as the deep
comparators. This is publishable with the data in hand and does not require the
lost BAMs.

**Route C — narrow to a representation-learning study.** Drop all caller
language, present the label-efficiency curve as evidence about optimisation and
inductive bias, and state up front that the task is separable so the numbers are
not caller performance. Weakest of the three, but honest.

**Not acceptable:** submitting the present framing. The control is too easy to
reproduce.

---

## 6. Required corrections to the manuscript (blocking)

1. Add the classical control as a first-class arm in Table 1 and as Figure 2;
   state the single-feature ROC-AUC of 0.955 in the Results, not a footnote.
2. Delete "statistically indistinguishable at full supervision" — the paired test
   contradicts it; from-scratch is significantly higher.
3. Requalify all ablation rankings as not significant at the available seed count.
4. Report DeepSV ECE as median with the outlier named; remove the implication that
   pretraining improves calibration.
5. Requalify the ancestry claim to the one fraction where it is significant, and
   disclose the inversion at 1% and 50%.
6. Correct the pretraining corpus size to 120,000 windows / three samples.
7. Rewrite Abstract and contributions to match items 1–6.
8. State in Limitations: random-negative protocol, no orthogonal truth set,
   deletions only, single coverage regime, one held-out population.
9. Describe the negative-sampling procedure explicitly in Methods. Its absence is
   what let the shortcut go unnoticed.

---

## 7. What holds up

Worth stating plainly, because it is the part that survives adversarial review:

- No chromosomal leakage. Pretraining shards contain chr1–11 only; test is
  chr12–22; verified from the stored `chrom` field, exact counts summing to 120,000.
- Identical test set across all arms; harmonized fine-tuning batch size; distinct
  pretraining encoder per seed.
- Every manuscript table reconciles exactly with the per-seed JSONs.
- The low-label gap between pretrained and from-scratch is real and significant
  *at a fixed 0.5 decision threshold*. Section 8 revises this bullet: under
  threshold-free scoring the gap largely dissolves, and the fixed-threshold
  framing is no longer defensible.
- The length-stratified recall breakdown is honest and is the most scientifically
  useful table in the paper.
- The 1% cross-population and calibration analyses were run and reported even
  where they did not favour the method.

The pipeline is trustworthy. The benchmark it runs on is not hard enough to
support the claims made from it.

---

## 8. Evaluation-protocol audit (second pass)

The first pass audited *what the numbers claim*. This pass audited *how the
numbers were produced*, and found four defects in the shared evaluation path.
Two are arithmetic and were silent; the third invalidates the paper's headline
framing; the fourth (§8.6) shows that even under the framing that produces the
headline, its significance does not survive correction for the sweep it was
selected from. All four are fixed in code, with regression tests that encode
the defect rather than only the corrected behaviour.

### 8.1 The decision threshold was fixed at 0.5 for every arm

Every reported F1 was computed as `logits.argmax(1)`, i.e. a fixed 0.5
probability cut, with no threshold selection anywhere in the pipeline. For a
class-imbalanced task evaluated on models trained on as few as tens of labels,
this conflates two entirely different properties: how well a model *ranks* the
test set, and where its sigmoid happens to sit.

`analysis/threshold_confound.py` isolates the mechanism. Holding the ranking
signal exactly constant and moving only the sigmoid offset gives two models
with AUPRC identical to machine precision (0.658861) and best-threshold F1
within 0.001 of each other, yet F1 at the fixed cut differing by 0.198.

The first recomputed cell has exactly this shape. Uniform benchmark, 1% labels:

| arm | F1@tau | F1@0.5 | AUPRC |
|---|---|---|---|
| AlignSSL-pretrained | 0.456 | 0.362 | 0.463 |
| AlignSSL-scratch | 0.451 | **0.035** | **0.484** |

The from-scratch model's AUPRC is *higher*. It ranks the test set at least as
well as the pretrained model and collapses only at the fixed cut, because it
places nearly every probability below 0.5. The manuscript's description of it
as a model that "all but collapses" and "barely learns to fire" is therefore
not a statement about learned representation quality; it is a statement about
sigmoid placement.

This is the paper's central claim. It appears in the Abstract, the
contributions list, Section 4.1, Table 1, Figure 1, Section 5, Section 6.1 and
the novelty statement — eight places, all resting on the same fixed-threshold
comparison.

**Fix.** `alignssl/metrics.py` now scores every arm threshold-free (AUPRC,
ROC-AUC) *and* at a threshold selected on a held-out validation split, never on
test. The legacy `F1` key is preserved as an alias for F1@0.5 so old
aggregation still runs, but it is no longer the headline number.

### 8.2 The label budget was not the same for every arm

The deep evaluators floored the labelled-subset size at the training batch size
(`max(batch_size, int(frac * n_pool))`); the classical control did not
(`int(frac * n_pool)`). On the uniform benchmark (n = 21,016) the floor never
binds and the two rules agree at every fraction, so the defect was invisible
there. On the candidate-filtered benchmark (n = 3,452) the 1% fraction is 34
labels, below the batch size of 96 — so the deep arms silently received 2.8x
the labels of the control they were plotted against, in precisely the cell
carrying the low-label claim. The inflated count is printed in the published
Table 7's own `n` column, which reads 96 at 1%.

### 8.3 The validation split was gated on batch size

The split used to select a decision threshold was carved only when the subset
exceeded a batch-size-derived minimum. On the filtered benchmark no split was
carved below a mid-range fraction, so the low-label cells silently fell back to
the fixed 0.5 cut — the same cells as 8.2, and the same cells as the headline
claim.

The batch-size floor in 8.2 was not gratuitous: the training loader discards
incomplete batches, so removing the floor naively yields *zero* batches on a
subset smaller than one batch, and the low-label cells would train on nothing.
Defects 8.2 and 8.3 are one root cause: batch size, an implementation detail,
had leaked into the experimental protocol.

**Fix.** `alignssl/protocol.py` now owns the budget rule, the split rule and
the loader-parameter rule, and is imported by all three evaluators, so budget
parity holds by construction rather than by three copies agreeing. The budget
honours the true fraction and the loader adapts to it — the batch shrinks to
the subset rather than the subset inflating to suit the batch — and incomplete
batches are discarded only when the dropped tail is a small share of the data.
The split gate is now a small absolute minimum per side, independent of batch
size. Each output row records its effective loader configuration so the
protocol is auditable from the results files, not only from the code.

### 8.4 Consequences

Every deep-arm number in the paper is being recomputed. The uniform benchmark
is affected by 8.1 and 8.3 (not 8.2, which does not bind there); the filtered
benchmark by all three. The classical control is affected by 8.1 only.

The likely outcome, on the evidence available so far, is that the paper's
positive claim weakens substantially and its critical contribution strengthens.
If the pretrained-versus-scratch gap is a calibration effect rather than a
discrimination effect, the honest claim is narrower and more interesting than
the one currently made: *self-supervised initialisation places a low-label
model's decision boundary usefully, but does not measurably improve how well
that model ranks candidate deletions* — on a benchmark whose negatives a single
untrained depth ratio already separates at ROC-AUC 0.955.

That is a paper about how easily label-efficiency claims in this area can be
manufactured by an unstated thresholding convention. It is a less flattering
result than the one originally written, and a more useful one.

### 8.5 Regression tests

- `tests/test_metrics.py` (9 guards) — asserts that a model ranking the test
  set perfectly with all scores below 0.5 records AUPRC 1.0, F1@0.5 = 0 and
  F1@tau = 1.0; that tau is selected on validation and never on test; that
  legacy keys keep their old meaning; and the one-class and empty cases.
- `tests/test_protocol.py` (11 guards) — asserts that the two historical budget
  rules genuinely disagree at the broken cell, that the shared rule matches the
  classical rule at every fraction on both benchmarks, that the loader never
  yields zero batches across a swept range of subset sizes, and traces the
  broken cell end to end.
- `tests/test_shard_schema.py` — static guard that both extractors write the
  exact field set the shared loader reads.

All run under pytest or as plain scripts, because the cluster environment has
no pytest. Every cluster job now gates on them before training, so a
recurrence fails in seconds rather than after GPU-hours. Full suite: 35 passed.

### 8.6 No significance claim was corrected for multiplicity

Every *p*-value in the manuscript is drawn from a sweep — six label budgets
per contrast, two scoring rules on the candidate-filtered benchmark — and was
reported one test at a time. In a family of six simultaneous tests at
α = 0.05 the probability of at least one false positive is
1 − 0.95⁶ ≈ 0.26, which is roughly the strength of evidence the headline
claim rested on.

`analysis/apply_multiplicity.py` declares one family per sweep per contrast
per scoring rule and applies Holm–Bonferroni (family-wise error) and
Benjamini–Hochberg (false discovery). The table it writes,
`results/stats_multiplicity.csv`, already existed and the manuscript never
cited it; worse, it was stale — its candidate-filtered families were read
from `stats_hardneg.csv`, which predates the equal-budget and
budgeted-threshold corrections, and whose p-values disagree sharply with the
corrected `table15_hardneg_arm_contrasts.csv` (0.016 versus 0.666/0.058 at
the 1% budget). Correcting a stale p-value for multiplicity produces a stale
verdict, so `build_families` now prefers the corrected sources and retains
the pre-correction families under explicit labels, because Sections 4.5 and
4.6 are themselves reported under that protocol and quote those values.

Regenerated: 67 tests in 11 families, 20 nominally significant, 16 surviving
BH, 10 surviving Holm. Three consequences:

- The headline claim fails a second time. Its *p* = 0.009 becomes Holm
  *p* = 0.055 against the five other budgets it was selected from.
- The cross-ancestry claim is withdrawn outright, not merely hedged: its one
  nominally significant fraction is what a family of six yields by chance
  (Holm *p* = 0.169).
- The corrections' own strongest findings survive: both deep arms beat the
  DeepSV representation on the repaired benchmark at the largest budgets
  (Holm *p* = 0.005–0.049), and no pretrained-versus-scratch contrast
  survives anywhere — consistent with §6.3's conclusion that the two are
  tied there.

One disclosure. This is the single claim whose verdict depends on family
assignment: grouped with the objective-ablation contrasts it survives Holm at
0.005, grouped with its own budget sweep it does not (0.055). Section 4.9
reports both and argues for the sweep on selection grounds rather than on
which answer it gives — a claim must be corrected against the comparisons
that could have produced it, not against a neighbouring set of different
questions.

A caveat on the correction itself: Holm and BH assume exchangeability within
a family, whereas budgets in a sweep share seeds, encoders and test windows
and are positively dependent. Both remain valid under positive dependence
(BH provably, Holm conservatively), so the adjusted values are conservative
bounds, not exact — stated in Limitations.

### 8.7 A counted claim drifted from its own table

Section 4.6's prose said the pretrained arm's held-out CEU F1 exceeds the
from-scratch arm's "at four of six fractions". `table5_cross_ancestry.csv`
shows five of six — only the 50% fraction inverts, which the same sentence
already called out. A hand-counted claim sitting beside the table that
refutes it is the first thing a referee checks, so the count is now
recomputed from the CSV by `check_manuscript.check_cross_ancestry_count`,
which requires the manuscript to state the number in words. Verified in both
directions: it passes on the corrected text and fails with the reverted
count.
