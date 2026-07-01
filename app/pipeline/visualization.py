import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Optional, Tuple
from app.models.canonical import Candidate
from app.pipeline.identity_resolution.models import IdentityResolutionResult

class GraphVisualizer:
    def __init__(
        self,
        candidates: List[Candidate],
        matches: List[IdentityResolutionResult],
        final_results: Optional[List[Tuple]] = None,
    ):
        self.candidates = {c.candidate_id: c for c in candidates}
        self.matches = matches
        self.G = nx.Graph()

        # Build a set of candidate-pair IDs that belong to INVALID clusters so
        # they can be styled differently in the visualization.
        self._invalid_pairs: set = set()
        if final_results:
            for _proj, cluster in final_results:
                status_val = getattr(cluster.status, "value", str(cluster.status))
                if status_val == "INVALID" or str(cluster.status) == "INVALID":
                    cand_ids = [c.candidate_id for c in cluster.candidates]
                    for i in range(len(cand_ids)):
                        for j in range(i + 1, len(cand_ids)):
                            a, b = sorted([cand_ids[i], cand_ids[j]])
                            self._invalid_pairs.add((a, b))

        # Build Graph
        for c_id, c in self.candidates.items():
            source = c_id.split("_")[0] if "_" in c_id else "unknown"
            self.G.add_node(
                c_id,
                label=c.personal_info.name if c.personal_info else "Unknown",
                source=source,
            )

        for m in self.matches:
            a_id = m.candidate_pair.candidate_a_id
            b_id = m.candidate_pair.candidate_b_id
            a, b = sorted([a_id, b_id])
            is_invalid = (a, b) in self._invalid_pairs
            self.G.add_edge(a_id, b_id, weight=1.0, invalid=is_invalid)

    def export_png(self, filepath: Path):
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.G, k=0.5, iterations=50)

        # Draw nodes
        sources = set(nx.get_node_attributes(self.G, "source").values())
        colors = plt.cm.get_cmap("tab10", max(len(sources), 1))
        color_map = {src: colors(i) for i, src in enumerate(sources)}
        node_colors = [color_map[self.G.nodes[n]["source"]] for n in self.G.nodes()]

        # Split edges by validity
        valid_edges = [(u, v) for u, v, d in self.G.edges(data=True) if not d.get("invalid")]
        invalid_edges = [(u, v) for u, v, d in self.G.edges(data=True) if d.get("invalid")]

        nx.draw_networkx_nodes(self.G, pos, node_color=node_colors, node_size=500, alpha=0.8)
        if valid_edges:
            nx.draw_networkx_edges(self.G, pos, edgelist=valid_edges, width=2.0, alpha=0.6, edge_color="steelblue")
        if invalid_edges:
            nx.draw_networkx_edges(
                self.G, pos, edgelist=invalid_edges,
                width=2.0, alpha=0.8, edge_color="red", style="dashed",
            )
        nx.draw_networkx_labels(
            self.G, pos,
            labels=nx.get_node_attributes(self.G, "label"),
            font_size=8,
        )

        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color="steelblue", linewidth=2, label="VALID / WARNING match"),
            Line2D([0], [0], color="red", linewidth=2, linestyle="dashed", label="INVALID match (rejected)"),
        ]
        plt.legend(handles=legend_elements, loc="upper left", fontsize=8)

        plt.title("Candidate Identity Resolution Graph")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close()

    def export_dot(self, filepath: Path):
        lines = ["graph G {"]
        for n, attr in self.G.nodes(data=True):
            label = attr.get("label", "").replace('"', '\\"')
            lines.append(f'  "{n}" [label="{label}"];')
        for u, v, d in self.G.edges(data=True):
            style = ' [style=dashed color=red label="INVALID"]' if d.get("invalid") else ""
            lines.append(f'  "{u}" -- "{v}"{style};')
        lines.append("}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def export_mermaid(self, filepath: Path):
        lines = ["graph TD"]
        for n, attr in self.G.nodes(data=True):
            label = attr.get("label", "").replace('"', "")
            lines.append(f'  {n}["{label}"]')
        for u, v, d in self.G.edges(data=True):
            if d.get("invalid"):
                lines.append(f"  {u} -. INVALID .- {v}")
            else:
                lines.append(f"  {u} --- {v}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
