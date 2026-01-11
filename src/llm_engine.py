"""
LLM Engine Module for Oracle AI Platform

This module provides a centralized interface for LLM interactions using Groq API.
Handles prompt engineering, error handling, and different types of analysis.
"""

import os
import yaml
import time
from typing import Dict, Any, Optional, List
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMEngine:
    """
    Centralized LLM engine for Oracle AI Platform using Groq API.
    """

    def __init__(self, api_key: str = None, model: str = "meta-llama/llama-4-scout-17b-16e-instruct",
                 prompts_file: str = "data/prompts.yaml"):
        """
        Initialize LLM Engine.

        Args:
            api_key: Groq API key
            model: Groq model to use
            prompts_file: Path to prompts YAML file
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        self.model = model
        self.client = Groq(api_key=self.api_key)

        # Load prompts
        self.prompts = self._load_prompts(prompts_file)

        # Error handling settings
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def _load_prompts(self, prompts_file: str) -> Dict[str, Any]:
        """
        Load prompts from YAML file.

        Args:
            prompts_file: Path to prompts file

        Returns:
            Dictionary of prompts
        """
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading prompts file: {e}")
            return {}

    def _call_llm(self, prompt: str, context: str = None, temperature: float = 0.1) -> str:
        """
        Make LLM API call with retry logic.

        Args:
            prompt: The prompt to send
            context: Optional context for RAG
            temperature: Creativity parameter

        Returns:
            LLM response text
        """
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\n{prompt}"

        messages = [
            {"role": "system", "content": self.prompts.get('general', {}).get('system_prompt', '')},
            {"role": "user", "content": full_prompt}
        ]

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=2048,
                    top_p=1,
                    stream=False
                )

                return response.choices[0].message.content.strip()

            except Exception as e:
                print(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    return f"Error: Failed to get LLM response after {self.max_retries} attempts"

    def generate(self, prompt: str, context: str = None, model: str = None) -> str:
        """
        General LLM generation method.

        Args:
            prompt: The prompt text
            context: Optional context
            model: Override default model

        Returns:
            Generated response
        """
        if model:
            # Temporarily change model
            original_model = self.model
            self.model = model
            result = self._call_llm(prompt, context)
            self.model = original_model
            return result
        else:
            return self._call_llm(prompt, context)

    def analyze_query(self, sql_query: str, plan: Dict[str, Any]) -> str:
        """
        Analyze SQL query performance.

        Args:
            sql_query: The SQL query text
            plan: Execution plan dictionary

        Returns:
            Analysis and optimization suggestions
        """
        prompt_template = self.prompts.get('query_optimization', {}).get('explain_plan', '')
        if not prompt_template:
            return "Error: Query optimization prompt not found"

        # Format plan for prompt
        plan_text = self._format_execution_plan(plan)

        prompt = prompt_template.format(plan_data=plan_text)

        return self._call_llm(prompt)

    def explain_plan(self, plan: Dict[str, Any]) -> str:
        """
        Explain execution plan in simple terms.

        Args:
            plan: Execution plan dictionary

        Returns:
            Simple explanation
        """
        prompt_template = self.prompts.get('query_optimization', {}).get('explain_plan', '')
        if not prompt_template:
            return "Error: Explain plan prompt not found"

        plan_text = self._format_execution_plan(plan)
        prompt = prompt_template.format(plan_data=plan_text)

        return self._call_llm(prompt)

    def identify_costly_operations(self, plan: Dict[str, Any]) -> str:
        """
        Identify the 3 most costly operations in execution plan.

        Args:
            plan: Execution plan dictionary

        Returns:
            Analysis of costly operations
        """
        prompt_template = self.prompts.get('query_optimization', {}).get('identify_costly_operations', '')
        if not prompt_template:
            return "Error: Identify costly operations prompt not found"

        plan_text = self._format_execution_plan(plan)
        prompt = prompt_template.format(plan_data=plan_text)

        return self._call_llm(prompt)

    def suggest_optimizations(self, sql_query: str, plan: Dict[str, Any]) -> str:
        """
        Suggest specific optimizations for query and plan.

        Args:
            sql_query: The SQL query text
            plan: Execution plan dictionary

        Returns:
            Optimization suggestions
        """
        prompt_template = self.prompts.get('query_optimization', {}).get('suggest_optimizations', '')
        if not prompt_template:
            return "Error: Suggest optimizations prompt not found"

        plan_text = self._format_execution_plan(plan)
        prompt = prompt_template.format(sql_query=sql_query, plan_data=plan_text)

        return self._call_llm(prompt)

    def assess_security(self, config: Dict[str, Any]) -> str:
        """
        Assess security configuration.

        Args:
            config: Security configuration data

        Returns:
            Security assessment report
        """
        prompt_template = self.prompts.get('security_audit', {}).get('analyze_users_roles', '')
        if not prompt_template:
            return "Error: Security audit prompt not found"

        # Format config for prompt
        config_text = self._format_security_config(config)

        prompt = prompt_template.format(users_roles_data=config_text)

        return self._call_llm(prompt)

    def detect_anomaly(self, log_entry: Dict[str, Any], context: str = None) -> str:
        """
        Detect anomalies in audit logs.

        Args:
            log_entry: Audit log entry
            context: Additional context

        Returns:
            Anomaly assessment
        """
        prompt_template = self.prompts.get('anomaly_detection', {}).get('analyze_log_entry', '')
        if not prompt_template:
            return "Error: Anomaly detection prompt not found"

        # Format log entry for prompt
        log_text = self._format_audit_log(log_entry)

        prompt = prompt_template.format(log_entry=log_text)

        return self._call_llm(prompt, context)

    def _format_execution_plan(self, plan) -> str:
        """
        Format execution plan for prompt input.

        Args:
            plan: Execution plan dictionary or list

        Returns:
            Formatted plan text
        """
        if isinstance(plan, list):
            lines = ["📋 Execution Plan:"]
            for step in plan:
                id_val = step.get('id', 0)
                operation = step.get('operation', 'UNKNOWN')
                options = step.get('options', '')
                object_name = step.get('object_name', '')
                cost = step.get('cost', 0)
                cardinality = step.get('cardinality', 0)
                op_text = f"{operation} {options}".strip()
                line = f"  {id_val}: {op_text}"
                if object_name:
                    line += f" on {object_name}"
                if cost or cardinality:
                    line += f" (Cost: {cost}, Rows: {cardinality})"
                lines.append(line)
            return "\n".join(lines)
        elif isinstance(plan, dict):
            lines = []
            self._format_plan_recursive(plan, lines, 0)
            return "\n".join(lines)
        else:
            return str(plan)

    def _format_plan_recursive(self, plan: Dict[str, Any], lines: List[str], depth: int):
        """
        Recursively format plan tree.

        Args:
            plan: Plan node
            lines: Output lines
            depth: Current depth
        """
        indent = "  " * depth

        operation = plan.get('operation', 'UNKNOWN')
        object_name = plan.get('object_name', '')
        cost = plan.get('cost', '')
        cardinality = plan.get('cardinality', '')

        line = f"{indent}{operation}"
        if object_name:
            line += f" on {object_name}"
        if cost:
            line += f" (Cost: {cost}"
        if cardinality:
            line += f", Rows: {cardinality}"
        if cost or cardinality:
            line += ")"

        lines.append(line)

        # Process children
        if 'children' in plan and plan['children']:
            for child in plan['children']:
                self._format_plan_recursive(child, lines, depth + 1)

    def _format_security_config(self, config: Dict[str, Any]) -> str:
        """
        Format security configuration for prompt input.

        Args:
            config: Security config dictionary

        Returns:
            Formatted config text
        """
        lines = []

        if 'users' in config:
            lines.append("Users:")
            for user in config['users']:
                status = user.get('account_status', 'UNKNOWN')
                lines.append(f"  - {user.get('username', 'UNKNOWN')}: {status}")

        if 'roles' in config:
            lines.append("\nRoles:")
            for role in config['roles']:
                lines.append(f"  - {role.get('role', 'UNKNOWN')}")

        if 'privileges' in config:
            lines.append("\nPrivileges:")
            for priv in config['privileges']:
                grantee = priv.get('grantee', 'UNKNOWN')
                privilege = priv.get('privilege', 'UNKNOWN')
                lines.append(f"  - {grantee}: {privilege}")

        return "\n".join(lines)

    def _format_audit_log(self, log_entry: Dict[str, Any]) -> str:
        """
        Format audit log entry for prompt input.

        Args:
            log_entry: Audit log dictionary

        Returns:
            Formatted log text
        """
        timestamp = log_entry.get('timestamp', 'UNKNOWN')
        user = log_entry.get('user', 'UNKNOWN')
        action = log_entry.get('action', 'UNKNOWN')
        object_name = log_entry.get('object', 'UNKNOWN')
        return_type = log_entry.get('returncode', 'UNKNOWN')

        return f"Timestamp: {timestamp}\nUser: {user}\nAction: {action}\nObject: {object_name}\nReturn Code: {return_type}"

    def get_available_models(self) -> List[str]:
        """
        Get list of available Groq models.

        Returns:
            List of model names
        """
        # Groq models as of 2024
        return [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "gemma-7b-it",
            "llama2-70b-4096"
        ]

    def test_connection(self) -> bool:
        """
        Test LLM API connection.

        Returns:
            True if connection successful
        """
        try:
            response = self.generate("Hello, respond with 'OK' if you can read this.")
            return "OK" in response.upper()
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
        
    def classify_intent_with_confidence(self, user_prompt: str) -> str:
        """
        Classify user intent into appropriate module category.
        
        Args:
            user_prompt: The user's question or request
        
        Returns:
            Category name (DATABASE_QUERY, QUERY_OPTIMIZATION, etc.)
        """
        prompt_template = self.prompts.get('intent_classification', {}).get('classify_intent', '')
        
        if not prompt_template:
            print("Warning: Intent classification prompt not found, using fallback")
            return "GENERAL_HELP"
        
        # Format the prompt
        formatted_prompt = prompt_template.format(user_prompt=user_prompt)
        
        # Get classification with low temperature for consistency
        try:
            classification = self._call_llm(formatted_prompt, temperature=0.0)
            
            # Clean up response (remove any extra text)
            classification = classification.strip().upper()
            
            # Validate response
            valid_categories = [
                "DATABASE_QUERY",
                "QUERY_OPTIMIZATION",
                "SECURITY_AUDIT",
                "ANOMALY_DETECTION",
                "BACKUP_STRATEGY",
                "RECOVERY_GUIDE",
                "GENERAL_HELP"
            ]
            
            # Extract category from response if LLM added extra text
            for category in valid_categories:
                if category in classification:
                    return category
            
            # Fallback if no valid category found
            print(f"Warning: Invalid classification '{classification}', using GENERAL_HELP")
            return "GENERAL_HELP"
            
        except Exception as e:
            print(f"Error during intent classification: {e}")
            return "GENERAL_HELP"