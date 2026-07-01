from typing import List, Dict, Set, Tuple
from collections import defaultdict
from app.models.canonical import Candidate
from app.pipeline.identity_resolution.models import IdentityResolutionResult, DecisionType

class CandidateGraph:
    def __init__(self):
        # adjacency list: candidate_id -> list of adjacent candidate_ids
        self.adj: Dict[str, Set[str]] = defaultdict(set)
        # nodes mapping: candidate_id -> Candidate
        self.nodes: Dict[str, Candidate] = {}
        # edges mapping: (id1, id2) -> IdentityResolutionResult
        self.edges: Dict[tuple, IdentityResolutionResult] = {}
        
    def build(self, candidates: List[Candidate], resolution_results: List[IdentityResolutionResult]):
        # Add all candidates as disconnected nodes initially
        for cand in candidates:
            self.nodes[cand.candidate_id] = cand
            
        # Add edges for MATCH decisions
        for res in resolution_results:
            if res.decision == DecisionType.MATCH:
                id_a = res.candidate_pair.candidate_a_id
                id_b = res.candidate_pair.candidate_b_id
                
                # Bi-directional edges
                self.adj[id_a].add(id_b)
                self.adj[id_b].add(id_a)
                
                # Store edge data (sorted tuple to ensure undirected consistency)
                a, b = sorted([id_a, id_b])
                self.edges[(a, b)] = res
                
    def get_connected_components(self) -> List[Tuple[List[Candidate], List[IdentityResolutionResult]]]:
        """
        Runs BFS/DFS to extract connected components.
        Returns a list of (Component_Candidates, Component_Edges).
        """
        visited: Set[str] = set()
        components = []
        
        for node_id in self.nodes.keys():
            if node_id not in visited:
                # BFS
                comp_ids = set()
                queue = [node_id]
                visited.add(node_id)
                
                while queue:
                    curr = queue.pop(0)
                    comp_ids.add(curr)
                    for neighbor in self.adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                            
                # Reconstruct Candidate objects and Edges for this component
                comp_candidates = [self.nodes[cid] for cid in sorted(comp_ids)] # sorted for determinism
                comp_edges = []
                
                # Gather edges internal to this component
                comp_ids_list = list(comp_ids)
                for i in range(len(comp_ids_list)):
                    for j in range(i + 1, len(comp_ids_list)):
                        a, b = sorted([comp_ids_list[i], comp_ids_list[j]])
                        if (a, b) in self.edges:
                            comp_edges.append(self.edges[(a, b)])
                            
                components.append((comp_candidates, comp_edges))
                
        return components
