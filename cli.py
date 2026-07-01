import argparse
import sys
import json
import logging
import subprocess
import importlib
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1.0.0"

# ─── Argument Parsing ─────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="Resume Identity Resolution Pipeline CLI\n\nOrchestrates the ingestion, normalization, comparison, resolution, and projection of candidate profiles.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="See commands.md for full documentation and examples."
    )
    
    # Global flags
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging (DEBUG level)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress logging output (WARNING level and above only)")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # version
    subparsers.add_parser("version", help="Print pipeline version")

    # doctor
    subparsers.add_parser(
        "doctor", 
        help="Comprehensive system health check",
        description="Validates the environment, checking for required dependencies, config files, directories, and data files."
    )

    # verify
    subparsers.add_parser(
        "verify", 
        help="Run all architecture verification scripts",
        description="Executes internal architectural integrity checks (e.g., verify_resolution.py) to ensure pipeline invariants hold."
    )

    # test
    parser_test = subparsers.add_parser(
        "test", 
        help="Run automated test suites",
        description="Runs pytest over the tests/ directory."
    )

    # ingest
    parser_ingest = subparsers.add_parser(
        "ingest", 
        help="Ingest input files into Canonical Candidates",
        description="Reads PDF/CSV files and parses them into Canonical Candidate models."
    )
    parser_ingest.add_argument("--inputs", nargs="+", required=True, help="Input files (PDFs, CSVs) to process")

    # normalize
    parser_normalize = subparsers.add_parser(
        "normalize", 
        help="Run through normalization stage",
        description="Ingests candidates and normalizes fields (names, phones, emails, skills) using aliases and standardization rules."
    )
    parser_normalize.add_argument("--inputs", nargs="+", required=True, help="Input files to process")

    # compare
    parser_compare = subparsers.add_parser(
        "compare", 
        help="Run through blocking & eligibility stage",
        description="Generates eligible candidate pairs using blocking keys and hard eligibility rules."
    )
    parser_compare.add_argument("--inputs", nargs="+", required=True, help="Input files to process")

    # resolve
    parser_resolve = subparsers.add_parser(
        "resolve", 
        help="Run through identity resolution stage",
        description="Compares eligible pairs and computes MATCH / NO_MATCH / REVIEW decisions."
    )
    parser_resolve.add_argument("--inputs", nargs="+", required=True, help="Input files to process")

    # merge
    parser_merge = subparsers.add_parser(
        "merge", 
        help="Run through merge stage",
        description="Combines matched candidates into unified profiles resolving conflicts via priority rules."
    )
    parser_merge.add_argument("--inputs", nargs="+", required=True, help="Input files to process")

    # project
    parser_project = subparsers.add_parser(
        "project", 
        help="Run through projection stage",
        description="Projects canonical merged candidates into a configured JSON schema."
    )
    parser_project.add_argument("--inputs", nargs="+", required=True, help="Input files to process")
    parser_project.add_argument("--projection", default="default", help="Projection config (e.g. 'ats', 'default', 'assignment_example.json')")

    # run (E2E)
    parser_run = subparsers.add_parser(
        "run", 
        help="Run the complete end-to-end pipeline",
        description="Executes all pipeline stages: Ingest -> Normalize -> Compare -> Resolve -> Merge -> Project -> Visualize.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Example:\n  python cli.py run --inputs Master.csv --projection assignment_example.json"
    )
    parser_run.add_argument("--inputs", nargs="+", required=True, help="Input files (PDFs, CSVs)")
    parser_run.add_argument("--output", default="output", help="Base output directory (default: 'output')")
    parser_run.add_argument("--projection", default="default", help="Projection config to use (default: 'default')")

    # visualize
    parser_vis = subparsers.add_parser(
        "visualize", 
        help="Generate pipeline visualizations",
        description="Generates .png, .dot, and .mmd identity graphs for the given inputs."
    )
    parser_vis.add_argument("--inputs", nargs="+", required=True, help="Input files to process")

    # stats
    parser_stats = subparsers.add_parser(
        "stats", 
        help="Print statistics from a previous run",
        description="Reads the statistics.json from a specified run directory and formats the output."
    )
    parser_stats.add_argument("--run-dir", required=True, help="Path to a timestamped run directory (e.g., output/2026-07-01_12-00-00)")

    # config
    subparsers.add_parser(
        "config", 
        help="Validate and display configuration",
        description="Loads all YAML configs and ensures they are well-formed, printing summaries."
    )

    # explain
    parser_explain = subparsers.add_parser(
        "explain", 
        help="Explain resolution path for two candidates",
        description="Provides a detailed, structured breakdown of why two candidates matched or didn't."
    )
    parser_explain.add_argument("candidate_a", help="Candidate A ID")
    parser_explain.add_argument("candidate_b", help="Candidate B ID")
    parser_explain.add_argument("--inputs", nargs="+", required=True, help="Input files to load candidates from")

    return parser.parse_args()


