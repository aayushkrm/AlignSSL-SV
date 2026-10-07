# Error-twin analytical kill test

Date: October 7, 2026. A paper-and-equation control, not biological data,
a new algorithm or a publication contribution. Main reread the full objective
and clean checkpoint `f1984f136ceee70e6c6c4d00f5b935ff5dbc2228` before continuing.
The previous goal turn made verified progress by stopping the fixed screen
and preserving its failure. Historical charge **8,588,703,005 bytes** remains;
this analytical calculation opens no genomic source or cluster job.

## Completed high-impact decision

Dalton (Sol6.1/max requested) recommends no publication lead yet. Main accepts
these decisions, not just a relative ranking:

| Candidate | Decision | Evidence required to reconsider |
|---|---|---|
| A: paralog copy-state identifiability | Reject current framing. ctyper already addresses unique-k-mer ambiguity, allele grouping and held-out haplotypes. | A consequential distinct mechanism beyond those controls; orthogonally resolved copy states with test donors excluded from the panel |
| B: selective risk under missing truth/assay transfer | Not selected. A useful target is specific-genotype error among retained target-assay calls, with retention/population reported. | Probability-sampled orthogonal adjudication including difficult, previously unlabeled retained calls |
| C: rare specific allele versus near-identical background | ONE ≤10-minute analytical kill test only; no acquisition or caller execution | A distinct useful decision beyond ordinary competing-haplotype likelihood, with independently testable artifact constraints and exact A-only/known-B-positive labels |

The corrected ctyper article is strong prior art, not our replication.
[Primary method](https://www.nature.com/articles/s41588-025-02346-4).
MIMS already separates hard/easy allele targets and studies support/depth;
neither is a new contribution here.
[First-party benchmark](https://github.com/BCM-HGSC/SMaHT_MIMS).
No absent selective-risk method is inferred from the short ContextSV/Dual-SVF
excerpts. Their completed [full-main-XML audit](2026-10-07-filtering-prior-art-methods.md)
finds empirical scoring/filtering, not a validated selective error bound in
the main articles. Supplements and code remain unread. This bounded finding
does not establish a novel research gap or supply representative labels.

For B, let `m` be the unlabeled fraction among retained target calls and
`r_L` the labeled-subset error. Without further restrictions the overall
risk is `(1-m)*r_L + m*r_U`, where unknown `r_U` can lie anywhere in [0,1].
Thus the identified interval is `[(1-m)*r_L, (1-m)*r_L+m]`. This is a sharp
identified interval for given `m` and `r_L`, not a statistical confidence
interval for estimates from a sample. This elementary
missing-label bound is not a new result; a generic calibration/conformal
wrapper cannot shrink it without additional assumptions or labels.

## Exact toy hypotheses and observed laws

A and B share the SV structure. Only diagnostic bases differ. Use a **binary**
symmetric flip channel, not a claimed physical nucleotide error model. Reads
cover the diagnostic bases; under **all three cases reads are independent**.
In the correlated A-only case, dependence is between bases within a read,
not between reads. This is an existence counterexample, not measured sequencing
artifacts or an estimated nuisance-error range.

With mixture fraction `f=1/100` and flip probability `e=1/100`, the observed
B base has probability `(1-f)*e + f*(1-e) = 99/5000 = 0.0198`.
An A-only process with flip probability `e'=99/5000` has exactly that law.
No read count can identify B from this one-base observation when both nuisance
models are permitted. Shared SV-support evidence adds no diagnostic distinction
in this toy, because the common SV structure is held identical.

For two linked bases, the joint states and **exact probabilities** are:

| Observed pair | A only; independent flips `e'` | 1% B mixture; independent flips `e` | A only; allowed correlated artifacts |
|---|---:|---:|---:|
| AA | 0.96079204 | 0.9703 | 0.9703 |
| AB | 0.01940796 | 0.0099 | 0.0099 |
| BA | 0.01940796 | 0.0099 | 0.0099 |
| BB | 0.00039204 | 0.0099 | 0.0099 |

Every column sums to one. Both bases in the last column have marginal flip
probability 0.0198. It is a valid correlated A-only channel with the **complete
same joint law** as the mixture, not merely the same double-error count.
Independence across reads gives equal full-sample laws at every fixed depth.
The correlated channel is constructed as a permissible counterexample; it
was not independently measured or shown realistic for sequencing.

Under the restricted independent models, an ordinary competing-haplotype
likelihood has KL divergence **0.028192878792330765 nats per read** (mixture
versus A-only). Positive KL establishes distinguishability under these
assumptions, not perfect finite-depth accuracy or a learned-method advantage.
For illustration only, at fixed N=1,000 and at least four BB observations,
the exact binomial probabilities are about **0.00071733** for independent
A-only and **0.98915592** for the mixture. The correlated A-only process has
the latter probability too. This is a toy count test, not the full likelihood
test, a tuned threshold, an SV performance metric or a recommended rule.

## Execution, reproducibility and scientific disposition

Main executed a standard-library Python calculation locally in 0.0047s.
`fractions.Fraction` verifies exact law equality, all state sums and marginals;
`math.log` gives the KL and `math.comb` the illustrative binomial tails.
No simulation, data download, installations, caller run or scientific source
read. Exact rational values and numerical outputs are retained in
`results/analytic_controls/2026-10-07/error_twin.json`.

Reproduce the core calculation with ordinary Python:

```python
from fractions import Fraction as F
from math import comb, log
f, e, t = F(1,100), F(1,100), F(99,5000)
a = ((1-t)**2, t*(1-t), t*(1-t), t**2)
b = ((1-f)*(1-e)**2+f*e**2, e*(1-e), e*(1-e),
     (1-f)*e**2+f*(1-e)**2)
assert (1-f)*e+f*(1-e) == t
assert sum(a) == sum(b) == 1
assert b[1]+b[3] == b[2]+b[3] == t
print(a, b, sum(float(p)*log(float(p/q)) for p,q in zip(b,a)))
def bb_tail(probability):
    p = float(probability)
    return 1-sum(comb(1000,k)*p**k*(1-p)**(1000-k) for k in range(4))
print(bb_tail(a[3]), bb_tail(b[3]))
```

Main recomputed these quantities after saving the JSON: exact rational/decimal
values, normalized laws, marginals, KL and both binomial tails match. No
scientific source or cluster was opened for that verification.

Main's conclusion: **stop C as the current method lead**. The identifiable
toy is already distinguishable by ordinary likelihood; permitting an
unconstrained correlated artifact law defeats allele attribution. We have
not supplied an independently testable real-artifact constraint or a distinct
method contribution. This does not establish that real sequencing attribution
is universally impossible. Do not follow this stop with a MIMS availability
search, bulk download or another wrapper project to rescue C. The independent
Sol6.1/high-requested reviewer accepts this narrow conclusion after a required
clarification: reads are independent in the correlated case too. That wording
is now explicit above; correlation is only within a read. The reviewer also
confirmed the exact laws, KL, tails and sharp missing-label interval, while
distinguishing that interval from a statistical confidence interval. Main
accepts STOP with these corrections. See the [review record](2026-10-07-error-twin-independent-review.md).

Checkpoint verification: saved JSON recomputation PASS; 11 documentation-scope
tests pass; manuscript consistency and `git diff --check` pass. Scientific code
is unchanged from the earlier full suite of 737 passed, 35 skipped; that full
suite was not rerun for this note-only/analytical-output checkpoint.

All three proposed method leads are rejected or unselected in their current
form. The broad publication objective remains active; DeepSV remains excluded.
Requested model/effort configuration is not independently attested. Dalton
was closed after its completed decision, not after a timed-out observation.
