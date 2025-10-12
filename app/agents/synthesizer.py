import google.generativeai as genai
import json
import os

class SynthesizerAgent:
    """
    Takes a user's question and a context of retrieved knowledge nodes,
    then calls an LLM to synthesize a final answer.
    """

    def __init__(self, config, logger):
        self.logger = logger
        self.config = config['llm']
        self.prompt_template = config['prompts']['synthesizer']
        
        # No proxy code here. The global fix in app.py handles it.
        self.model = genai.GenerativeModel(
            self.config['model_name'],
            generation_config=self.config['generation_config']
        )

    def run(self, user_question, context_nodes):
        """
        Executes the agent's logic.
        Args:
            user_question (str): The original question from the user.
            context_nodes (list): A list of retrieved KnowledgeNode dictionaries.
        Returns:
            str: The final, formatted markdown answer.
        """
        # Format the context for the prompt
        context = []
        for node in context_nodes:
            context.append({
                "node_id": node['node_id'],
                "content": node.get('content_summary') or node.get('content_raw')
            })
        
        prompt = self.prompt_template.format(
            user_question=user_question,
            context=json.dumps(context, indent=2)
        )

        try:
            response = self.model.generate_content(prompt)
            answer = response.text
            
            self.logger.log_api_call(
                agent_name="Synthesizer",
                prompt=prompt,
                response=answer,
                status="success"
            )
            return answer

        except Exception as e:
            self.logger.log_api_call(
                agent_name="Synthesizer",
                prompt=prompt,
                response=str(e),
                status="error"
            )
            print(f"Synthesizer Agent Error: {e}")
            raise