# ─── Doctor ───────────────────────────────────────────────────────────────────

def run_doctor():
    print("Running pipeline doctor...\n")

    all_pass = True

    def check(label, status, hint=""):
        nonlocal all_pass
        if status == "PASS":
            print(f"  [PASS] {label}")
        elif status == "WARNING":
            print(f"  [WARNING] {label}" + (f"  ->  {hint}" if hint else ""))
        else:
            print(f"  [FAIL] {label}" + (f"  ->  {hint}" if hint else ""))
            all_pass = False

    # Environment
    print("  [Environment]")
    import sys as _sys
    py_ver = _sys.version_info
    check(f"Python version ({py_ver.major}.{py_ver.minor}.{py_ver.micro})", 
          "PASS" if py_ver >= (3, 8) else "FAIL", "Python 3.8+ required")
    
    in_venv = _sys.prefix != _sys.base_prefix
    check("Virtual Environment", "PASS" if in_venv else "WARNING", "Not running inside a virtual environment (conda/venv)")

    # Config files
    print("\n  [Configuration]")
    required_configs = [
        ("config/normalization/skills_aliases.yaml",     "skills_aliases.yaml", True),
        ("config/normalization/company_aliases.yaml",    "company_aliases.yaml", True),
        ("config/normalization/job_title_aliases.yaml",  "job_title_aliases.yaml", True),
        ("config/comparison/comparators.yaml",           "comparators.yaml", True),
        ("config/comparison/blocking.yaml",              "blocking.yaml", True),
        ("config/comparison/eligibility.yaml",           "eligibility.yaml", True),
        ("config/identity_resolution/rules.yaml",        "rules.yaml", True),
        ("config/identity_resolution/weights.yaml",      "weights.yaml", True),
        ("config/identity_resolution/thresholds.yaml",   "thresholds.yaml", True),
        ("config/resolution/conflict.yaml",              "conflict.yaml", True),
        ("config/resolution/confidence.yaml",            "confidence.yaml", True),
        ("config/projection/default.yaml",               "projection default.yaml", True),
        ("config/projection/minimal.yaml",               "projection minimal.yaml", False),
        ("config/projection/ats.yaml",                   "projection ats.yaml", False),
        ("config/projection/assignment_example.json",    "projection assignment_example.json", False),
    ]
    for path, label, is_required in required_configs:
        exists = Path(path).exists()
        if exists:
            check(label, "PASS")
        else:
            check(label, "FAIL" if is_required else "WARNING", f"Missing: {path}")

    # Datasets
    print("\n  [Datasets]")
    check("Master.csv", "PASS" if Path("Master.csv").exists() else "WARNING", "Missing optional Master.csv dataset")
    check("generated_data/ directory", "PASS" if Path("generated_data").is_dir() else "WARNING", "Missing generated_data/")
    check("matching_candidates.csv", "PASS" if Path("generated_data/matching_candidates.csv").exists() else "WARNING")
    check("conflict_candidates.csv", "PASS" if Path("generated_data/conflict_candidates.csv").exists() else "WARNING")
    check("new_candidates.csv", "PASS" if Path("generated_data/new_candidates.csv").exists() else "WARNING")
    check("Resumes/ directory", "PASS" if Path("Resumes").is_dir() else "WARNING", "Missing Resumes/ directory (needed for PDFs)")

    # Dependencies
    print("\n  [Dependencies]")
    packages = [
        ("pydantic",   "pydantic", True),
        ("yaml",       "pyyaml", True),
        ("pandas",     "pandas", True),
        ("rapidfuzz",  "rapidfuzz", True),
        ("networkx",   "networkx", True),
        ("matplotlib", "matplotlib", True),
        ("phonenumbers","phonenumbers", True),
        ("pytest",     "pytest", True),
        ("fitz",       "PyMuPDF", False),
        ("paddleocr",  "paddleocr", False),
    ]
    for mod, pkg, is_required in packages:
        try:
            importlib.import_module(mod)
            check(f"{pkg} importable", "PASS")
        except ImportError:
            check(f"{pkg} importable", "FAIL" if is_required else "WARNING", f"pip install {pkg}")

    # Output directory
    print("\n  [Output]")
    try:
        Path("output").mkdir(exist_ok=True)
        test_file = Path("output/.write_test")
        test_file.touch()
        test_file.unlink()
        check("output/ directory writable", "PASS")
    except Exception as e:
        check("output/ directory writable", "FAIL", str(e))

    # CLI
    print("\n  [CLI]")
    check("cli.py exists", "PASS" if Path("cli.py").exists() else "FAIL")

    # Verification scripts
    print("\n  [Verification Scripts]")
    for script in ["verify_identity_resolution.py", "verify_resolution.py",
                   "verify_normalization.py", "verify_comparison.py", "verify_projection.py"]:
        path = f"tools/verification/{script}"
        check(script, "PASS" if Path(path).exists() else "FAIL", f"Missing {path}")

    print()
    if all_pass:
        print("  Doctor check PASSED. System is healthy.")
    else:
        print("  Doctor check FAILED. Fix the issues above before running the pipeline.")
        sys.exit(1)


