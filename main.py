"""
🪔 Diwali Sale Analytics — Master Orchestrator
=================================================
One-command entry point to run the entire project pipeline.

Usage:
    python main.py generate    → Generate synthetic star-schema data
    python main.py pipeline    → Run ETL pipeline (profile → clean → validate)
    python main.py analyze     → Run statistical analysis + EDA
    python main.py dashboard   → Launch Streamlit dashboard
    python main.py all         → Run generate + pipeline + analyze
    python main.py full        → Run all + launch dashboard
"""

import os, sys, subprocess, time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def banner():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  🪔  FESTIVE E-COMMERCE SALES ANALYTICS PIPELINE           ║
    ║      Diwali Sale 2025 — Performance Dashboard              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)


def run_step(name, script_path):
    """Run a Python script and report timing."""
    print(f"\n{'━' * 60}")
    print(f"  ▶ {name}")
    print(f"{'━' * 60}\n")
    start = time.time()
    result = subprocess.run([sys.executable, script_path], cwd=PROJECT_ROOT)
    elapsed = round(time.time() - start, 2)
    if result.returncode == 0:
        print(f"\n  ✅ {name} completed in {elapsed}s")
    else:
        print(f"\n  ❌ {name} failed (exit code {result.returncode})")
        sys.exit(1)


def cmd_generate():
    """Generate synthetic star-schema data."""
    run_step("Data Generation (Star Schema)",
             os.path.join(PROJECT_ROOT, "generate_star_schema.py"))


def cmd_pipeline():
    """Run the ETL pipeline."""
    from pipeline.etl_pipeline import ETLPipeline
    pipeline = ETLPipeline()
    success = pipeline.run()
    if not success:
        print("  ❌ Pipeline failed")
        sys.exit(1)


def cmd_analyze():
    """Run statistical analysis."""
    from analysis.statistical_analysis import StatisticalAnalyzer
    analyzer = StatisticalAnalyzer()
    analyzer.run()
    analyzer.generate_eda_summary()


def cmd_dashboard():
    """Launch the Streamlit dashboard."""
    print("\n  🚀 Launching Streamlit dashboard...")
    print("     Open http://localhost:8501 in your browser\n")
    app_path = os.path.join(PROJECT_ROOT, "dashboard", "app.py")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.headless", "true",
        "--theme.primaryColor", "#FF6F00",
        "--theme.backgroundColor", "#0E1117",
        "--theme.secondaryBackgroundColor", "#1E2A3A",
        "--theme.textColor", "#FAFAFA",
    ])


def cmd_all():
    """Run the full pipeline (generate + ETL + analyze)."""
    banner()
    total_start = time.time()

    print("  Step 1/3: Generating synthetic data...")
    cmd_generate()

    print("\n  Step 2/3: Running ETL pipeline...")
    cmd_pipeline()

    print("\n  Step 3/3: Running statistical analysis...")
    cmd_analyze()

    total_elapsed = round(time.time() - total_start, 2)
    print(f"\n{'═' * 60}")
    print(f"  🎉 ALL STEPS COMPLETE — Total time: {total_elapsed}s")
    print(f"{'═' * 60}")
    print(f"\n  Next: Launch the dashboard with:")
    print(f"    python main.py dashboard")
    print(f"\n  Or open the reports in data/reports/")


def cmd_full():
    """Run everything and launch the dashboard."""
    cmd_all()
    cmd_dashboard()


COMMANDS = {
    "generate":  ("Generate synthetic star-schema data",    cmd_generate),
    "pipeline":  ("Run ETL pipeline (profile→clean→validate)", cmd_pipeline),
    "analyze":   ("Run statistical analysis + EDA",         cmd_analyze),
    "dashboard": ("Launch Streamlit dashboard",             cmd_dashboard),
    "all":       ("Run generate + pipeline + analyze",      cmd_all),
    "full":      ("Run all + launch dashboard",             cmd_full),
}


def print_usage():
    banner()
    print("  Usage: python main.py <command>\n")
    print("  Commands:")
    for cmd, (desc, _) in COMMANDS.items():
        print(f"    {cmd:12s}  {desc}")
    print()
    print("  Typical first run:")
    print("    python main.py all         # Generate data, run pipeline & analysis")
    print("    python main.py dashboard   # Launch interactive dashboard")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    command = sys.argv[1].lower()
    if command in COMMANDS:
        COMMANDS[command][1]()
    elif command in ("help", "--help", "-h"):
        print_usage()
    else:
        print(f"  ❌ Unknown command: '{command}'")
        print_usage()
        sys.exit(1)

