import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from app.adapters.router import SourceRouter
from app.adapters.csv_adapter import CsvSourceAdapter
from app.adapters.resume_adapter import ResumeSourceAdapter
from app.adapters.github_adapter import GitHubAdapter
from app.pipeline.normalization.engine import NormalizationEngine
from app.pipeline.comparison.blocking.engine import BlockingEngine
from app.pipeline.comparison.comparators.registry import ComparatorRegistry
from app.pipeline.comparison.comparators.engine_integration import load_comparators
from app.pipeline.comparison.eligibility import EligibilityEngine
from app.pipeline.identity_resolution.engine import IdentityResolutionEngine
from app.pipeline.resolution.coordinator import ResolutionCoordinator

logger = logging.getLogger(__name__)

class EndToEndRunner:
    def __init__(self, projection_config_path: str = "config/projection/default.yaml"):
        self.router = SourceRouter()
        # Register known adapters
        from app.adapters.detector import SourceType
        self.router.register_adapter(SourceType.CSV, CsvSourceAdapter())
        self.router.register_adapter(SourceType.RESUME_PDF, ResumeSourceAdapter())
        
        self.norm_engine = NormalizationEngine()
        self.github_adapter = GitHubAdapter()
        self.comp_registry = load_comparators()  # loads from config/comparison/comparators.yaml
        self.blocking_engine = BlockingEngine()
        self.eligibility_engine = EligibilityEngine(self.comp_registry)
        self.id_res_pipeline = IdentityResolutionEngine(self.comp_registry)
        self.resolution_coordinator = ResolutionCoordinator(projection_config_path)

    def execute(self, inputs: List[str], output_base: str = "output"):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_dir = Path(output_base) / timestamp
        out_dir.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "execution_date": timestamp,
            "inputs": inputs,
            "timings": {}
        }
        
        start_total = time.time()
        
        # 1. Ingest
        logger.info("Starting Ingestion...")
        t0 = time.time()
        candidates = []
        for inp in inputs:
            p = Path(inp)
            if not p.exists():
                logger.warning(f"Input file not found: {p}")
                continue
            candidates.extend(self.router.process(p))
        stats["timings"]["ingest"] = time.time() - t0
        stats["num_candidates_raw"] = len(candidates)
        
        # 2. Normalize
        logger.info("Starting Normalization...")
        t0 = time.time()
        normalized_candidates = []
        for c in candidates:
            normalized_c = self.norm_engine.normalize(c)
            github_profile = self._github_profile_url(normalized_c)
            if github_profile:
                normalized_c = self.github_adapter.enrich(github_profile, normalized_c)
            normalized_candidates.append(normalized_c)
        stats["timings"]["normalize"] = time.time() - t0
        stats["num_candidates_normalized"] = len(normalized_candidates)
        
        # 3. Compare (Blocking & Eligibility)
        logger.info("Starting Comparison (Blocking & Eligibility)...")
        t0 = time.time()
        # Blocking
        candidate_pairs = self.blocking_engine.block(normalized_candidates)
        stats["num_blocked_pairs"] = len(candidate_pairs)
        
        # Eligibility
        eligible_pairs = []
        for pair in candidate_pairs:
            c_a = next(c for c in normalized_candidates if c.candidate_id == pair.candidate_a_id)
            c_b = next(c for c in normalized_candidates if c.candidate_id == pair.candidate_b_id)
            elig_res = self.eligibility_engine.is_eligible(c_a, c_b)
            if elig_res.eligible:
                eligible_pairs.append(pair)
        stats["num_eligible_pairs"] = len(eligible_pairs)
        stats["timings"]["compare"] = time.time() - t0
        
        # 4. Resolve Identity
        logger.info("Starting Identity Resolution...")
        t0 = time.time()
        resolutions = []
        matches = []
        no_matches = 0
        reviews = 0
        for pair in eligible_pairs:
            c_a = next(c for c in normalized_candidates if c.candidate_id == pair.candidate_a_id)
            c_b = next(c for c in normalized_candidates if c.candidate_id == pair.candidate_b_id)
            res = self.id_res_pipeline.resolve(c_a, c_b, pair)
            resolutions.append(res)
            # Assuming enum value or string matches MATCH
            decision_str = str(res.decision)
            if decision_str.endswith("MATCH") and not decision_str.endswith("NO_MATCH"):
                matches.append(res)
            elif decision_str.endswith("NO_MATCH"):
                no_matches += 1
            elif decision_str.endswith("REVIEW"):
                reviews += 1
                
        stats["num_resolutions"] = len(resolutions)
        stats["num_matches"] = len(matches)
        stats["num_no_matches"] = no_matches
        stats["num_reviews"] = reviews
        stats["timings"]["resolve"] = time.time() - t0
        
        # 5. Final Resolution (Merge & Project)
        logger.info("Starting Final Resolution & Projection...")
        t0 = time.time()
        final_results = self.resolution_coordinator.coordinate(normalized_candidates, matches)
        stats["timings"]["resolution_coordinator"] = time.time() - t0
        # Write Outputs
        logger.info(f"Writing outputs to {out_dir}")
        projected_data = [res[0].dictionary_view for res in final_results]
        with open(out_dir / "projected_candidates.json", "w") as f:
            json.dump(projected_data, f, indent=2)
            
        cluster_summaries = []
        seen_clusters = set()
        for proj, cluster in final_results:
            if id(cluster) not in seen_clusters:
                seen_clusters.add(id(cluster))
                status_str = cluster.status.value if hasattr(cluster.status, "value") else str(cluster.status)
                if status_str.startswith("ClusterStatus."):
                    status_str = status_str.replace("ClusterStatus.", "")
                cluster_summaries.append({
                    "status": status_str,
                    "size": len(cluster.candidates),
                    "contradictions": cluster.contradictions
                })
        
        stats["num_clusters"] = len(cluster_summaries)
        with open(out_dir / "cluster_summary.json", "w") as f:
            json.dump(cluster_summaries, f, indent=2)
            
        stats["timings"]["total"] = time.time() - start_total
        
        with open(out_dir / "statistics.json", "w") as f:
            json.dump(stats, f, indent=2)
            
        return out_dir, stats, final_results, normalized_candidates, matches

    def _github_profile_url(self, candidate):
        for profile in candidate.social_profiles:
            if profile.platform.lower() == "github" and profile.url:
                return profile.url
        return None