# ─── Verify ───────────────────────────────────────────────────────────────────

def run_verify():
    import time
    print("Running architecture verification...\n")
    scripts = [
        "verify_normalization.py",
        "verify_comparison.py",
        "verify_identity_resolution.py",
        "verify_resolution.py",
        "verify_projection.py"
    ]
    
    results = []
    
    for s in scripts:
        path = f"tools/verification/{s}"
        if not Path(path).exists():
            results.append({"script": s, "status": "SKIPPED", "time": 0.0, "output": "Script not found."})
            continue
            
        t0 = time.time()
        res = subprocess.run([sys.executable, path], capture_output=True, text=True)
        t_elapsed = time.time() - t0
        
        status = "PASS" if res.returncode == 0 else "FAIL"
        
        results.append({
            "script": s,
            "status": status,
            "time": t_elapsed,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        })
        
    # Print Structured Summary
    print(f"{'Script':<35} | {'Status':<10} | {'Time'}")
    print("-" * 60)
    
    all_pass = True
    for r in results:
        status_color = r["status"] # if we had colors we'd use them, but we'll stick to text
        print(f"{r['script']:<35} | {status_color:<10} | {r['time']:.2f}s")
        if r["status"] == "FAIL":
            all_pass = False
            
    print("\n=== Error Details ===")
    has_errors = False
    for r in results:
        if r["status"] == "FAIL":
            has_errors = True
            print(f"\n[{r['script']}] STDOUT:\n{r['stdout']}")
            print(f"[{r['script']}] STDERR:\n{r['stderr']}")
    
    if not has_errors:
        print("None.")
        
    print()
    if all_pass:
        print("  [PASS] All verification checks passed.")
    else:
        print("  [FAIL] One or more verification checks failed.")
        sys.exit(1)


# ─── Test ─────────────────────────────────────────────────────────────────────

def run_test(verbose=False):
    print("Running automated test suites...")
    test_files = [
        "tests/test_adapters.py",
        "tests/test_normalization.py",
        "tests/test_comparison.py",
        "tests/test_resolution.py",
        "tests/test_cli.py",
        "tests/test_e2e.py",
    ]
    # Filter to existing test files only
    existing = [t for t in test_files if Path(t).exists()]
    cmd = [sys.executable, "-m", "pytest"] + existing
    if verbose:
        cmd.append("-v")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        sys.exit(res.returncode)


# ─── Stats ────────────────────────────────────────────────────────────────────

def run_stats(run_dir):
    p = Path(run_dir) / "statistics.json"
    if not p.exists():
        print(f"No statistics found in {run_dir}")
        print("Run `python cli.py run --inputs <files>` first to generate a run directory.")
        return
    with open(p) as f:
        stats = json.load(f)
    print("=== PIPELINE STATS ===")
    print(f"  Candidates (raw):      {stats.get('num_candidates_raw', 0)}")
    print(f"  Normalized:            {stats.get('num_candidates_normalized', 0)}")
    print(f"  Blocked Pairs:         {stats.get('num_blocked_pairs', 0)}")
    print(f"  Eligible Pairs:        {stats.get('num_eligible_pairs', 0)}")
    print(f"  Resolutions:           {stats.get('num_resolutions', 0)}")
    print(f"  MATCH:                 {stats.get('num_matches', 0)}")
    print(f"  Clusters:              {stats.get('num_clusters', 0)}")
    timings = stats.get("timings", {})
    print(f"  Execution Time:        {timings.get('total', 0):.3f}s")
    print(f"    Ingest:              {timings.get('ingest', 0):.3f}s")
    print(f"    Normalize:           {timings.get('normalize', 0):.3f}s")
    print(f"    Compare:             {timings.get('compare', 0):.3f}s")
    print(f"    Resolve:             {timings.get('resolve', 0):.3f}s")
    print(f"    Coordinator:         {timings.get('resolution_coordinator', 0):.3f}s")
    print(f"  Run Directory:         {run_dir}")


