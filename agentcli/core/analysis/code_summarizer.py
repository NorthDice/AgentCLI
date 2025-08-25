"""Code summarizer using LLM for intelligent code explanation."""

from typing import List, Optional
from agentcli.core import get_llm_service, LLMServiceError
from .models import ModuleInfo, AnalysisResult


class CodeSummarizer:
    """Generates intelligent summaries of code using LLM."""
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def summarize_module(self, module_info: ModuleInfo) -> AnalysisResult:
        """Generate comprehensive summary of a module.
        
        Args:
            module_info (ModuleInfo): Parsed module information
            
        Returns:
            AnalysisResult: Complete analysis with summary and insights
        """
        try:
            # Build context for LLM
            context = self._build_module_context(module_info)
            
            # Generate summary
            summary = self._generate_summary(context, module_info)
            
            # Extract key points
            key_points = self._extract_key_points(module_info)
            
            # Analyze dependencies
            dependencies = self._analyze_dependencies(module_info)
            
            # Determine complexity level
            complexity_level = self._determine_complexity_level(module_info)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(module_info)
            
            return AnalysisResult(
                module_info=module_info,
                summary=summary,
                key_points=key_points,
                dependencies=dependencies,
                complexity_level=complexity_level,
                recommendations=recommendations
            )
            
        except LLMServiceError as e:
            # Fallback to basic analysis if LLM fails
            return self._create_fallback_analysis(module_info)
    
    def _build_module_context(self, module_info: ModuleInfo) -> str:
        """Build context string for LLM analysis."""
        context_parts = []
        
        # Module header
        context_parts.append(f"Module: {module_info.module_name}")
        context_parts.append(f"File: {module_info.file_path}")
        context_parts.append(f"Lines: {module_info.line_count}")
        
        # Module docstring
        if module_info.docstring:
            context_parts.append(f"Module docstring: {module_info.docstring}")
        
        # Imports summary
        if module_info.imports:
            imports_summary = []
            for imp in module_info.imports[:10]:  # Limit to first 10
                if imp.is_from_import:
                    imports_summary.append(f"from {imp.module} import {', '.join(imp.names)}")
                else:
                    imports_summary.append(f"import {imp.module}")
            context_parts.append(f"Key imports: {'; '.join(imports_summary)}")
        
        # Classes summary
        if module_info.classes:
            classes_summary = []
            for cls in module_info.classes:
                methods_count = len(cls.methods)
                base_info = f" extends {', '.join(cls.base_classes)}" if cls.base_classes else ""
                classes_summary.append(f"{cls.name}{base_info} ({methods_count} methods)")
            context_parts.append(f"Classes: {'; '.join(classes_summary)}")
        
        # Functions summary  
        if module_info.functions:
            functions_summary = []
            for func in module_info.functions:
                params_count = len(func.parameters)
                async_info = "async " if func.is_async else ""
                functions_summary.append(f"{async_info}{func.name}({params_count} params)")
            context_parts.append(f"Functions: {'; '.join(functions_summary)}")
        
        # Constants
        if module_info.constants:
            context_parts.append(f"Constants: {', '.join(module_info.constants[:5])}")
        
        return "\\n".join(context_parts)
    
    def _generate_summary(self, context: str, module_info: ModuleInfo) -> str:
        """Generate LLM-based summary."""
        prompt = f"""
            Analyze the following Python module and provide a concise summary:

            {context}

            Please provide a clear, concise summary that includes:
            1. The main purpose of this module
            2. Key functionality it provides
            3. Primary inputs and outputs
            4. How it fits into a larger system (if apparent)

            Keep the summary under 150 words and focus on what the module does, not how it's implemented.
            """
        
        try:
            actions = self.llm_service.generate_actions(prompt)
            
            # Extract summary from LLM response
            for action in actions:
                if action.get('type') in ['info', 'create_file']:
                    content = action.get('content', '')
                    if content:
                        return content.strip()
            
            # Fallback if no content found
            return self._generate_basic_summary(module_info)
            
        except Exception:
            return self._generate_basic_summary(module_info)
    
    def _generate_basic_summary(self, module_info: ModuleInfo) -> str:
        """Generate basic summary without LLM."""
        parts = []
        
        if module_info.docstring:
            parts.append(module_info.docstring.split('.')[0] + ".")
        
        if module_info.classes:
            class_count = len(module_info.classes)
            parts.append(f"Defines {class_count} class{'es' if class_count > 1 else ''}.")
        
        if module_info.functions:
            func_count = len(module_info.functions)
            parts.append(f"Provides {func_count} function{'s' if func_count > 1 else ''}.")
        
        if not parts:
            parts.append(f"Python module with {module_info.line_count} lines of code.")
        
        return " ".join(parts)
    
    def _extract_key_points(self, module_info: ModuleInfo) -> List[str]:
        """Extract key points about the module."""
        points = []
        

        if module_info.classes:
            for cls in module_info.classes:
                if cls.docstring:
                    points.append(f"Class {cls.name}: {cls.docstring.split('.')[0]}")
                else:
                    methods_info = f"with {len(cls.methods)} methods" if cls.methods else "empty class"
                    points.append(f"Class {cls.name}: {methods_info}")
        
        # Functions
        if module_info.functions:
            for func in module_info.functions:
                if func.docstring:
                    points.append(f"Function {func.name}: {func.docstring.split('.')[0]}")
                else:
                    complexity_info = "complex" if func.complexity_score > 5 else "simple"
                    points.append(f"Function {func.name}: {complexity_info} function")
        
        # Complexity warning
        if module_info.complexity_score > 20:
            points.append(f"⚠️ High complexity score: {module_info.complexity_score}")
        
        return points[:8]  
    
    def _analyze_dependencies(self, module_info: ModuleInfo) -> List[str]:
        """Analyze module dependencies."""
        deps = []
        
        external_deps = set()
        internal_deps = set()
        
        for imp in module_info.imports:
            module_name = imp.module
            
            # Skip standard library (basic heuristic)
            if module_name in {'os', 'sys', 'json', 'datetime', 'typing', 're', 'pathlib'}:
                continue
            
            # Check if it's an internal import (relative or project-specific)
            if module_name.startswith('.') or 'agentcli' in module_name:
                internal_deps.add(module_name)
            else:
                external_deps.add(module_name)
        
        if external_deps:
            deps.append(f"External: {', '.join(sorted(external_deps))}")
        
        if internal_deps:
            deps.append(f"Internal: {', '.join(sorted(internal_deps))}")
        
        return deps
    
    def _determine_complexity_level(self, module_info: ModuleInfo) -> str:
        """Determine complexity level based on various metrics."""
        score = module_info.complexity_score
        
        # Factor in other metrics
        if module_info.line_count > 500:
            score += 5
        if len(module_info.classes) > 5:
            score += 3
        if len(module_info.functions) > 10:
            score += 3
        
        if score <= 10:
            return "low"
        elif score <= 25:
            return "medium"
        else:
            return "high"
    
    def _generate_recommendations(self, module_info: ModuleInfo) -> List[str]:
        """Generate recommendations for code improvement."""
        recommendations = []
        
        # Missing docstrings
        missing_docs = []
        if not module_info.docstring:
            missing_docs.append("module")
        
        for cls in module_info.classes:
            if not cls.docstring:
                missing_docs.append(f"class {cls.name}")
        
        for func in module_info.functions:
            if not func.docstring:
                missing_docs.append(f"function {func.name}")
        
        if missing_docs:
            recommendations.append(f"Add docstrings to: {', '.join(missing_docs[:3])}")
        
        # Complexity warnings
        complex_functions = [f.name for f in module_info.functions if f.complexity_score > 8]
        if complex_functions:
            recommendations.append(f"Consider refactoring complex functions: {', '.join(complex_functions[:2])}")
        
        # Large classes
        large_classes = [c.name for c in module_info.classes if len(c.methods) > 15]
        if large_classes:
            recommendations.append(f"Consider breaking down large classes: {', '.join(large_classes[:2])}")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _create_fallback_analysis(self, module_info: ModuleInfo) -> AnalysisResult:
        """Create basic analysis when LLM is unavailable."""
        return AnalysisResult(
            module_info=module_info,
            summary=self._generate_basic_summary(module_info),
            key_points=self._extract_key_points(module_info),
            dependencies=self._analyze_dependencies(module_info),
            complexity_level=self._determine_complexity_level(module_info),
            recommendations=self._generate_recommendations(module_info)
        )
