# flow.py -- Research Assistant Flow
#
# Minimal viable digital employee: one sandbox, one tool, one approval gate,
# four-level audit logging. Exercises every concept in the article.
#
# Requires: crewai==1.14.4, crewai-tools==1.14.3
# Runtime: OpenShell with sandbox.yaml in the same directory

from crewai import Agent, Crew, Task
from crewai.flow.flow import Flow, listen, start
from crewai_tools import ScrapeWebsiteTool

ALLOWED_DOMAINS = {"docs.example.com", "blog.example.com"}

# LLM backend declared in sandbox.yaml's inference router.
# In production, OpenShell routes this through the privacy router.
# For local testing without OpenShell, override with any supported provider:
#   LLM_BACKEND = "openai/gpt-4o"
LLM_BACKEND = "claude-on-prem://nim-endpoint"


def _create_researcher():
    """Create the Research Assistant agent.

    Deferred to a function so the module can be imported in test environments
    that don't have the on-prem LLM backend available. In production, the
    Agent is created at flow startup inside the OpenShell sandbox.
    """
    return Agent(
        role="Research Assistant",
        goal="Fetch a URL and summarize its content in under 200 words.",
        backstory=(
            "You are a research assistant that fetches web pages and produces "
            "concise summaries. You operate inside an OpenShell sandbox with "
            "restricted egress and audit logging enabled."
        ),
        tools=[ScrapeWebsiteTool()],
        llm=LLM_BACKEND,
    )


class ResearchFlow(Flow):
    @start()
    def choose_url(self):
        """Ask the human which URL to summarize.

        Uses Flow.ask() which suspends until human input arrives.
        The egress allowlist in sandbox.yaml restricts which domains
        the agent can actually reach.
        """
        url = self.ask(
            message=(
                "Which URL should I summarize? "
                f"Allowed: {', '.join(sorted(ALLOWED_DOMAINS))}"
            ),
            timeout=300,  # 5 minutes
        )
        self.state["url"] = url
        return url

    @listen(choose_url)
    def summarize(self, url):
        """Fetch the URL and write a summary.

        The OpenShell sandbox enforces:
        - Egress: only docs.example.com and blog.example.com
        - Filesystem: write only to /var/log/research/${task_id}/
        - Inference: only claude-on-prem://nim-endpoint
        - Audit: all four levels to audit.jsonl
        """
        researcher = _create_researcher()
        task = Task(
            description=f"Fetch {url} and write a summary under 200 words.",
            agent=researcher,
            expected_output="A plain-text summary.",
        )
        crew = Crew(agents=[researcher], tasks=[task])
        result = crew.kickoff()
        self.state["summary"] = str(result)
        return str(result)


if __name__ == "__main__":
    ResearchFlow().kickoff()
