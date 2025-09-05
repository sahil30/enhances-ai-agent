import asyncio
import json
from typing import Dict, List, Any, Optional
import httpx
from config import Config


class CustomAIClient:
    """Client for interacting with custom AI API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {config.custom_ai_api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 2000) -> str:
        """Generate response from custom AI API"""
        try:
            payload = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = await self.client.post(
                self.config.custom_ai_api_url,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except Exception as e:
            return f"Error generating AI response: {str(e)}"
    
    async def analyze_context(self, query: str, confluence_data: List[Dict], 
                            jira_data: List[Dict], code_data: List[Dict]) -> str:
        """Analyze all context and generate solution proposal"""
        
        context_summary = self._build_context_summary(confluence_data, jira_data, code_data)
        
        messages = [
            {
                "role": "system",
                "content": """You are an AI agent that analyzes queries against Confluence documentation, 
                JIRA issues, and code repositories to propose solutions. Provide comprehensive, 
                actionable solutions based on the available context."""
            },
            {
                "role": "user", 
                "content": f"""
                Query: {query}
                
                Available Context:
                {context_summary}
                
                Please analyze this information and propose a comprehensive solution.
                Include:
                1. Problem analysis
                2. Relevant documentation references
                3. Related JIRA issues
                4. Code examples or implementations
                5. Step-by-step solution
                """
            }
        ]
        
        return await self.generate_response(messages)
    
    def _build_context_summary(self, confluence_data: List[Dict], 
                             jira_data: List[Dict], code_data: List[Dict]) -> str:
        """Build a comprehensive context summary"""
        summary = []
        
        if confluence_data:
            summary.append("CONFLUENCE DOCUMENTATION:")
            for doc in confluence_data[:5]:  # Limit to top 5 results
                summary.append(f"- {doc.get('title', 'Unknown')}: {doc.get('excerpt', '')[:200]}...")
        
        if jira_data:
            summary.append("\nJIRA ISSUES:")
            for issue in jira_data[:5]:  # Limit to top 5 results
                summary.append(f"- {issue.get('key', 'Unknown')}: {issue.get('summary', '')}")
        
        if code_data:
            summary.append("\nCODE REPOSITORY:")
            for code in code_data[:5]:  # Limit to top 5 results
                summary.append(f"- {code.get('file_path', 'Unknown')}: {code.get('content_preview', '')[:200]}...")
        
        return "\n".join(summary)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()