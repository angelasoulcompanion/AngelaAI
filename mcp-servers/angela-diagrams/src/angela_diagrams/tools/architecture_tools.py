"""
Architecture Diagram Tools
Using the 'diagrams' library for cloud and system architecture
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "output"


class ArchitectureTools:
    """Tools for generating architecture diagrams"""

    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, prefix: str) -> str:
        """Generate unique filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(self.output_dir / f"{prefix}_{timestamp}")

    async def create_cloud_architecture(
        self,
        title: str,
        provider: str,
        components: list[dict],
        connections: list[dict],
        direction: str = "LR"
    ) -> dict:
        """
        Create cloud architecture diagram

        Args:
            title: Diagram title
            provider: aws, gcp, azure, kubernetes, onprem
            components: List of components:
                [
                    {"id": "web", "type": "EC2", "label": "Web Server"},
                    {"id": "db", "type": "RDS", "label": "Database"},
                    {"id": "cache", "type": "ElastiCache", "label": "Redis"}
                ]
            connections: List of connections:
                [
                    {"from": "web", "to": "db", "label": "query"},
                    {"from": "web", "to": "cache"}
                ]
            direction: LR (left-right), TB (top-bottom), RL, BT

        Returns:
            dict with file path and diagram info
        """
        try:
            from diagrams import Diagram, Edge, Cluster

            # Import provider-specific nodes
            if provider == "aws":
                from diagrams.aws.compute import EC2, Lambda, ECS
                from diagrams.aws.database import RDS, ElastiCache, DynamoDB
                from diagrams.aws.network import ELB, Route53, APIGateway
                from diagrams.aws.storage import S3

                node_map = {
                    "EC2": EC2, "Lambda": Lambda, "ECS": ECS,
                    "RDS": RDS, "ElastiCache": ElastiCache, "DynamoDB": DynamoDB,
                    "ELB": ELB, "Route53": Route53, "APIGateway": APIGateway,
                    "S3": S3
                }
            elif provider == "gcp":
                from diagrams.gcp.compute import ComputeEngine, Functions, GKE
                from diagrams.gcp.database import SQL, Memorystore, BigTable
                from diagrams.gcp.network import LoadBalancing, DNS
                from diagrams.gcp.storage import GCS

                node_map = {
                    "ComputeEngine": ComputeEngine, "Functions": Functions, "GKE": GKE,
                    "SQL": SQL, "Memorystore": Memorystore, "BigTable": BigTable,
                    "LoadBalancing": LoadBalancing, "DNS": DNS,
                    "GCS": GCS
                }
            elif provider == "azure":
                from diagrams.azure.compute import VM, FunctionApps, AKS
                from diagrams.azure.database import SQLDatabases, CosmosDb
                from diagrams.azure.network import LoadBalancers, DNS
                from diagrams.azure.storage import BlobStorage

                node_map = {
                    "VM": VM, "FunctionApps": FunctionApps, "AKS": AKS,
                    "SQLDatabases": SQLDatabases, "CosmosDb": CosmosDb,
                    "LoadBalancers": LoadBalancers, "DNS": DNS,
                    "BlobStorage": BlobStorage
                }
            elif provider == "kubernetes":
                from diagrams.k8s.compute import Pod, Deployment, ReplicaSet
                from diagrams.k8s.network import Service, Ingress
                from diagrams.k8s.storage import PV, PVC

                node_map = {
                    "Pod": Pod, "Deployment": Deployment, "ReplicaSet": ReplicaSet,
                    "Service": Service, "Ingress": Ingress,
                    "PV": PV, "PVC": PVC
                }
            else:  # onprem
                from diagrams.onprem.compute import Server
                from diagrams.onprem.database import PostgreSQL, MySQL, MongoDB, Redis
                from diagrams.onprem.network import Nginx, HAProxy
                from diagrams.onprem.queue import RabbitMQ, Kafka
                from diagrams.onprem.client import Client, User

                node_map = {
                    "Server": Server,
                    "PostgreSQL": PostgreSQL, "MySQL": MySQL, "MongoDB": MongoDB, "Redis": Redis,
                    "Nginx": Nginx, "HAProxy": HAProxy,
                    "RabbitMQ": RabbitMQ, "Kafka": Kafka,
                    "Client": Client, "User": User
                }

            output_path = self._generate_filename(f"architecture_{provider}")

            # Create diagram
            graph_attr = {
                "fontsize": "14",
                "bgcolor": "white"
            }

            with Diagram(
                title,
                filename=output_path,
                show=False,
                direction=direction,
                graph_attr=graph_attr
            ):
                # Create nodes
                nodes = {}
                for comp in components:
                    node_class = node_map.get(comp["type"])
                    if node_class:
                        label = comp.get("label", comp["id"])
                        nodes[comp["id"]] = node_class(label)

                # Create connections
                for conn in connections:
                    if conn["from"] in nodes and conn["to"] in nodes:
                        edge_label = conn.get("label", "")
                        if edge_label:
                            nodes[conn["from"]] >> Edge(label=edge_label) >> nodes[conn["to"]]
                        else:
                            nodes[conn["from"]] >> nodes[conn["to"]]

            return {
                "success": True,
                "file_path": f"{output_path}.png",
                "diagram_type": "cloud_architecture",
                "provider": provider,
                "title": title,
                "components_count": len(components),
                "connections_count": len(connections)
            }

        except ImportError as e:
            return {
                "success": False,
                "error": f"Missing dependency: {str(e)}. Install with: pip install diagrams",
                "diagram_type": "cloud_architecture"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "diagram_type": "cloud_architecture"
            }

    async def create_system_architecture(
        self,
        title: str,
        layers: list[dict],
        connections: list[dict]
    ) -> dict:
        """
        Create a layered system architecture diagram

        Args:
            title: Diagram title
            layers: List of layers with components:
                [
                    {
                        "name": "Frontend",
                        "components": [
                            {"id": "web", "label": "Web App"},
                            {"id": "mobile", "label": "Mobile App"}
                        ]
                    },
                    {
                        "name": "Backend",
                        "components": [
                            {"id": "api", "label": "API Server"},
                            {"id": "worker", "label": "Background Worker"}
                        ]
                    }
                ]
            connections: Same as cloud_architecture

        Returns:
            dict with diagram info
        """
        try:
            from diagrams import Diagram, Cluster, Edge
            from diagrams.onprem.compute import Server
            from diagrams.onprem.client import Client
            from diagrams.onprem.database import PostgreSQL
            from diagrams.onprem.queue import RabbitMQ
            from diagrams.onprem.network import Nginx

            output_path = self._generate_filename("system_architecture")

            with Diagram(title, filename=output_path, show=False, direction="TB"):
                all_nodes = {}

                for layer in layers:
                    with Cluster(layer["name"]):
                        for comp in layer.get("components", []):
                            label = comp.get("label", comp["id"])
                            all_nodes[comp["id"]] = Server(label)

                # Create connections
                for conn in connections:
                    if conn["from"] in all_nodes and conn["to"] in all_nodes:
                        edge_label = conn.get("label", "")
                        if edge_label:
                            all_nodes[conn["from"]] >> Edge(label=edge_label) >> all_nodes[conn["to"]]
                        else:
                            all_nodes[conn["from"]] >> all_nodes[conn["to"]]

            return {
                "success": True,
                "file_path": f"{output_path}.png",
                "diagram_type": "system_architecture",
                "title": title,
                "layers_count": len(layers)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "diagram_type": "system_architecture"
            }

    def get_available_components(self, provider: str) -> dict:
        """
        Get list of available components for a provider

        Args:
            provider: aws, gcp, azure, kubernetes, onprem

        Returns:
            dict with component categories and types
        """
        components = {
            "aws": {
                "compute": ["EC2", "Lambda", "ECS", "EKS", "Fargate"],
                "database": ["RDS", "DynamoDB", "ElastiCache", "Redshift"],
                "storage": ["S3", "EBS", "EFS"],
                "network": ["ELB", "Route53", "APIGateway", "CloudFront", "VPC"]
            },
            "gcp": {
                "compute": ["ComputeEngine", "Functions", "GKE", "AppEngine"],
                "database": ["SQL", "Spanner", "BigTable", "Memorystore"],
                "storage": ["GCS", "Filestore"],
                "network": ["LoadBalancing", "DNS", "CDN"]
            },
            "azure": {
                "compute": ["VM", "FunctionApps", "AKS", "ContainerInstances"],
                "database": ["SQLDatabases", "CosmosDb", "CacheForRedis"],
                "storage": ["BlobStorage", "DataLake"],
                "network": ["LoadBalancers", "DNS", "CDN", "Firewall"]
            },
            "kubernetes": {
                "compute": ["Pod", "Deployment", "ReplicaSet", "StatefulSet", "DaemonSet"],
                "network": ["Service", "Ingress", "NetworkPolicy"],
                "storage": ["PV", "PVC", "StorageClass"],
                "config": ["ConfigMap", "Secret"]
            },
            "onprem": {
                "compute": ["Server"],
                "database": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra"],
                "network": ["Nginx", "HAProxy", "Apache"],
                "queue": ["RabbitMQ", "Kafka", "Celery"],
                "client": ["Client", "User"]
            }
        }

        return components.get(provider, {})
