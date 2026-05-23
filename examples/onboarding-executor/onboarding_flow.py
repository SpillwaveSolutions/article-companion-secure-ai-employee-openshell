# onboarding_flow.py -- CrewAI Flow for the Onboarding Executor
#
# This uses CrewAI's Flow architecture with @start, @listen, and @router
# decorators. The human approval gate uses Flow.ask(), which suspends
# execution until a human responds.
#
# In production, the provisioner Crew runs inside an OpenShell sandbox
# specified by onboarding-policy.yaml. The Flow itself runs outside the
# sandbox in the orchestrator's privilege domain.
#
# LLM calls go through the OpenShell privacy router at
# https://inference.local (configured via `openshell inference set`).

from crewai.flow.flow import Flow, listen, router, start


class OnboardingFlow(Flow):
    @start()
    def onboard(self):
        """Kick off the onboarding task."""
        self.state["new_hire"] = self.state.get("new_hire", "new-contractor")
        return self.state["new_hire"]

    @listen(onboard)
    def provision_accounts(self, new_hire):
        """Create accounts in the identity provider.

        In production, this delegates to a Crew running inside an OpenShell
        sandbox with scoped credentials (see onboarding-policy.yaml).
        """
        # Placeholder: in production, use sandboxed_run() from the
        # orchestrator-pattern example to spawn a sandboxed sub-agent.
        self.state["account_result"] = "created"
        return self.state["account_result"]

    @router(provision_accounts)
    def check_result(self, result):
        """Route based on whether provisioning succeeded."""
        if result == "created":
            return "approval_required"
        return "failed"

    @listen("approval_required")
    def human_gate(self, _):
        """Suspend until a human approves the account creation.

        Uses Flow.ask() which blocks until human input arrives or timeout.
        """
        response = self.ask(
            message=f"Approve account for {self.state['new_hire']}? (yes/no)",
            timeout=1800,  # 30 minutes in seconds
        )
        self.state["approval"] = response
        return response

    @listen("failed")
    def escalate(self, _):
        """Route failures to a human operator."""
        self.state["escalated"] = True
        return "escalated"

    @listen(human_gate)
    def send_welcome(self, approval):
        """Send the welcome email and finalize audit."""
        if approval and approval.lower() == "yes":
            self.state["welcome_sent"] = True
        self.state["audit_finalized"] = True
        return self.state
