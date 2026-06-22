import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

class ResearchPipeline:
    def __init__(self, storage_path: str = "research_vault"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "insights").mkdir(exist_ok=True)
        (self.storage_path / "reports").mkdir(exist_ok=True)

    async def store_finding(self, agent_id: str, topic: str, content: Any, metadata: Optional[Dict[str, Any]] = None):
        finding_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{agent_id[:8]}"
        finding = {
            "id": finding_id,
            "agent_id": agent_id,
            "topic": topic,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        file_path = self.storage_path / "insights" / f"{finding_id}.json"
        with open(file_path, "w") as f:
            json.dump(finding, f, indent=2)

        return finding_id

    async def query_insights(self, query: str) -> List[Dict[str, Any]]:
        results = []
        # Simple keyword-based query for now
        for file in (self.storage_path / "insights").glob("*.json"):
            with open(file, "r") as f:
                finding = json.load(f)
                if query.lower() in str(finding).lower():
                    results.append(finding)
        return results

    async def generate_report(self, title: str, findings: List[Dict[str, Any]], format: str = "markdown"):
        report_id = f"report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        if format == "markdown":
            report_content = f"# Research Report: {title}\n\n"
            report_content += f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            report_content += "## Key Findings\n\n"

            for f in findings:
                report_content += f"### {f.get('topic', 'Untitled Finding')}\n"
                report_content += f"- **Agent**: {f.get('agent_id')}\n"
                report_content += f"- **Timestamp**: {f.get('timestamp')}\n\n"
                report_content += "#### Content\n"
                report_content += f"```json\n{json.dumps(f.get('content'), indent=2)}\n```\n\n"
                if f.get('metadata'):
                    report_content += "#### Metadata\n"
                    for k, v in f['metadata'].items():
                        report_content += f"- **{k}**: {v}\n"
                    report_content += "\n"
                report_content += "---\n\n"

            file_path = self.storage_path / "reports" / f"{report_id}.md"
            with open(file_path, "w") as f:
                f.write(report_content)
        else:
            file_path = self.storage_path / "reports" / f"{report_id}.json"
            with open(file_path, "w") as f:
                json.dump({"title": title, "findings": findings}, f, indent=2)

        return str(file_path)
