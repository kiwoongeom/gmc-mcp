"""Storefront policy audit tools. No external LLM API or appeal submission."""

from ..client import MerchantClient
from ..policy import PolicyAuditor


def register(mcp, client: MerchantClient) -> None:
    auditor = PolicyAuditor(client)

    @mcp.tool()
    def gmc_run_policy_audit(url: str, max_pages: int = 8, include_account: bool = True) -> dict:
        """Audit public HTTPS storefront policies; persist full downloaded evidence and a heuristic risk score. Not a Google verdict."""
        return auditor.run(url, max_pages, include_account)

    @mcp.tool()
    def gmc_list_policy_audits(limit: int = 20) -> dict:
        """List stored policy audits for the configured Merchant Center account."""
        return auditor.list_audits(limit)

    @mcp.tool()
    def gmc_get_policy_audit(audit_id: str) -> dict:
        """Read a stored policy audit, its risk score, coverage and raw evidence paths."""
        return auditor.get(audit_id)

    @mcp.tool()
    def gmc_get_policy_fix_plan(audit_id: str) -> dict:
        """Prioritize observed missing or unassessed policy checks; a plan is not a completed fix."""
        return auditor.plan(audit_id)

    @mcp.tool()
    def gmc_generate_policy_appeal(audit_id: str, merchant_statement: str = "") -> dict:
        """Create an evidence-linked review-request DRAFT. Statements remain unverified; never submits to Google."""
        return auditor.appeal(audit_id, merchant_statement)

    @mcp.tool()
    def gmc_set_policy_monitoring(url: str, enabled: bool = True) -> dict:
        """Persist or disable weekly policy monitoring. A local policy-monitor-run scheduler is required to execute jobs."""
        return auditor.set_monitor(url, enabled)

    @mcp.tool()
    def gmc_get_policy_monitoring() -> dict:
        """Read weekly schedules, last runs, score changes and locally persisted alerts."""
        return auditor.monitoring()

    @mcp.tool()
    def gmc_run_policy_monitors() -> dict:
        """Execute due weekly policy audits now; a lease prevents concurrent duplicate runs."""
        return auditor.run_due()