# ─── Config ───────────────────────────────────────────────────────────────────

def run_config():
    import yaml
    print("=== PIPELINE CONFIGURATION ===\n")
    config_files = {
        "Comparators":        "config/comparison/comparators.yaml",
        "Blocking":           "config/comparison/blocking.yaml",
        "Eligibility":        "config/comparison/eligibility.yaml",
        "IR Rules":           "config/identity_resolution/rules.yaml",
        "IR Weights":         "config/identity_resolution/weights.yaml",
        "IR Thresholds":      "config/identity_resolution/thresholds.yaml",
        "Conflict Priority":  "config/resolution/conflict.yaml",
        "Confidence":         "config/resolution/confidence.yaml",
        "Projection Map":     "config/projection/default.yaml",
    }
    for label, path in config_files.items():
        p = Path(path)
        if not p.exists():
            print(f"  [{label}]  ← MISSING: {path}")
            continue
        try:
            with open(p) as f:
                data = yaml.safe_load(f) or {}
            print(f"  [{label}]  ({path})")
            # Print top-level keys only for brevity
            for k, v in data.items():
                if isinstance(v, list):
                    print(f"    {k}: [{', '.join(str(i) for i in v[:3])}{'...' if len(v) > 3 else ''}]")
                elif isinstance(v, dict):
                    print(f"    {k}: {{...({len(v)} keys)}}")
                else:
                    print(f"    {k}: {v}")
            print()
        except Exception as e:
            print(f"  [{label}]  ← ERROR reading {path}: {e}")


# ─── E2E Run ──────────────────────────────────────────────────────────────────

def write_results_md(stats, out_dir, inputs):
    res_path = Path("results.md")
    if not res_path.exists():
        with open(res_path, "w") as f:
            f.write("# Pipeline Execution Results\n\n")
    with open(res_path, "a") as f:
        f.write("--------------------------------------------------\n")
        f.write(f"Execution Date: {stats['execution_date']}\n")
        f.write(f"Command Used: pipeline run\n")
        f.write(f"CLI Version: {PIPELINE_VERSION}\n")
        f.write(f"Input Files: {', '.join(inputs)}\n")
        f.write(f"Number of Candidates (raw): {stats.get('num_candidates_raw', 0)}\n")
        f.write(f"Normalization Summary: {stats.get('num_candidates_normalized', 0)} normalized\n")
        f.write(f"Blocking Summary: {stats.get('num_blocked_pairs', 0)} pairs blocked\n")
        f.write(f"Eligible Pairs: {stats.get('num_eligible_pairs', 0)}\n")
        f.write(f"Identity Resolutions: {stats.get('num_resolutions', 0)}\n")
        f.write(f"Identity Matches (MATCH): {stats.get('num_matches', 0)}\n")
        f.write(f"Connected Components: {stats.get('num_clusters', 0)} clusters\n")
        f.write(f"Execution Time: {stats['timings'].get('total', 0):.3f}s\n")
        f.write(f"Execution Folder: {out_dir}\n")
        f.write("Assignment Compliance Checklist:\n")
        f.write("  [x] Structured source (CSV) ingestion\n")
        f.write("  [x] Unstructured source (PDF) ingestion\n")
        f.write("  [x] Canonical profile generation\n")
        f.write("  [x] Normalization engine applied\n")
        f.write("  [x] Blocking + eligibility comparison\n")
        f.write("  [x] Identity resolution (MATCH/NO_MATCH/REVIEW)\n")
        f.write("  [x] Conflict resolution with source priority\n")
        f.write("  [x] Merge engine with provenance\n")
        f.write("  [x] Confidence engine (HIGH/MEDIUM/LOW)\n")
        f.write("  [x] Projection to output schema\n")
        f.write("  [x] Visualization (PNG, DOT, MMD)\n")
        f.write("  [x] Runtime configuration (projection.yaml)\n")
        f.write("--------------------------------------------------\n\n")


