"""Ask command for Q&A functionality over the project."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text

from agentcli.core.search import perform_semantic_search, SearchServiceFactory
from agentcli.core.azure_llm import create_llm_service
from agentcli.utils.logging import logger


class ProjectQAService:
    """Service for answering questions about the project using RAG."""
    
    def __init__(self, console: Console):
        self.console = console
        self.llm_service = create_llm_service()
        self.search_service = SearchServiceFactory.get_default_semantic_search_service()
    
    def answer_question(self, question: str, top_k: int = 5) -> str:
        """Answer a question about the project."""
        try:
            # 1. Perform semantic search to find relevant code
            with self.console.status("🔍 Searching for relevant code..."):
                search_results_dict = perform_semantic_search(question, top_k=top_k)
                search_results = search_results_dict.get("results", [])
            
            if not search_results:
                return "I couldn't find any relevant code to answer your question. Try rephrasing or being more specific."
            
            # 2. Build context from search results
            context_parts = []
            for i, result in enumerate(search_results[:top_k], 1):
                relevance = result.get('relevance', 0.0)
                metadata = result.get('metadata', {})
                content = result.get('content', '')
                
                context_parts.append(f"### Code snippet {i} (Relevance: {relevance:.3f})")
                context_parts.append(f"File: {metadata.get('file_path', 'unknown')}")
                context_parts.append(f"```{self._get_language_from_path(metadata.get('file_path', ''))}")
                context_parts.append(content)
                context_parts.append("```")
                context_parts.append("")
            
            context = "\n".join(context_parts)
            
            # 3. Generate answer using LLM
            with self.console.status("🤖 Generating answer..."):
                answer = self._generate_answer(question, context, search_results)
            
            return answer
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"Sorry, I encountered an error while trying to answer your question: {str(e)}"
    
    def _generate_answer(self, question: str, context: str, search_results) -> str:
        """Generate an answer using the LLM."""
        # Show which files were found for context
        files_found = set()
        for result in search_results:
            metadata = result.get('metadata', {})
            file_path = metadata.get('file_path', 'unknown')
            files_found.add(file_path)
        
        files_list = "\n".join(f"- {file}" for file in sorted(files_found))
        
        prompt = f"""You are an expert code assistant helping a developer understand their codebase. 
Based on the provided code snippets, answer the user's question accurately and helpfully.

**Question:** {question}

**Relevant code found in these files:**
{files_list}

**Code Context:**
{context}

**Instructions:**
1. Answer the question based ONLY on the provided code context
2. Be specific and reference the actual code when possible
3. If the code doesn't contain enough information to fully answer the question, say so
4. Use technical terms appropriately but explain complex concepts
5. Format your answer in markdown for better readability
6. Include code examples from the context when relevant

**Answer:**"""

        try:
            response = self.llm_service.complete(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            # Fallback: provide a basic answer based on search results
            return self._create_fallback_answer(question, search_results)
    
    def _get_language_from_path(self, file_path: str) -> str:
        """Get programming language from file path."""
        if not file_path:
            return 'text'
        
        ext = file_path.split('.')[-1].lower()
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rs': 'rust',
            'rb': 'ruby',
            'php': 'php',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'yaml': 'yaml',
            'yml': 'yaml',
            'xml': 'xml',
            'md': 'markdown',
            'sh': 'bash',
            'sql': 'sql'
        }
        return language_map.get(ext, 'text')
    
    def _create_fallback_answer(self, question: str, search_results) -> str:
        """Create a fallback answer when LLM fails."""
        answer_parts = [
            f"I found {len(search_results)} relevant code snippets for your question:",
            ""
        ]
        
        for i, result in enumerate(search_results[:3], 1):
            metadata = result.get('metadata', {})
            file_path = metadata.get('file_path', 'unknown')
            relevance = result.get('relevance', 0.0)
            content = result.get('content', '')
            
            answer_parts.append(f"**{i}. {file_path}** (Relevance: {relevance:.1%})")
            answer_parts.append(f"```")
            answer_parts.append(content[:200] + "..." if len(content) > 200 else content)
            answer_parts.append(f"```")
            answer_parts.append("")
        
        answer_parts.append("*Note: LLM service is unavailable, showing raw search results.*")
        
        return "\n".join(answer_parts)


@click.command()
@click.argument("question", required=True)
@click.option("--top-k", "-k", default=5, help="Number of relevant code snippets to consider")
@click.option("--rebuild-index", is_flag=True, help="Rebuild the search index before answering")
@click.option("--format", type=click.Choice(["rich", "plain"]), default="rich", help="Output format")
def ask(question, top_k, rebuild_index, format):
    """Ask a question about your project and get an AI-powered answer.
    
    QUESTION - Your question about the codebase
    
    Examples:
      agentcli ask "How does the rollback functionality work?"
      agentcli ask "What files are involved in the delete command?"
      agentcli ask "How is the LLM service configured?"
    """
    console = Console()
    
    if rebuild_index:
        with console.status("🔄 Rebuilding search index..."):
            search_service = SearchServiceFactory.get_default_semantic_search_service()
            search_service.rebuild_index()
        console.print("✅ Search index rebuilt!")
    
    # Initialize Q&A service
    qa_service = ProjectQAService(console)
    
    # Show the question
    question_panel = Panel(
        Text(question, style="bold cyan"),
        title="❓ Your Question",
        border_style="cyan"
    )
    console.print(question_panel)
    
    # Get the answer
    answer = qa_service.answer_question(question, top_k=top_k)
    
    # Display the answer
    if format == "rich":
        try:
            # Try to render as markdown for rich formatting
            answer_content = Markdown(answer)
        except Exception:
            # Fallback to plain text if markdown parsing fails
            answer_content = Text(answer)
        
        answer_panel = Panel(
            answer_content,
            title="🤖 Answer",
            border_style="green"
        )
        console.print(answer_panel)
    else:
        # Plain format
        console.print("\n" + answer + "\n")


if __name__ == "__main__":
    ask()
