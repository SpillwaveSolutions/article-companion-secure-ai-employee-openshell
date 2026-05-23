# flow.py -- Competitive Research Assistant Flow
#
# Fetches a target company URL, uses Google to find competitors,
# and writes a CSV report of the competitive landscape.
#
# Requires: crewai>=1.14.4 with anthropic extra, crewai-tools>=1.14.4
# Runtime: OpenShell with research-policy.yaml
#
# LLM calls go through the OpenShell privacy router at
# https://inference.local. The router injects the real API key
# and rewrites the model to whatever `openshell inference set` configured.

import csv
import json
import os

from crewai import Agent, Crew, Task, LLM
from crewai.flow.flow import Flow, listen, start
from crewai_tools import ScrapeWebsiteTool, SerperDevTool

ALLOWED_DOMAINS = {"spillwave.ai"}

OUTPUT_CSV = "competitors.csv"
CSV_COLUMNS = ["url", "name", "competitive_overlap", "description"]


def _get_llm():
    """Create an LLM routed through the OpenShell privacy router."""
    os.environ.setdefault("ANTHROPIC_API_KEY", "unused")
    return LLM(
        model="anthropic/claude-sonnet-4-20250514",
        base_url="https://inference.local",
    )


def _create_scout():
    """Create the Company Scout agent that scrapes the target URL."""
    return Agent(
        role="Company Scout",
        goal=(
            "Scrape the target company's website and extract a clear summary "
            "of what the company does, its key products, and target market."
        ),
        backstory=(
            "You are a competitive intelligence analyst. You read company "
            "websites and distill them into structured briefs that a "
            "strategist can act on."
        ),
        tools=[ScrapeWebsiteTool()],
        llm=_get_llm(),
    )


def _create_competitor_finder():
    """Create the Competitor Finder agent that searches Google."""
    return Agent(
        role="Competitor Finder",
        goal=(
            "Given a company summary, search Google to find 5-10 competing "
            "companies. For each competitor, return the company name, URL, "
            "a one-sentence description, and a brief note on competitive "
            "overlap with the target company."
        ),
        backstory=(
            "You are a market research specialist who identifies competitive "
            "landscapes. You search methodically and distinguish direct "
            "competitors from adjacent players. You always return structured "
            "JSON output."
        ),
        tools=[SerperDevTool()],
        llm=_get_llm(),
    )


class ResearchFlow(Flow):
    @start()
    def choose_url(self):
        """Ask the human which company URL to research."""
        url = self.ask(
            message=(
                "Which company URL should I research for competitors? "
                f"Allowed domains: {', '.join(sorted(ALLOWED_DOMAINS))}"
            ),
            timeout=300,
        )
        self.state["url"] = url
        return url

    @listen(choose_url)
    def scout_company(self, url):
        """Scrape the target URL and produce a company summary."""
        scout = _create_scout()
        task = Task(
            description=(
                f"Scrape {url} and produce a structured summary: "
                "company name, what they do, key products/services, "
                "target market, and differentiators."
            ),
            agent=scout,
            expected_output="A structured company summary in plain text.",
        )
        crew = Crew(agents=[scout], tasks=[task])
        result = crew.kickoff()
        self.state["company_summary"] = str(result)
        return str(result)

    @listen(scout_company)
    def find_competitors(self, company_summary):
        """Search Google for competitors and produce a CSV report."""
        finder = _create_competitor_finder()
        task = Task(
            description=(
                f"Using this company summary:\n\n{company_summary}\n\n"
                "Search Google for 5-10 competing companies.\n\n"
                "Return ONLY a JSON array. Each element must have exactly "
                "these four keys:\n"
                '  "url": the competitor\'s website URL\n'
                '  "name": the company name\n'
                '  "competitive_overlap": one sentence on how they compete\n'
                '  "description": one sentence on what the competitor does\n\n'
                "Example output:\n"
                '[{"url":"https://example.com","name":"Example Corp",'
                '"competitive_overlap":"Both offer AI consulting",'
                '"description":"Enterprise AI platform"}]\n\n'
                "Return ONLY the JSON array, no other text."
            ),
            agent=finder,
            expected_output="A JSON array of competitor objects.",
        )
        crew = Crew(agents=[finder], tasks=[task])
        result = crew.kickoff()

        # Parse JSON output from the LLM
        raw = str(result).strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

        rows = []
        try:
            competitors = json.loads(raw)
            if isinstance(competitors, list):
                for c in competitors:
                    if isinstance(c, dict) and "url" in c and "name" in c:
                        rows.append([
                            c.get("url", ""),
                            c.get("name", ""),
                            c.get("competitive_overlap", ""),
                            c.get("description", ""),
                        ])
        except json.JSONDecodeError:
            # Fallback: try CSV parsing
            reader = csv.reader(io.StringIO(raw))
            rows = [row[:4] for row in reader if len(row) >= 4]

        with open(OUTPUT_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)
            writer.writerows(rows)

        self.state["csv_path"] = OUTPUT_CSV
        self.state["competitor_count"] = len(rows)
        return OUTPUT_CSV


if __name__ == "__main__":
    flow = ResearchFlow()
    result = flow.kickoff()
    count = flow.state.get("competitor_count", 0)
    print(f"Wrote {count} competitors to {result}")
    if count > 0:
        with open(OUTPUT_CSV) as f:
            print(f.read())
