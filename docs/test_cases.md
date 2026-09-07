# Aegis-Ops: Validation & Test Cases

To prove the "Self-Healing" capability of Aegis-Ops, the following test scenarios should be executed and recorded.

## Scenario 1: Memory Leak (Resource Exhaustion)
- **Setup:** Deploy a pod with very low memory limits. Run a script that consumes memory rapidly.
- **Expected Behavior:**
    1. Prometheus detects `OOMKilled`.
    2. Webhook triggers n8n $\rightarrow$ AI Agent.
    3. AI Agent identifies "Out of Memory" from logs/events.
    4. AI Agent triggers a `scale` action to increase memory limits.
- **Success Criterion:** Pod returns to `Running` state with increased limits without manual intervention.

## Scenario 2: Configuration Error (CrashLoopBackOff)
- **Setup:** Update a ConfigMap with an invalid value that causes the application to crash on startup.
- **Expected Behavior:**
    1. Prometheus detects `CrashLoopBackOff`.
    2. AI Agent analyzes logs and finds "Invalid configuration at line X".
    3. AI Agent suggests a rollback or a specific config fix.
- **Success Criterion:** The system identifies the exact config error and notifies the engineer with the corrected value.

## Scenario 3: Dependency Failure (External API Down)
- **Setup:** Block network access to a required external API.
- **Expected Behavior:**
    1. Pod logs show `Connection Timeout` or `503 Service Unavailable`.
    2. AI Agent analyzes logs and identifies a network/dependency issue.
    3. AI Agent checks the status of the dependency.
- **Success Criterion:** AI Agent reports "External Dependency [API Name] is down," avoiding unnecessary pod restarts.

## Recording Results for LinkedIn
For each scenario, capture:
1. **The Alert:** Screenshot of the Prometheus alert.
2. **The Thought Process:** Screenshot of the AI Agent's analysis (from n8n logs).
3. **The Resolution:** Screenshot of the fixed pod and the Slack notification.