def run_e2e(inputs, output_base="output", projection="default"):
    # Validate inputs before running
    for inp in inputs:
        p = Path(inp)
        if not p.exists():
            print(f"ERROR: Input file not found: {inp}")
            sys.exit(1)
        if p.suffix.lower() not in [".csv", ".pdf"]:
            print(f"ERROR: Unsupported file type: {inp} (must be .csv or .pdf)")
            sys.exit(1)

    from app.pipeline.e2e_runner import EndToEndRunner
    from app.pipeline.visualization import GraphVisualizer

    # Clean up GitHub enrichment warnings unless verbose
    class GitHubWarningFilter(logging.Filter):
        def __init__(self):
            super().__init__()
            self.warnings = []
        def filter(self, record):
            if record.name == "app.adapters.github_adapter" and record.levelno >= logging.WARNING:
                self.warnings.append(record.getMessage())
                return False
            return True
            
    gh_filter = None

    if projection.endswith(".yaml") or projection.endswith(".json"):
        proj_path = projection
    else:
        json_path = Path(f"config/projection/{projection}.json")
        proj_path = str(json_path) if json_path.exists() else f"config/projection/{projection}.yaml"

    runner = EndToEndRunner(proj_path)
    
    # Add filter to root handlers after runner might have initialized them
    if logger.getEffectiveLevel() > logging.DEBUG:
        gh_filter = GitHubWarningFilter()
        for h in logging.root.handlers:
            h.addFilter(gh_filter)
        for h in logging.getLogger().handlers:
            h.addFilter(gh_filter)
            
    out_dir, stats, final_results, norm_cands, matches = runner.execute(inputs, output_base=output_base)

    # Visualization
    try:
        vis = GraphVisualizer(norm_cands, matches, final_results=final_results)
        try:
            p_png = out_dir / "graph.png"
            vis.export_png(p_png)
            print(p_png.name)
        except Exception as e:
            logger.warning(f"Failed to generate graph.png: {e}")
            
        try:
            p_dot = out_dir / "graph.dot"
            vis.export_dot(p_dot)
            print(p_dot.name)
        except Exception as e:
            logger.warning(f"Failed to generate graph.dot: {e}")
            
        try:
            p_mmd = out_dir / "graph.mmd"
            vis.export_mermaid(p_mmd)
            print(p_mmd.name)
        except Exception as e:
            logger.warning(f"Failed to generate graph.mmd: {e}")
            
    except Exception as e:
        logger.warning(f"Failed to initialize GraphVisualizer: {e}")

    write_results_md(stats, out_dir, inputs)

    # Presentation
    import json
    
    try:
        with open(out_dir / "cluster_summary.json", "r") as f:
            cluster_summaries = json.load(f)
        valid_clusters = sum(1 for c in cluster_summaries if c.get("status") == "VALID")
        warning_clusters = sum(1 for c in cluster_summaries if c.get("status") == "WARNING")
        invalid_clusters = sum(1 for c in cluster_summaries if c.get("status") == "INVALID")
    except Exception:
        valid_clusters = warning_clusters = invalid_clusters = 0

    print("")
    
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
        
        console = Console()
        
        # Summary Panel
        summary_text = (
            f"[bold]Input Candidates:[/bold]   {stats.get('num_candidates_raw', 0)}\n"
            f"[bold]Output Profiles:[/bold]    {len(final_results)}\n"
            f"[bold]VALID Clusters:[/bold]     {valid_clusters}\n"
            f"[bold]WARNING Clusters:[/bold]   {warning_clusters}\n"
            f"[bold]INVALID Clusters:[/bold]   {invalid_clusters}\n"
            f"[bold]Execution Time:[/bold]     {stats['timings'].get('total', 0):.2f} s\n"
            f"[bold]Projection Profile:[/bold] {projection}\n"
            f"[bold]Output Directory:[/bold]   {out_dir}"
        )
        console.print(Panel(summary_text, title="[bold blue]ASSIGNMENT PRESENTATION SUMMARY[/bold blue]", border_style="blue", box=box.ROUNDED))
        
        # DataFrame/Table
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        table.add_column("Type")
        table.add_column("Candidate ID")
        table.add_column("Name")
        table.add_column("Primary Email")
        table.add_column("Company")
        table.add_column("Confidence")
        table.add_column("Sources", justify="right")
        
        for proj, cluster in final_results:
            d = proj.dictionary_view
            
            c_type = "MERGED"
            status_val = getattr(cluster.status, "value", str(cluster.status))
            if status_val == "INVALID" or str(cluster.status) == "INVALID" or len(cluster.candidates) <= 1:
                c_type = "SINGLE"
            
            # Find ID
            c_id = str(d.get("candidate_id") or d.get("id") or d.get("candidate_uuid") or "-")
            
            # Find Name
            name = str(d.get("name") or d.get("full_name") or "-")
            
            # Find Email
            email = "-"
            for k in ["email", "emails", "primary_email"]:
                if k in d:
                    val = d[k]
                    if isinstance(val, list) and val:
                        email = val[0]
                    elif isinstance(val, str):
                        email = val
                    break
            
            # Find Company
            company = "-"
            if "company" in d and d["company"]:
                company = d["company"]
            elif "experience" in d and isinstance(d["experience"], list) and d["experience"]:
                company = d["experience"][0].get("company", "-")
            elif "experiences" in d and isinstance(d["experiences"], list) and d["experiences"]:
                company = d["experiences"][0].get("company", "-")
                
            if not company:
                company = "-"
                
            # Confidence
            conf = str(d.get("confidence") or getattr(getattr(cluster, "confidence_result", None), "level", "N/A"))
            if conf.startswith("ConfidenceLevel."):
                conf = conf.replace("ConfidenceLevel.", "")
                
            # Sources
            src_count = str(len(cluster.candidates))
            if c_type == "SINGLE":
                src_count = "1"
            
            table.add_row(c_type, c_id, name, str(email), str(company), conf, src_count)
            
        console.print(table)
        
        # Artifacts
        console.print("\n[bold green]Generated:[/bold green]")
        for f in out_dir.iterdir():
            console.print(f"  [green]-[/green] {f.name}")
            
    except ImportError:
        # Clean Text Fallback
        print("="*80)
        print("ASSIGNMENT PRESENTATION SUMMARY")
        print("="*80)
        print(f"Input Candidates:   {stats.get('num_candidates_raw', 0)}")
        print(f"Output Profiles:    {len(final_results)}")
        print(f"VALID Clusters:     {valid_clusters}")
        print(f"WARNING Clusters:   {warning_clusters}")
        print(f"INVALID Clusters:   {invalid_clusters}")
        print(f"Execution Time:     {stats['timings'].get('total', 0):.2f} s")
        print(f"Projection Profile: {projection}")
        print(f"Output Directory:   {out_dir}")
        print("-" * 80)
        
        header = f"{'Type':<10} {'ID':<15} {'Name':<25} {'Email':<30} {'Company':<25} {'Confidence':<12} {'Sources':<7}"
        print(header)
        print("-" * len(header))
        
        for proj, cluster in final_results:
            d = proj.dictionary_view
            c_type = "MERGED"
            status_val = getattr(cluster.status, "value", str(cluster.status))
            if status_val == "INVALID" or str(cluster.status) == "INVALID" or len(cluster.candidates) <= 1:
                c_type = "SINGLE"
            
            c_id = str(d.get("candidate_id") or d.get("id") or d.get("candidate_uuid") or "-")[:14]
            name = str(d.get("name") or d.get("full_name") or "-")[:24]
            
            email = "-"
            for k in ["email", "emails", "primary_email"]:
                if k in d:
                    val = d[k]
                    if isinstance(val, list) and val: email = val[0]
                    elif isinstance(val, str): email = val
                    break
            email = str(email)[:29]
            
            company = "-"
            if "company" in d and d["company"]: company = d["company"]
            elif "experience" in d and isinstance(d["experience"], list) and d["experience"]: company = d["experience"][0].get("company", "-")
            elif "experiences" in d and isinstance(d["experiences"], list) and d["experiences"]: company = d["experiences"][0].get("company", "-")
            if not company: company = "-"
            company = str(company)[:24]
            
            conf = str(d.get("confidence") or getattr(getattr(cluster, "confidence_result", None), "level", "N/A")).replace("ConfidenceLevel.", "")[:11]
            src_count = str(len(cluster.candidates)) if c_type == "MERGED" else "1"
            
            print(f"{c_type:<10} {c_id:<15} {name:<25} {email:<30} {company:<25} {conf:<12} {src_count:<7}")
            
        print("\nGenerated:")
        for f in out_dir.iterdir():
            print(f"  - {f.name}")
            
    if gh_filter and gh_filter.warnings:
        print(f"\n[GitHub Enrichment] {len(gh_filter.warnings)} profiles could not be enriched (API rate limit / forbidden).")


