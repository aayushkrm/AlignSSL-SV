# Acquisition/control review: no selected method

October 7, 2026. Main-recorded ledger of maintained independent reviewer
Dirac (`01a11272-8c0c-7bf1-aef2-66b3a3bc8dec`), requested Sol6.1/high.
Pauli's decision requested Sol6.1/max. Requests are not attested runtime.

## Actual native-component control

Pinned BOSS: `a5b6af8520669dd3d182bbf95021a7242a2ede4e`.
[Simulation](https://github.com/goldman-gp-ebi/BOSS-RUNS/blob/a5b6af8520669dd3d182bbf95021a7242a2ede4e/boss/aeons/simulation.py)
feeds full sampled lengths, obtained before truncation, to its estimator.
The resulting `lam`/`approx_ccl` enter later strategy calculations. Main read
complete simulation/sampler/estimator sources, scoring at recorded ranges.

[Script](../../analysis/check_aeons_observability.py) fetches only the reviewed
3,898-byte estimator into RAM, validates size and Git blob
`46d29031a0d9c31518c004a15a79f190eb94943a`, then executes only its class.
Estimator-source SHA256:
`f985f7f4a29cabf26b37802bf538ea65e88f21ac4a3da760e8f16e01744939c3`.
Existing NumPy 1.26.4; two executions gave the same saved values. No genomes.

| Observed data in both cases | Hidden rejected length | Native `lam` | Guard `lam` |
|---|---:|---:|---:|
| Kept 4,000; rejected prefix 400 bases | 10,000 | 7,000 | 4,000 |
| Kept 4,000; rejected prefix 400 bases | 40,000 | 22,000 | 4,000 |

Native `approx_ccl` differs; guard states are identical. The class excludes
lengths ≤800 at its default 400-base prefix, so guard `lam` is **4,000, not
2,200**. This negative control is not a corrected estimator or selection-bias
correction. Accepted lengths are selected data.
[Exact output](../../results/analytic_controls/2026-10-07/aeons_observability.json).

Conclusion: hidden rejected lengths change estimator state at matched observed
evidence. No full simulator, strategy-mask change, acceptance effect, time
saving or SV performance measured. Not target-label leakage, biological-result
invalidation or a new biological foundation. A separately declared fixed prior
would be different from hidden evaluation-stream feedback.

```sh
../.venv/bin/python analysis/check_aeons_observability.py
../.venv/bin/python -m pytest -q tests/test_aeons_observability_control.py
```

Four offline tests check size/blob fail-closed behavior and saved-output scope;
they do not emulate the native controller. Actual native execution is separate.

## Reviewer scope and decisions

Dirac initially made four Firecrawl scrapes, no searches, after reading its
skill: pinned simulation/sampler/batch/core raw URLs, markdown, maxAge=0,
timeout 30 seconds, no extraction-size cap. Simulation fully inspected;
others keyword contexts only. No blob rehash or estimator inspection then.
On follow-up Dirac read the script and accepted sensitivity, requiring the
4,000/2,200 explanation. Dirac did not rerun or fetch the class. Main performed
executions/pin checks; no independent replication claim.

Dirac's two-topology causal discriminator was only a candidate, not execution
approval. Useful endpoint: unique correct resolution at charged pore-time,
native/static/end/accept-all controls, prefix-only evidence, reachable and
unreachable cases. Joint phased links can suffice without a single long read.
Pauli rejected acquisition: residual native benefit, physical opportunity,
blinded topology truth and real counterfactual costs are unverified. Main
accepts rejection; no replay wrapper, controller or toy campaign follows.

Pauli's paper-only region-C consequence gate was accepted as triage only by
Dirac, with shared junction/copy constraints, fixed annotation and symmetric
genes. Main previously saw clinical results: **phenotype not used for
selection**, not blinded. The source check then failed to reconcile case
identity. Both agents required UNRESOLVED/STOP, no fabricated C structures or
substitution of chromosome X. Main visually checked the relevant PDF table
and caption, accepts stop. [Case check](2026-10-07-region-c-consequence-gate.md).

No functional advantage, biological null, publication lead or campaign.
Goal active, unachieved; historical stop decisions/full charge remain intact.

Final ledger review: Dirac found the conclusions/scope accurate, did no new
fetch, run or write. Requested clearer source-SHA and public-PDF/raw-data
wording are applied. Pauli also returned a **post-finding** response: its
three-C assumption was unsupported; visual confirmation should stop the
fixed C gate without X substitution. This is distinct from simply applying
the original predeclared missing-information rule.
