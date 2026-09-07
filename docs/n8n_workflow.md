# n8n Workflow Design for Aegis-Ops

This document describes the logical flow of the n8n workflow that acts as the orchestrator for the self-healing process.

## Workflow Nodes & Logic

1. **Webhook Node (Trigger)**
   - **Endpoint:** `/webhook/k8s-alert`
   - **Input:** Receives JSON payload from Prometheus Alertmanager.
   - **Data Extracted:** `pod_name`, `namespace`, `alert_reason`, `severity`.

2. **HTTP Request Node (Log Fetcher)**
   - **Action:** Calls the Aegis-Ops AI Agent Controller API.
   - **Purpose:** Requests the latest logs and events for the specific pod.
   - **Auth:** Uses internal K8s service token.

3. **AI Agent Node (The Brain)**
   - **Tool:** LangChain / OpenAI GPT-4.
   - **Input:** {logs, events, alert_reason}.
   - **Prompt:** "Analyze these K8s logs and events. Determine if the issue is: A) Resource Exhaustion, B) Configuration Error, or C) Application Crash. Provide a remediation action."
   - **Output:** JSON containing `{ "action": "...", "details": "..." }`.

4. **Decision Node (The Router)**
   - **Branch A (Restart):** If action == 'restart' $\rightarrow$ Call K8s API to delete pod.
   - **Branch B (Scale):** If action == 'scale' $\rightarrow$ Call K8s API to update deployment resources.
   - **Branch C (Escalate):** If action == 'manual' $\rightarrow$ Trigger high-priority alert.

5. **Notification Node (The Reporter)**
   - **Channel:** Slack / Microsoft Teams.
   - **Message:** "🤖 **Aegis-Ops Update:** Pod [Name] failed due to [Reason]. AI analyzed logs and performed [Action]. Status: Resolved."

## Error Handling
- **Retry Logic:** If the AI Agent fails to respond, the workflow triggers a fallback "Manual Intervention" alert to the SRE team.
- **Audit Log:** Every execution is logged to a PostgreSQL database for later analysis and AI fine-tuning.