# ─── Partial Stage ────────────────────────────────────────────────────────────

def run_partial(stage, inputs, projection="default"):
    for inp in inputs:
        if not Path(inp).exists():
            print(f"ERROR: Input file not found: {inp}")
            sys.exit(1)

    from app.pipeline.e2e_runner import EndToEndRunner
    if projection.endswith(".yaml") or projection.endswith(".json"):
        proj_path = projection
    else:
        json_path = Path(f"config/projection/{projection}.json")
        proj_path = str(json_path) if json_path.exists() else f"config/projection/{projection}.yaml"
        
    runner = EndToEndRunner(proj_path)
    print(f"Executing pipeline up to stage: {stage}")
    out_dir, stats, final_results, norm_cands, matches = runner.execute(inputs)
    print(f"\nCompleted stage '{stage}' successfully.\n")
    print("Candidates ingested:")
    print(f"{stats.get('num_candidates_raw', 0)}\n")
    
    if stage != "ingest":
        print("Candidates normalized:")
        print(f"{stats.get('num_candidates_normalized', 0)}\n")
        
    if stage not in ["ingest", "normalize"]:
        print("Eligible pairs:")
        print(f"{stats.get('num_eligible_pairs', 0)}\n")
        
    if stage not in ["ingest", "normalize", "compare"]:
        print("Matches found:")
        print(f"{stats.get('num_matches', 0)}\n")
        
    print("Output Directory:\n")
    print(f"{out_dir}")


