import sys
import os
import copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.adapters.csv_adapter import CsvSourceAdapter
from app.pipeline.normalization.engine import NormalizationEngine
from app.pipeline.comparison.blocking.engine import BlockingEngine
from app.pipeline.comparison.eligibility import EligibilityEngine
from app.pipeline.comparison.comparators.engine_integration import load_comparators
from app.pipeline.identity_resolution.engine import IdentityResolutionEngine
from app.pipeline.resolution.coordinator import ResolutionCoordinator
from app.adapters.github_adapter import GitHubAdapter

def run_audit():
    print("=== GitHub Enrichment Audit ===")
    
    # 1. Ingest
    adapter = CsvSourceAdapter()
    candidates_raw = adapter.process(Path('Master.csv'))
    
    norm_engine = NormalizationEngine()
    
    # Run A: Disabled
    cands_A = []
    for c in candidates_raw:
        cands_A.append(norm_engine.normalize(copy.deepcopy(c)))
        
    # Run B: Enabled
    cands_B = []
    github_adapter = GitHubAdapter()
    
    for c in candidates_raw:
        norm_c = norm_engine.normalize(copy.deepcopy(c))
        # Find github profile
        github_url = None
        for sp in norm_c.social_profiles:
            if sp.platform.lower() == "github" and sp.url:
                github_url = sp.url
                break
        
        if github_url:
            norm_c = github_adapter.enrich(github_url, norm_c)
        cands_B.append(norm_c)
        
    # Compare Candidate fields
    print("\n--- Step 2: Mutation Audit ---")
    mutations_found = 0
    for a, b in zip(cands_A, cands_B):
        if a.model_dump() != b.model_dump():
            print(f"Mutation in {a.candidate_id}:")
            for field in a.model_fields:
                val_a = getattr(a, field)
                val_b = getattr(b, field)
                if val_a != val_b:
                    print(f"  Field changed: {field}")
            mutations_found += 1
    if mutations_found == 0:
        print("No mutations found across all candidates.")
        
    # 3. Blocking
    print("\n--- Step 3: Blocking Audit ---")
    block_engine = BlockingEngine()
    pairs_A = block_engine.block(cands_A)
    pairs_B = block_engine.block(cands_B)
    
    if len(pairs_A) != len(pairs_B):
        print(f"Blocking Count Mismatch: A={len(pairs_A)}, B={len(pairs_B)}")
    else:
        print(f"Blocking Count Identical: {len(pairs_A)} pairs.")
        diff = set(pairs_A) ^ set(pairs_B)
        if diff:
            print(f"Blocking Pairs differ: {diff}")
        else:
            print("Blocking Pairs are exactly identical.")
            
    # 4 & 5. Eligibility & Comparators
    print("\n--- Step 4 & 5: Eligibility & Comparators Audit ---")
    registry = load_comparators()
    elig_engine = EligibilityEngine(registry)
    
    elig_A = []
    for p in pairs_A:
        ca = next(c for c in cands_A if c.candidate_id == p.candidate_a_id)
        cb = next(c for c in cands_A if c.candidate_id == p.candidate_b_id)
        elig_A.append(elig_engine.is_eligible(ca, cb))
        
    elig_B = []
    for p in pairs_B:
        ca = next(c for c in cands_B if c.candidate_id == p.candidate_a_id)
        cb = next(c for c in cands_B if c.candidate_id == p.candidate_b_id)
        elig_B.append(elig_engine.is_eligible(ca, cb))
        
    mismatches = 0
    for i, (ea, eb) in enumerate(zip(elig_A, elig_B)):
        if ea.eligible != eb.eligible or ea.matched_rule_id != eb.matched_rule_id:
            print(f"Eligibility Mismatch at pair {pairs_A[i]}: {ea} vs {eb}")
            mismatches += 1
            
    if mismatches == 0:
        print("Eligibility results are exactly identical.")
        
    # 6. Identity Resolution
    print("\n--- Step 6: Identity Resolution Audit ---")
    id_engine = IdentityResolutionEngine(registry)
    
    res_A = []
    for p, e in zip(pairs_A, elig_A):
        if e.eligible:
            ca = next(c for c in cands_A if c.candidate_id == p.candidate_a_id)
            cb = next(c for c in cands_A if c.candidate_id == p.candidate_b_id)
            res_A.append(id_engine.resolve(ca, cb, p))
            
    res_B = []
    for p, e in zip(pairs_B, elig_B):
        if e.eligible:
            ca = next(c for c in cands_B if c.candidate_id == p.candidate_a_id)
            cb = next(c for c in cands_B if c.candidate_id == p.candidate_b_id)
            res_B.append(id_engine.resolve(ca, cb, p))
            
    id_mismatches = 0
    for ra, rb in zip(res_A, res_B):
        if ra.decision != rb.decision:
            print(f"Decision Mismatch: {ra.decision} vs {rb.decision}")
            id_mismatches += 1
            
        if ra.similarity_result and rb.similarity_result:
            if ra.similarity_result.total_score != rb.similarity_result.total_score:
                print(f"Total Score Mismatch: {ra.similarity_result.total_score} vs {rb.similarity_result.total_score}")
                id_mismatches += 1
            else:
                for k in ra.similarity_result.comparator_results.keys():
                    sc_a = ra.similarity_result.comparator_results[k].score
                    sc_b = rb.similarity_result.comparator_results[k].score
                    if sc_a != sc_b:
                        print(f"Comparator Score Mismatch on {k}: {sc_a} vs {sc_b}")
                        id_mismatches += 1
    if id_mismatches == 0:
        print("Identity Resolution results are exactly identical.")
        
    # 7. Merge (Coordinator)
    print("\n--- Step 7: Graph & Merge Audit ---")
    coord = ResolutionCoordinator()
    merge_A = coord.coordinate(cands_A, res_A)
    coord2 = ResolutionCoordinator()
    merge_B = coord2.coordinate(cands_B, res_B)
    
    print(f"Projected Candidates A: {len(merge_A)}")
    print(f"Projected Candidates B: {len(merge_B)}")
    
    diffs = 0
    if len(merge_A) != len(merge_B):
        print("Different number of projected candidates!")
        diffs += 1
    
    for (pa, _), (pb, _) in zip(merge_A, merge_B):
        # We only expect differences in the enriched fields and provenance
        da = pa.dictionary_view
        db = pb.dictionary_view
        
        # Check if identical outside of enriched fields?
        if da['candidate_id'] != db['candidate_id']:
            print("Different candidate merge ID!")
            diffs += 1
            
    if diffs == 0:
        print("Merge clusters matched exactly (ignoring pure field completion differences).")

if __name__ == "__main__":
    run_audit()
