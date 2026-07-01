import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .models import MergeResult, ProjectedCandidate, ProjectionResult, ConfidenceResult
from .path_resolver import PathResolver, MISSING

class ProjectionError(Exception):
    pass

class ProjectionEngine:
    def __init__(self, config_path: str = "config/projection/default.yaml"):
        self.fields_config = {}
        self.include_provenance = False
        self.include_confidence = False
        self.include_sources = False
        self.path_resolver = PathResolver()
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Projection config not found: {config_path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() == '.json':
                import json
                data = json.load(f) or {}
            else:
                data = yaml.safe_load(f) or {}
            
        allowed_top_keys = {"fields", "include_provenance", "include_confidence", "include_sources"}
        for key in data.keys():
            if key not in allowed_top_keys:
                raise ValueError(f"Unknown configuration key at top level: {key}")
                
        self.include_provenance = bool(data.get("include_provenance", False))
        self.include_confidence = bool(data.get("include_confidence", False))
        self.include_sources = bool(data.get("include_sources", False))
        self.fields_config = data.get("fields", {})
        
        allowed_field_keys = {"from", "on_missing", "map"}
        for field_name, field_def in self.fields_config.items():
            self._validate_field_node(field_name, field_def)

    def _validate_field_node(self, node_name: str, node: Dict[str, Any]):
        if not isinstance(node, dict):
            raise ValueError(f"Field configuration for '{node_name}' must be a dictionary")
            
        if "from" in node:
            # It's a Leaf Node
            allowed_keys = {"from", "on_missing", "map"}
            for key in node.keys():
                if key not in allowed_keys:
                    raise ValueError(f"Unknown configuration key in field '{node_name}': {key}")
            
            on_missing = node.get("on_missing")
            if on_missing is None:
                on_missing = "null"
            if on_missing not in ("null", "omit", "error"):
                raise ValueError(f"Invalid on_missing value '{on_missing}' in field '{node_name}'")
                
            if "map" in node:
                if not isinstance(node["map"], dict):
                    raise ValueError(f"'map' in field '{node_name}' must be a dictionary")
                for k, v in node["map"].items():
                    if not isinstance(v, str):
                        raise ValueError(f"Value for mapped key '{k}' in field '{node_name}' must be a string path")
        else:
            # It's a Structural Node (nested object)
            for child_name, child_def in node.items():
                self._validate_field_node(f"{node_name}.{child_name}", child_def)
        
    def project(self, merge_result: MergeResult, confidence_result: Optional[ConfidenceResult] = None) -> ProjectionResult:
        candidate = merge_result.candidate
        dictionary_view = self._project_node(self.fields_config, candidate)

        if self.include_provenance and merge_result.provenance:
            # Output provenance as per assignment
            dictionary_view["provenance"] = {
                k: v.model_dump() for k, v in merge_result.provenance.items()
            }
            
        if self.include_confidence and confidence_result:
            dictionary_view["confidence"] = confidence_result.model_dump()
            
        if self.include_sources and merge_result.provenance:
            sources = set()
            for prov in merge_result.provenance.values():
                for s in prov.source_candidates:
                    sources.add(s)
            dictionary_view["sources"] = sorted(list(sources))
            
        # Optional backward compatibility wrapper
        try:
            proj = ProjectedCandidate(**dictionary_view)
        except Exception:
            proj = None
            
        return ProjectionResult(
            dictionary_view=dictionary_view,
            projected=proj
        )

    def _project_node(self, node: Dict[str, Any], context: Any) -> Dict[str, Any]:
        result = {}
        for key, field_def in node.items():
            if "from" in field_def:
                # Leaf node
                source_path = field_def["from"]
                on_missing = field_def.get("on_missing", "null")
                if on_missing is None:
                    on_missing = "null"
                    
                value = self.path_resolver.resolve(context, source_path)
                
                if value is MISSING or value is None:
                    if on_missing == "error":
                        raise ProjectionError(f"Projection failed: field '{key}' is missing at path '{source_path}'")
                    elif on_missing == "omit":
                        continue
                    else:
                        result[key] = None
                else:
                    if "map" in field_def:
                        # Array projection
                        if not isinstance(value, list) and not isinstance(value, tuple):
                            value = [value]
                            
                        mapped_list = []
                        for item in value:
                            item_dict = {}
                            for mk, mv in field_def["map"].items():
                                m_val = self.path_resolver.resolve(item, mv)
                                # Sub-fields missing behavior not specified in map. We will use omit for simplicity, 
                                # or null. Let's use null if missing, unless we want to apply on_missing.
                                # The instruction says "Do not invent a new projection language", so we keep it minimal.
                                item_dict[mk] = None if m_val is MISSING else self._serialize(m_val)
                            mapped_list.append(item_dict)
                        result[key] = mapped_list
                    else:
                        result[key] = self._serialize(value)
            else:
                # Structural node
                nested_result = self._project_node(field_def, context)
                result[key] = nested_result
        return result

    def _serialize(self, obj: Any) -> Any:
        from pydantic import BaseModel
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        elif isinstance(obj, list) or isinstance(obj, tuple):
            return [self._serialize(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        return obj
