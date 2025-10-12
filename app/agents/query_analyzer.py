import google.generativeai as genai
import json
import os

class QueryAnalyzerAgent:
    """
    Transforms a user's query into a structured JSON object containing a
    rephrased semantic_query and a list of graph_tags.
    """

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config['llm']
        self.prompt_template = config['prompts']['query_analyzer']
        
        # No proxy code here. The global fix in app.py handles it.
        self.model = genai.GenerativeModel(
            self.config['model_name'],
            generation_config=self.config['generation_config']
        )

    def run(self, user_question):
        """
        Executes the agent's logic.
        Args:
            user_question (str): The user's question in natural language.
        Returns:
            dict: A dictionary containing the semantic_query and graph_tags.
        """
        prompt = self.prompt_template.format(user_question=user_question)
        
        try:
            response = self.model.generate_content(prompt)
            cleaned_response_text = response.text.strip().lstrip("```json").rstrip("```")
            structured_query = json.loads(cleaned_response_text)
            
            self.logger.log_api_call(
                agent_name="QueryAnalyzer",
                prompt=prompt,
                response=cleaned_response_text,
                status="success"
            )
            return structured_query

        except Exception as e:
            self.logger.log_api_call(
                agent_name="QueryAnalyzer",
                prompt=prompt,
                response=str(e),
                status="error"
            )
            print(f"QueryAnalyzer Agent Error: {e}")
            raise
