import asyncio
import os
import sys
import json
from pathlib import Path
from typing import List

# Add backend to path so we can import our core modules
sys.path.append(str(Path(__file__).parent.parent))

from agents.avaira_agent import AvairaAgent
from core.research_pipeline import ResearchPipeline

async def analyze_file(agent: AvairaAgent, pipeline: ResearchPipeline, file_path: Path):
    try:
        content = file_path.read_text(errors='ignore')[:4000] # Limit content for analysis
        task = f"Analyze this file for patterns, potential bugs, and architectural significance. File: {file_path}\n\nContent:\n{content}"

        # Run agent 'think' (reasoning)
        intent = await agent.think(task)

        # Store the finding
        await pipeline.store_finding(
            agent_id=agent.agent_id,
            topic=f"File Analysis: {file_path.name}",
            content=intent.model_dump(),
            metadata={"file_path": str(file_path), "size": file_path.stat().st_size}
        )
        print(f"✓ Analyzed: {file_path}")
    except Exception as e:
        print(f"✗ Failed {file_path}: {e}")

async def run_codebase_research(target_dir: str):
    print(f"--- Starting Codebase Research on {target_dir} ---")

    agent = AvairaAgent(
        agent_id="researcher-v2-auto",
        risk_envelope={"allowed_actions": ["analyze_code", "report_finding"], "max_spend_usd": 0.0}
    )
    pipeline = ResearchPipeline(storage_path="research_vault")

    target_path = Path(target_dir)
    files_to_analyze = []

    # Simple walk, ignoring common large/irrelevant dirs
    ignore_dirs = {'.git', 'node_modules', '__pycache__', 'dist', 'build', 'venv', '.next'}

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.tsx', '.go', '.rs', '.java')):
                files_to_analyze.append(Path(root) / file)

    print(f"Found {len(files_to_analyze)} candidate files.")

    # Process in chunks to manage concurrency
    CHUNK_SIZE = 5
    for i in range(0, len(files_to_analyze), CHUNK_SIZE):
        chunk = files_to_analyze[i:i + CHUNK_SIZE]
        tasks = [analyze_file(agent, pipeline, f) for f in chunk]
        await asyncio.gather(*tasks)

    # Generate final report
    findings = await pipeline.query_insights("File Analysis")
    report_path = await pipeline.generate_report("Full Codebase Analysis", findings)
    print(f"\n--- Research Complete ---")
    print(f"Findings stored in research_vault/insights")
    print(f"Full report generated at: {report_path}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    asyncio.run(run_codebase_research(target))
