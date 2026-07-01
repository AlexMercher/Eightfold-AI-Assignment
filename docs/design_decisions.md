# Design Decisions

## Dataset Augmentation Strategy
**Decision:** Built a deterministic, logic-based Python augmentation tool over a purely LLM/Generative approach for testing datasets.
**Reason:** Testing pipelines like Identity Resolution require deterministic, highly reproducible datasets to accurately measure regressions in matching logic (F1, Precision, Recall). LLMs introduce variability that makes pipeline debugging difficult.
**Alternatives Considered:** Prompting an LLM to generate variations on-the-fly or writing random transformations without seeding. 
**Why this approach was selected:** A logic-based approach with seeded RNGs (`random.Random(seed)`) and a `StrategySelector` ensures maximum coverage of edge cases (e.g. name variations, email formatting) while guaranteeing identical outputs on every run.
**Future improvements:** Could read lists of typical typos or synonyms from a database for even more robust edge cases, without breaking determinism.

## CSV Processing Module
**Decision:** Used `pandas` for reading and writing CSVs in the augmentation script.
**Reason:** Offers robust handling of missing values (filling with empty strings instead of complex NaN checks), clean API for dictionary conversions, and is already a project dependency. Readability and maintainability were prioritized over marginal performance gains.
**Alternatives Considered:** Built-in `csv` module.
**Why this approach was selected:** Provides cleaner typing and mapping to the underlying `CandidateRecord` dataclasses.
**Future improvements:** Could stream the dataset if sizes grow extremely large, though for augmentation of testing sets memory is typically sufficient.

## Modular Strategy Executor
**Decision:** Implemented a `StrategySelector` class to wrap augmentation rules.
**Reason:** Pure random selection might omit rare rules entirely. We needed a guarantee that every augmentation strategy is exercised at least once.
**Alternatives Considered:** Standard `random.choice`.
**Why this approach was selected:** A stateful cycler guarantees round-robin strategy execution before repeating, fulfilling test coverage requirements while remaining strictly deterministic via seeded `shuffle`.
**Future improvements:** Weighting strategies to reflect real-world distributions (e.g. initial names happen 5% of the time, whereas lowercased emails happen 40% of the time).

## GitHub URL Identity Classification
**Decision:** GitHub repository URLs are never converted into profile URLs. Only URLs classified by `GitHubURLClassifier` as `PROFILE` may populate the canonical GitHub social profile.
**Reason:** Removing repository path segments invents identity evidence that was not explicitly present in the resume, which can corrupt blocking and identity resolution.
**Alternatives Considered:** Strip `github.com/<username>/<repo>` down to `github.com/<username>` as a convenience fallback.
**Why this approach was selected:** Deterministic extraction must distinguish identity links from project links. The shared classifier and centralized constants avoid duplicated route/placeholder logic across extraction, normalization, and enrichment.
**Debugging finding:** Focused pytest runs require `--noconftest` in this checkout because the repository-wide conftest imports missing API storage modules unrelated to this GitHub pipeline path.