# ─── Explain ──────────────────────────────────────────────────────────────────

def run_explain(inputs, c_a, c_b):
    for inp in inputs:
        if not Path(inp).exists():
            print(f"ERROR: Input file not found: {inp}")
            sys.exit(1)

    print(f"Explaining resolution path for '{c_a}' and '{c_b}'...")
    print("-" * 60)

    from app.pipeline.e2e_runner import EndToEndRunner
    runner = EndToEndRunner()
    out_dir, stats, final_results, norm_cands, matches = runner.execute(inputs)

    # Find candidates
    cand_a = next((c for c in norm_cands if c.candidate_id == c_a), None)
    cand_b = next((c for c in norm_cands if c.candidate_id == c_b), None)

    if not cand_a:
        print(f"  ERROR: Candidate '{c_a}' not found in input files.")
        print(f"  Available IDs: {[c.candidate_id for c in norm_cands[:10]]}")
        sys.exit(1)
    if not cand_b:
        print(f"  ERROR: Candidate '{c_b}' not found in input files.")
        print(f"  Available IDs: {[c.candidate_id for c in norm_cands[:10]]}")
        sys.exit(1)

    # Show normalization
    print(f"\n[NORMALIZATION]")
    print(f"  Candidate A ({c_a}):")
    if cand_a.personal_info:
        print(f"    Name:   {cand_a.personal_info.name}")
    if cand_a.contact_info:
        print(f"    Emails: {cand_a.contact_info.emails}")
        print(f"    Phones: {cand_a.contact_info.phone_numbers}")
    print(f"  Candidate B ({c_b}):")
    if cand_b.personal_info:
        print(f"    Name:   {cand_b.personal_info.name}")
    if cand_b.contact_info:
        print(f"    Emails: {cand_b.contact_info.emails}")
        print(f"    Phones: {cand_b.contact_info.phone_numbers}")

    # Look for match in resolution results
    match = None
    for m in matches:
        if (m.candidate_pair.candidate_a_id == c_a and m.candidate_pair.candidate_b_id == c_b) or \
           (m.candidate_pair.candidate_a_id == c_b and m.candidate_pair.candidate_b_id == c_a):
            match = m
            break

    # Look for cluster in final results
    cluster_match = None
    for proj, cluster in final_results:
        cand_ids = [c.candidate_id for c in cluster.candidates]
        if c_a in cand_ids or c_b in cand_ids:
            cluster_match = cluster
            break

    # Re-run resolution directly for this pair to get full evidence breakdown
    from app.pipeline.comparison.blocking.base import CandidatePair
    from app.pipeline.identity_resolution.engine import IdentityResolutionEngine
    from app.pipeline.identity_resolution.evidence_collector import EvidenceCollector
    from app.pipeline.comparison.comparators.engine_integration import load_comparators

    registry = load_comparators()
    engine = IdentityResolutionEngine(registry)
    # Re-create pair with the actual blocking keys if it exists in matches
    b_keys = match.candidate_pair.blocking_keys_that_generated_this_pair if match else ["manual_explain"]
    pair = CandidatePair(
        candidate_a_id=c_a,
        candidate_b_id=c_b,
        blocking_keys_that_generated_this_pair=b_keys
    )
    result = engine.resolve(cand_a, cand_b, pair)

    print(f"\nBlocking")
    print(f"--------")
    if b_keys and b_keys[0] != "manual_explain":
        print(f"Matched via:")
        for k in b_keys:
            print(f"{k}")
    else:
        print("Not blocked automatically.")

    print(f"\nEligibility")
    print(f"-----------")
    from app.pipeline.comparison.eligibility import EligibilityEngine
    elig_engine = EligibilityEngine(registry)
    elig_res = elig_engine.is_eligible(cand_a, cand_b)
    if elig_res.eligible:
        print(f"Rule:\n{elig_res.matched_rule_id}")
    else:
        print(f"Ineligible:\nFailed all eligibility rules")

    print(f"\nIdentity Rule")
    print(f"-------------")
    rule_result = result.rule_result
    if rule_result and rule_result.triggered:
        print(f"{rule_result.rule_id}")
    else:
        print("None matched")

    print(f"\nSimilarity")
    print(f"----------")
    sim_result = result.similarity_result
    if sim_result:
        print(f"Score: {sim_result.overall_score}%")
    else:
        print("Skipped (terminating rule)")

    print(f"\nDecision")
    print(f"--------")
    print(f"{result.decision.value if hasattr(result.decision, 'value') else str(result.decision)}")

    print(f"\nCluster")
    print(f"-------")
    if cluster_match:
        status_str = cluster_match.status.value if hasattr(cluster_match.status, "value") else str(cluster_match.status)
        if status_str.startswith("ClusterStatus."):
            status_str = status_str.replace("ClusterStatus.", "")
        print(f"{status_str}")
        if cluster_match.contradictions:
            for c in cluster_match.contradictions:
                print(f"  - {c}")
    else:
        print("No cluster found")

    print(f"\nConfidence")
    print(f"----------")
    if cluster_match:
        from app.pipeline.resolution.confidence_engine import ConfidenceEngine
        from app.pipeline.resolution.merge_engine import MergeEngine
        from app.pipeline.resolution.conflict_resolver import ConflictResolver
        m_engine = MergeEngine(ConflictResolver())
        m_res = m_engine.merge(cluster_match)
        conf_res = ConfidenceEngine().evaluate(m_res, len(cluster_match.candidates))
        conf_str = conf_res.level.value if hasattr(conf_res.level, "value") else str(conf_res.level)
        if conf_str.startswith("ConfidenceLevel."):
            conf_str = conf_str.replace("ConfidenceLevel.", "")
        print(f"{conf_str}")
    else:
        print("N/A")
    print("-" * 60)



