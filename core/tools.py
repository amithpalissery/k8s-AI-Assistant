from kubernetes import client, config
from langchain_core.tools import tool
import os

# Load Kubernetes configuration
try:
    config.load_incluster_config()
    print("Loaded in-cluster Kubernetes config.")
except config.ConfigException:
    print("Not running in-cluster, loading local kubeconfig.")
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

@tool
def list_pods(namespace: str = "all") -> str:
    """
    Lists pod names in a namespace (or all namespaces).
    Returns only pod names, one per line.
    """
    try:
        if namespace.lower() == "all":
            ret = v1.list_pod_for_all_namespaces(watch=False)
        else:
            ret = v1.list_namespaced_pod(namespace=namespace, watch=False)

        pod_names = [i.metadata.name for i in ret.items]
        return "\n".join(pod_names) if pod_names else f"No pods found in namespace '{namespace}'."
    except client.ApiException as e:
        return f"Error: Failed to list pods. Details: {e.reason}"

@tool
def get_pod_details(pod_name: str, namespace: str) -> str:
    """
    Retrieves concise details about a pod:
    - Name
    - Namespace
    - Status
    - Node
    - Containers and their states
    """
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)

        # Containers
        containers = [c.name for c in (pod.spec.containers or [])]

        # Container statuses
        statuses = []
        if pod.status.container_statuses:
            for s in pod.status.container_statuses:
                state = (
                    "running" if s.state.running else
                    "waiting" if s.state.waiting else
                    "terminated" if s.state.terminated else
                    "unknown"
                )
                statuses.append(f"{s.name}: {state}")

        details = (
            f"Pod: {pod.metadata.name}\n"
            f"Namespace: {pod.metadata.namespace}\n"
            f"Status: {pod.status.phase}\n"
            f"Node: {pod.spec.node_name or 'N/A'}\n"
            f"Containers: {', '.join(containers) if containers else 'N/A'}\n"
            f"Container Statuses: {', '.join(statuses) if statuses else 'N/A'}\n"
            f"Start Time: {pod.status.start_time or 'N/A'}"
        )
        return details

    except client.ApiException as e:
        return f"Error: Failed to get details for pod '{pod_name}'. Details: {e.reason}"

@tool
def get_pod_logs(pod_name: str, namespace: str) -> str:
    """
    Fetches logs for a pod.
    Returns only the first few lines as a summary.
    """
    try:
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=20)
        lines = logs.splitlines()
        summary = "\n".join(lines[-10:]) if lines else "No logs available."
        return f"Log summary for '{pod_name}':\n{summary}"
    except client.ApiException as e:
        return f"Error: Failed to get logs for pod '{pod_name}'. Details: {e.reason}"

@tool
def list_deployments(namespace: str = "default") -> str:
    """
    Lists deployment names in a namespace.
    Returns only names, one per line.
    """
    try:
        if namespace.lower() == "all":
            deployments = apps_v1.list_deployment_for_all_namespaces()
        else:
            deployments = apps_v1.list_namespaced_deployment(namespace=namespace)

        deployment_names = [d.metadata.name for d in deployments.items]
        return "\n".join(deployment_names) if deployment_names else f"No deployments found in namespace '{namespace}'."
    except client.ApiException as e:
        return f"Error: Failed to list deployments. Details: {e.reason}"

@tool
def list_namespaces() -> str:
    """
    Lists all namespaces.
    Returns only namespace names, one per line.
    """
    try:
        ns_list = v1.list_namespace()
        namespaces = [ns.metadata.name for ns in ns_list.items]
        return "\n".join(namespaces) if namespaces else "No namespaces found."
    except client.ApiException as e:
        return f"Error: Failed to list namespaces. Details: {e.reason}"
