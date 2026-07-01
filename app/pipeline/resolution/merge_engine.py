from typing import Dict, List, Any
from app.models.canonical import Candidate, PersonalInfo, ContactInfo, ProfessionalInfo
from .models import ValidatedCluster, MergeResult, ProvenanceRecord, ConflictResult
from .conflict_resolver import ConflictResolver

class MergeEngine:
    def __init__(self, conflict_resolver: ConflictResolver):
        self.resolver = conflict_resolver
        
    def merge(self, cluster: ValidatedCluster) -> MergeResult:
        if not cluster.candidates:
            raise ValueError("Cannot merge empty cluster")
            
        merged_id = f"merged_{cluster.candidates[0].candidate_id}"
        merged = Candidate(candidate_id=merged_id)
        
        conflicts: Dict[str, ConflictResult] = {}
        provenance: Dict[str, ProvenanceRecord] = {}
        
        source_ids = [c.candidate_id for c in cluster.candidates]
        
        # 1. Merge PersonalInfo
        names = []
        name_sources = []
        for c in cluster.candidates:
            if c.personal_info and c.personal_info.name:
                names.append(c.personal_info.name)
                name_sources.append(c.candidate_id)
        name_conflict = self.resolver.resolve_scalar(names, name_sources)
        
        # Build PersonalInfo
        if name_conflict.winning_value:
            merged.personal_info = PersonalInfo(name=name_conflict.winning_value)
            conflicts["personal_info.name"] = name_conflict
            provenance["personal_info.name"] = ProvenanceRecord(
                source_candidates=source_ids, 
                merge_decision_path=name_conflict.reason
            )
            
        # 2. Merge ContactInfo (Arrays: union deduplication)
        all_emails = set()
        all_phones = set()
        for c in cluster.candidates:
            if c.contact_info:
                if c.contact_info.emails:
                    for e in c.contact_info.emails:
                        all_emails.add(e.lower())
                if c.contact_info.phone_numbers:
                    for p in c.contact_info.phone_numbers:
                        all_phones.add(p)
                        
        if all_emails or all_phones:
            merged.contact_info = ContactInfo(
                emails=list(all_emails),
                phone_numbers=list(all_phones)
            )
            provenance["contact_info"] = ProvenanceRecord(
                source_candidates=source_ids,
                merge_decision_path="Set Union Deduplication"
            )
            
        # 3. Merge ProfessionalInfo
        companies = []
        company_sources = []
        for c in cluster.candidates:
            if c.professional_info and c.professional_info.current_company:
                companies.append(c.professional_info.current_company)
                company_sources.append(c.candidate_id)
        comp_conflict = self.resolver.resolve_scalar(companies, company_sources)
        
        all_skills = set()
        for c in cluster.candidates:
            if c.professional_info and c.professional_info.skills:
                # Skill is an object, we need to hash by name
                for s in c.professional_info.skills:
                    if s.name:
                        all_skills.add(s.name.lower())
                        
        if comp_conflict.winning_value or all_skills:
            # We skip reconstructing full skill objects for this mock implementation 
            # and just attach the string list or rebuild mock Skill objects
            from app.models.canonical import Skill
            skills_list = [Skill(name=s) for s in all_skills]
            
            merged.professional_info = ProfessionalInfo(
                current_company=comp_conflict.winning_value,
                skills=skills_list
            )
            conflicts["professional_info.current_company"] = comp_conflict
            provenance["professional_info.current_company"] = ProvenanceRecord(
                source_candidates=source_ids,
                merge_decision_path=comp_conflict.reason
            )
            provenance["professional_info.skills"] = ProvenanceRecord(
                source_candidates=source_ids,
                merge_decision_path="Set Union Deduplication"
            )
            
        # 4. Education and Social Profiles (Arrays: union deduplication)
        # Assuming similar simple unioning by some key
        # (Omitted for brevity in this engine, identical to skills above)
        
        return MergeResult(
            candidate=merged,
            conflicts=conflicts,
            provenance=provenance
        )

    def wrap_single(self, candidate: Candidate) -> MergeResult:
        """Wrap a single candidate as a MergeResult without synthesizing a merged identity.

        Used by the coordinator for INVALID clusters where each source candidate
        must be projected independently while preserving its original candidate_id.
        Provenance is recorded so ConfidenceEngine and ProjectionEngine continue
        receiving structurally identical MergeResult objects.
        """
        provenance: Dict[str, ProvenanceRecord] = {
            "candidate": ProvenanceRecord(
                source_candidates=[candidate.candidate_id],
                merge_decision_path="identity-preserving (INVALID cluster: no merge performed)"
            )
        }
        return MergeResult(
            candidate=candidate,
            conflicts={},
            provenance=provenance
        )
