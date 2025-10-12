import google.generativeai as genai
import json
import os

class KnowledgeLinkerAgent:
    """
    Finds and defines relationships between a new knowledge node and
    existing nodes in the graph.
    """

    def __init__(self, config, logger, vector_db):
        self.logger = logger
        self.vector_db = vector_db
        self.config = config['llm']
        self.prompt_template = config['prompts']['linker']
        
        # No proxy code here. The global fix in app.py handles it.
        self.model = genai.GenerativeModel(
            self.config['model_name'],
            generation_config=self.config['generation_config']
        )

    def run(self, new_node_id, new_node_summary):
        """
        Executes the agent's logic.
        Args:
            new_node_id (str): The ID of the new node being added.
            new_node_summary (str): The summary of the new node.
        Returns:
            list: A list of JSON objects, each defining a relationship to create.
        """
        # 1. Retrieve candidate nodes via semantic search
        candidate_nodes_meta = self.vector_db.query_embeddings(new_node_summary, n_results=5)
        
        if not candidate_nodes_meta:
            return [] # No potential links found
        
        candidate_nodes_json = json.dumps(candidate_nodes_meta, indent=2)

        prompt = self.prompt_template.format(
            new_node_id=new_node_id,
            new_node_summary=new_node_summary,
            candidate_nodes=candidate_nodes_json
        )

        try:
            response = self.model.generate_content(prompt)
            cleaned_response_text = response.text.strip().lstrip("```json").rstrip("```")
            relationships = json.loads(cleaned_response_text)
            
            self.logger.log_api_call(
                agent_name="KnowledgeLinker",
                prompt=prompt,
                response=cleaned_response_text,
                status="success"
            )
            return relationships

        except Exception as e:
            self.logger.log_api_call(
                agent_name="KnowledgeLinker",
                prompt=prompt,
                response=str(e),
                status="error"
            )
            print(f"KnowledgeLinker Agent Error: {e}")
            # If parsing fails, return an empty list to not break the pipeline
            return []