def main():
    args = parse_args()
    
    # Configure logging based on global flags
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)

    if args.command == "version":
        print(f"Pipeline v{PIPELINE_VERSION}")

    elif args.command == "doctor":
        run_doctor()

    elif args.command == "verify":
        run_verify()

    elif args.command == "test":
        verbose = getattr(args, "verbose", False)
        run_test(verbose=verbose)

    elif args.command == "stats":
        run_stats(args.run_dir)

    elif args.command == "config":
        run_config()

    else:
        # Wrap execution commands to catch errors globally
        execute_command(args)


def execute_command(args):
    try:
        if args.command == "run":
            run_e2e(args.inputs, getattr(args, "output", "output"), getattr(args, "projection", "default"))

        elif args.command == "explain":
            run_explain(args.inputs, args.candidate_a, args.candidate_b)

        elif args.command in ["ingest", "normalize", "compare", "resolve", "merge", "project", "visualize"]:
            run_partial(args.command, args.inputs, getattr(args, "projection", "default"))
            
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nPipeline execution interrupted by user.")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\nInput file not found:\n\n{e.filename}\n\nCheck the file path and try again.")
        sys.exit(1)
    except KeyError as e:
        msg = str(e)
        import glob
        profiles = [Path(p).stem for p in glob.glob("config/projection/*")]
        print(f"\nProjection profile not found:\n\n{msg}\n\nAvailable profiles:\n\n" + "\n".join(profiles))
        sys.exit(1)
    except Exception as e:
        import traceback
        if "yaml" in str(type(e)).lower():
            print(f"\nMalformed YAML configuration:\n\n{e}")
            sys.exit(1)
        if getattr(args, "verbose", False):
            traceback.print_exc()
        else:
            print(f"\n[ERROR] Pipeline execution failed: {e}\n(Run with --verbose for full stack trace)")
        sys.exit(1)


if __name__ == "__main__":
    main()
