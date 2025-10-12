from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from datetime import datetime
import time

class GraphDBConnector:
    """Handles all interactions with the Neo4j database."""

    def __init__(self, uri, user, password):
        """
        Initializes the connector and establishes a connection to the database.
        Includes a retry mechanism to handle startup race conditions.
        Args:
            uri (str): The Bolt URI for the Neo4j instance.
            user (str): The username for authentication.
            password (str): The password for authentication.
        """
        self.driver = None
        retries = 5
        delay = 5  # seconds
        for i in range(retries):
            try:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                self.driver.verify_connectivity()
                self._create_constraints()
                print("Neo4j connection successful.")
                return
            except ServiceUnavailable as e:
                print(f"Neo4j not available, retrying in {delay}s... ({i+1}/{retries})")
                time.sleep(delay)
            except Exception as e:
                print(f"An unexpected error occurred during Neo4j connection: {e}")
                raise
        
        # If all retries fail, raise the last exception
        raise ServiceUnavailable("Could not connect to Neo4j after several retries.")


    def close(self):
        """Closes the database connection driver."""
        if self.driver:
            self.driver.close()

    def _create_constraints(self):
        """Ensures the KnowledgeNode node_id is unique."""
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.node_id IS UNIQUE")

    def create_knowledge_node(self, node_id, content_raw, content_summary, node_type, tags):
        """
        Creates a new KnowledgeNode in the graph.
        Args:
            node_id (str): A unique UUID for the node.
            content_raw (str): The original text from the user.
            content_summary (str): The AI-generated summary.
            node_type (str): The category of the node (e.g., 'Concept').
            tags (list): The hierarchical list of tags.
        """
        with self.driver.session() as session:
            session.run(
                """
                CREATE (n:KnowledgeNode {
                    node_id: $node_id,
                    content_raw: $content_raw,
                    content_summary: $content_summary,
                    node_type: $node_type,
                    tags: $tags,
                    created_at: $created_at
                })
                """,
                node_id=node_id,
                content_raw=content_raw,
                content_summary=content_summary,
                node_type=node_type,
                tags=tags,
                created_at=datetime.utcnow()
            )

    def create_relationship(self, from_node_id, to_node_id, rel_type, description):
        """
        Creates a directed relationship between two KnowledgeNodes.
        Args:
            from_node_id (str): The ID of the source node.
            to_node_id (str): The ID of the target node.
            rel_type (str): The type of the relationship (e.g., 'explains').
            description (str): An AI-generated sentence explaining the link.
        """
        with self.driver.session() as session:
            # The relationship type is dynamic, so we format it into the query string.
            # This is generally safe as we control the possible rel_type values.
            query = f"""
            MATCH (a:KnowledgeNode {{node_id: $from_node_id}})
            MATCH (b:KnowledgeNode {{node_id: $to_node_id}})
            CREATE (a)-[r:RELATES_TO {{type: $rel_type, description: $description}}]->(b)
            """
            session.run(query, from_node_id=from_node_id, to_node_id=to_node_id, rel_type=rel_type, description=description)

    def delete_node(self, node_id):
        """
        Deletes a node and all its relationships.
        Args:
            node_id (str): The ID of the node to delete.
        """
        with self.driver.session() as session:
            session.run("MATCH (n:KnowledgeNode {node_id: $node_id}) DETACH DELETE n", node_id=node_id)

    def search_nodes_by_tag(self, tag):
        """
        Finds all nodes that have a specific tag in their tags list.
        Args:
            tag (str): The tag to search for.
        Returns:
            list: A list of dictionaries, each representing a node.
        """
        with self.driver.session() as session:
            result = session.run("MATCH (n:KnowledgeNode) WHERE $tag IN n.tags RETURN n", tag=tag)
            return [record["n"]._properties for record in result]

    def search_nodes_by_content(self, search_term):
        """
        Finds nodes where the raw content or summary contains the search term.
        Args:
            search_term (str): The term to search for.
        Returns:
            list: A list of matching nodes.
        """
        with self.driver.session() as session:
            # Using toLower() for case-insensitive search
            result = session.run("""
                MATCH (n:KnowledgeNode)
                WHERE toLower(n.content_raw) CONTAINS toLower($search_term)
                OR toLower(n.content_summary) CONTAINS toLower($search_term)
                RETURN n
            """, search_term=search_term)
            return [record["n"]._properties for record in result]

    def get_nodes_by_ids(self, node_ids):
        """
        Fetches full node data for a given list of node IDs.
        Args:
            node_ids (list): A list of node_id strings.
        Returns:
            list: A list of node property dictionaries.
        """
        if not node_ids:
            return []
        with self.driver.session() as session:
            result = session.run("MATCH (n:KnowledgeNode) WHERE n.node_id IN $node_ids RETURN n", node_ids=list(node_ids))
            return [record["n"]._properties for record in result]


    def get_full_graph(self):
        """
        Fetches all nodes and relationships for visualization.
        Returns:
            dict: A dictionary containing lists of nodes and relationships.
        """
        with self.driver.session() as session:
            nodes_result = session.run("MATCH (n:KnowledgeNode) RETURN n")
            nodes = [record["n"]._properties for record in nodes_result]

            rels_result = session.run("MATCH (a)-[r:RELATES_TO]->(b) RETURN a.node_id AS source, b.node_id AS target, r.type AS type")
            relationships = [record.data() for record in rels_result]

            return {"nodes": nodes, "relationships": relationships}
