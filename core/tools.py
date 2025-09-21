from kubernetes import client, config
from langchain_core.tools import tool
import os

# The Kubernetes client automatically handles in-cluster configuration
# It uses the Service Account token to authenticate with the API server.
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
    Lists all pods in a specified namespace. If no namespace is provided,
    it lists pods in the current context's default namespace.
    
    Args:
        namespace: The Kubernetes namespace to list pods from.
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
    Retrieves detailed information about a specific pod.
    
    Args:
        pod_name: The name of the pod to get details for.
        namespace: The Kubernetes namespace the pod is in.
    """
    try:
        ret = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        details = f"Pod: {ret.metadata.name}\n" \
                  f"Namespace: {ret.metadata.namespace}\n" \
                  f"Status: {ret.status.phase}\n" \
                  f"Node: {ret.spec.node_name}\n" \
                  f"Containers: {[c.name for c in ret.spec.containers]}\n" \
                  f"Container Statuses: {[s.state for s in ret.status.container_statuses]}\n" \
                  f"Start Time: {ret.status.start_time}"
        return details
    except client.ApiException as e:
        return f"Error: Failed to get details for pod '{pod_name}'. Details: {e.reason}"

@tool
def get_pod_logs(pod_name: str, namespace: str) -> str:
    """
    Fetches the logs for a specific pod. Useful for debugging pod failures.
    
    Args:
        pod_name: The name of the pod to get logs for.
        namespace: The Kubernetes namespace the pod is in.
    """
    try:
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace)
        return f"Logs for '{pod_name}':\n\n{logs}"
    except client.ApiException as e:
        return f"Error: Failed to get logs for pod '{pod_name}'. Details: {e.reason}"

@tool
def list_deployments(namespace: str) -> str:
    """
    Lists all deployments in a specified namespace.
    
    Args:
        namespace: The Kubernetes namespace.
    """
    try:
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
        deployment_names = [d.metadata.name for d in deployments.items]
        if deployment_names:
            return "\n".join(deployment_names)
        else:
            return f"No deployments found in namespace '{namespace}'."
    except client.ApiException as e:
        return f"Error: Failed to list deployments. Details: {e.reason}"

# You would add more functions here for other read-only operations
# like listing services, nodes, etc.