import os
from fastapi import FastAPI, Request, BackgroundTasks
from kubernetes import client, config
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
import requests
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AegisOps-Agent")

app = FastAPI()

# Load K8s Config (In-cluster or local)
try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

v1 = client.CoreV1Api()

# AI Configuration
os.environ["OPENAI_API_KEY"] = "your-api-key-here" # Should be in .env
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)

SYSTEM_PROMPT = """
You are the Aegis-Ops AI Agent, a Senior Site Reliability Engineer (SRE). 
Your goal is to analyze Kubernetes failure events and provide a precise remediation action.
You have access to Pod logs and events. 

Your response must be in JSON format:
{
    "analysis": "Brief root cause analysis",
    "action": "restart | scale | update_config | manual_intervention",
    "target": "pod_name",
    "details": "Specific value or command to execute"
}
"""

async def remediate_issue(payload: dict):
    pod_name = payload.get("pod")
    namespace = payload.get("namespace", "default")
    alert_reason = payload.get("reason", "Unknown Failure")

    logger.info(f"Analyzing failure for pod {pod_name} in {namespace}. Reason: {alert_reason}")

    # 1. Fetch Logs and Events
    try:
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail=100)
        events = v1.list_namespaced_event(namespace=namespace, field_selector=f"involvedObject.name={pod_name}")
        event_text = "\n".join([e.message for e in events.items])
    except Exception as e:
        logger.error(f"Failed to fetch K8s data: {e}")
        return

    # 2. AI Analysis
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", f"Pod: {pod_name}\nReason: {alert_reason}\nLogs: {logs}\nEvents: {event_text}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({})
    
    # In a real scenario, we parse the JSON response from LLM
    # For this showcase, we simulate the remediation logic based on the 'action'
    try:
        import json
        result = json.loads(response.content)
        action = result.get("action")
        
        if action == "restart":
            logger.info(f"Executing Restart for {pod_name}...")
            v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        elif action == "scale":
            logger.info(f"Updating resources for {pod_name}...")
            # Logic to update resource limits via Patch
        else:
            logger.info(f"Manual intervention required: {result.get('analysis')}")

        # 3. Report to Teams/Slack
        send_notification(f"✅ Aegis-Ops remediated {pod_name}. Analysis: {result.get('analysis')}")
    except Exception as e:
        logger.error(f"AI Remediation failed: {e}")

def send_notification(message):
    # Mock notification function
    logger.info(f"NOTIFICATION: {message}")

@app.post("/webhook")
async def k8s_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    # Expecting payload from Prometheus Alertmanager
    pod = payload.get("labels", {}).get("pod", "unknown")
    namespace = payload.get("labels", {}).get("namespace", "default")
    reason = payload.get("annotations", {}).get("summary", "Pod Failure")
    
    background_tasks.add_task(remediate_issue, {"pod": pod, "namespace": namespace, "reason": reason})
    return {"status": "received", "action": "analyzing"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
