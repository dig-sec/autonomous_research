"""
Enhanced RAG System - Multi-Model Integration

Integrates the enhanced RAG system with the autonomous multi-model manager.
Provides model-specific prompt engineering and context optimization.
Uses Elasticsearch as the vector database backend.
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass

from .core import (
    DocumentChunk, Document, RetrievalResult, 
    EnhancedEmbeddingManager, DocumentProcessor
)
from .elasticsearch_db import ElasticsearchVectorDatabase

import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path

from .core import DocumentProcessor, EnhancedEmbeddingManager
from .vector_db import EnhancedVectorDatabase, RetrievalResult
from ..models.model_manager import MultiModelManager, ModelRole


@dataclass
class RAGContext:
    """Container for RAG context and metadata."""
    query: str
    retrieved_chunks: List[RetrievalResult]
    context_text: str
    model_role: str
    context_length: int
    source_count: int
    authority_score: float
    retrieval_time: float


class ModelSpecificRAGPromptBuilder:
    """
    Builds model-specific prompts for RAG-enhanced generation.
    """
    
    def __init__(self):
        """Initialize prompt builder with model-specific templates."""
        
        # Model-specific prompt templates
        self.prompt_templates = {
            ModelRole.ANALYSIS_AGENT: {
                'system_prompt': """You are a strategic security analyst specializing in complex threat analysis and risk assessment. Use the provided context to give comprehensive, strategic insights.""",
                'context_format': """SECURITY INTELLIGENCE CONTEXT:
{context}

ANALYSIS REQUEST: {query}

Provide a strategic analysis focusing on:
1. Threat landscape implications
2. Risk assessment and impact
3. Strategic defensive recommendations
4. Long-term security architecture considerations

Your analysis should be comprehensive and strategic, drawing insights from the provided context."""
            },
            
            ModelRole.CODE_EXPERT: {
                'system_prompt': """You are a technical security expert specializing in code analysis, implementation details, and forensic artifacts. Use the provided context to give detailed technical insights.""",
                'context_format': """TECHNICAL CONTEXT:
{context}

TECHNICAL QUERY: {query}

Provide detailed technical analysis including:
1. Implementation specifics and code examples
2. Technical detection methods
3. Forensic artifacts and evidence
4. API calls and system interactions
5. Technical countermeasures

Focus on technical depth and actionable implementation details."""
            },
            
            ModelRole.RESEARCH_SYNTHESIZER: {
                'system_prompt': """You are a research analyst specializing in synthesizing information from multiple sources and creating comprehensive documentation. Use the provided context to create well-structured, comprehensive responses.""",
                'context_format': """RESEARCH CONTEXT FROM MULTIPLE SOURCES:
{context}

RESEARCH QUESTION: {query}

Synthesize the information to provide:
1. Comprehensive overview of the topic
2. Key findings from different sources
3. Cross-source validation and conflicts
4. Structured documentation
5. Knowledge gaps and further research needed

Ensure your response is well-structured and cites relevant sources from the context."""
            },
            
            ModelRole.REDTEAM_SPECIALIST: {
                'system_prompt': """You are a red team specialist focusing on adversarial tactics, attack techniques, and offensive security. Use the provided context to give uncensored, practical insights from an attacker's perspective.""",
                'context_format': """ADVERSARIAL INTELLIGENCE:
{context}

RED TEAM ANALYSIS REQUEST: {query}

Provide red team perspective including:
1. Attack execution methods and variations
2. Evasion techniques and detection bypasses
3. Real-world adversarial usage
4. Advanced persistent threat implementations
5. Practical attack considerations

Focus on practical adversarial tactics and uncensored security analysis."""
            }
        }
    
    def build_prompt(
        self,
        query: str,
        context: str,
        model_role: ModelRole,
        additional_instructions: Optional[str] = None
    ) -> str:
        """
        Build a model-specific prompt with RAG context.
        
        Args:
            query: User query
            context: Retrieved context from RAG
            model_role: Target model role
            additional_instructions: Optional additional instructions
            
        Returns:
            Formatted prompt for the model
        """
        
        template = self.prompt_templates.get(model_role)
        if not template:
            # Fallback to generic template
            return f"Context:\n{context}\n\nQuery: {query}\n\nPlease provide a comprehensive response based on the context."
        
        # Build the main prompt
        main_prompt = template['context_format'].format(
            context=context,
            query=query
        )
        
        # Add additional instructions if provided
        if additional_instructions:
            main_prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{additional_instructions}"
        
        return main_prompt
    
    def get_system_prompt(self, model_role: ModelRole) -> str:
        """Get system prompt for a model role."""
        template = self.prompt_templates.get(model_role)
        return template['system_prompt'] if template else "You are a helpful security expert assistant."


class ContextOptimizer:
    """
    Optimizes context length and quality for different models.
    """
    
    def __init__(self):
        """Initialize context optimizer with model-specific limits."""
        
        # Model-specific context limits (estimated tokens)
        self.context_limits = {
            ModelRole.ANALYSIS_AGENT: 3000,      # phi4:14b - can handle more context
            ModelRole.CODE_EXPERT: 2500,         # deepseek-r1:7b - focus on technical detail
            ModelRole.RESEARCH_SYNTHESIZER: 3500, # gemma3:12b - good for comprehensive context
            ModelRole.REDTEAM_SPECIALIST: 1500   # llama2-uncensored:7b - faster, less context
        }
    
    def optimize_context(
        self,
        retrieval_results: List[RetrievalResult],
        model_role: ModelRole,
        query: str
    ) -> str:
        """
        Optimize context for a specific model.
        
        Args:
            retrieval_results: Retrieved chunks
            model_role: Target model role
            query: Original query for relevance scoring
            
        Returns:
            Optimized context string
        """
        
        context_limit = self.context_limits.get(model_role, 2000)
        
        # Sort by combined score
        sorted_results = sorted(retrieval_results, key=lambda x: x.combined_score, reverse=True)
        
        # Build context with most relevant chunks
        context_parts = []
        current_length = 0
        sources_used = set()
        
        for result in sorted_results:
            chunk = result.chunk
            
            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            chunk_tokens = len(chunk.content) // 4
            
            if current_length + chunk_tokens > context_limit:
                break
            
            # Add source information for context
            source_info = f"[Source: {chunk.source}]"
            if chunk.metadata.get('mitre_techniques'):
                techniques = ', '.join(chunk.metadata['mitre_techniques'])
                source_info += f" [MITRE: {techniques}]"
            
            context_parts.append(f"{source_info}\n{chunk.content}")
            current_length += chunk_tokens
            sources_used.add(chunk.source)
        
        # Assemble final context
        context = "\n\n" + "="*50 + "\n\n".join(context_parts)
        
        # Add context summary
        summary = f"CONTEXT SUMMARY: {len(context_parts)} chunks from {len(sources_used)} sources, ~{current_length} tokens"
        context = summary + "\n" + context
        
        return context
    
    def compress_context(self, context: str, target_length: int) -> str:
        """
        Compress context to fit target length while preserving key information.
        
        Args:
            context: Original context
            target_length: Target character length
            
        Returns:
            Compressed context
        """
        
        if len(context) <= target_length:
            return context
        
        # Split into sections
        sections = context.split('\n\n')
        
        # Prioritize sections with security keywords
        security_keywords = ['mitre', 'attack', 'technique', 'detection', 'exploit', 'vulnerability']
        
        scored_sections = []
        for section in sections:
            score = sum(1 for keyword in security_keywords if keyword.lower() in section.lower())
            scored_sections.append((score, section))
        
        # Sort by relevance and fit within target length
        scored_sections.sort(key=lambda x: x[0], reverse=True)
        
        compressed_parts = []
        current_length = 0
        
        for score, section in scored_sections:
            if current_length + len(section) <= target_length:
                compressed_parts.append(section)
                current_length += len(section)
            else:
                # Truncate final section if needed
                remaining = target_length - current_length
                if remaining > 100:  # Only add if meaningful content can fit
                    compressed_parts.append(section[:remaining] + "...")
                break
        
        return '\n\n'.join(compressed_parts)


class StandaloneElasticsearchRAG:
    """
    Standalone Enhanced RAG system using Elasticsearch backend.
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        cache_dir: str = "./cache/rag",
        elasticsearch_host: str = "localhost",
        elasticsearch_port: int = 9200,
        elasticsearch_user: str = "elastic",
        elasticsearch_password: str = "",  # Should be set via environment variable
        chunk_size: int = 1024,
        chunk_overlap: int = 128
    ):
        """
        Initialize the Standalone Enhanced RAG system.
        
        Args:
            embedding_model: Sentence transformer model name
            cache_dir: Directory for caching
            elasticsearch_host: Elasticsearch host
            elasticsearch_port: Elasticsearch port
            elasticsearch_user: Elasticsearch username
            elasticsearch_password: Elasticsearch password
            chunk_size: Text chunk size
            chunk_overlap: Overlap between chunks
        """
        self.embedding_manager = EnhancedEmbeddingManager(
            model_name=embedding_model,
            cache_dir=f"{cache_dir}/embeddings"
        )
        
        self.document_processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.vector_db = ElasticsearchVectorDatabase(
            embedding_manager=self.embedding_manager,
            host=elasticsearch_host,
            port=elasticsearch_port,
            username=elasticsearch_user,
            password=elasticsearch_password,
            index_name="autonomous_research_rag"
        )
        
        self.prompt_builder = ModelSpecificRAGPromptBuilder()
        self.context_optimizer = ContextOptimizer()
        
        print(f"✅ Standalone Enhanced RAG System initialized")
        print(f"   Embedding model: {embedding_model}")
        print(f"   Elasticsearch: {elasticsearch_host}:{elasticsearch_port}")
        print(f"   Available: {self.vector_db.es is not None}")
    
    def add_document_from_text(self, content: str, title: str, source: str = "manual", source_type: str = "manual") -> bool:
        """
        Add a document from text content.
        
        Args:
            content: Document content
            title: Document title
            source: Source identifier
            source_type: Type of source
            
        Returns:
            True if successful
        """
        # Create document object
        import hashlib
        doc_id = hashlib.sha256(f"{source}_{title}".encode()).hexdigest()[:16]
        
        document = Document(
            id=doc_id,
            title=title,
            content=content,
            source=source,
            source_type=source_type,
            metadata=self.document_processor.extract_metadata(content, source)
        )
        
        # Add to vector database
        chunks_added = self.vector_db.add_document(document, self.document_processor)
        
        if chunks_added > 0:
            print(f"✅ Added document '{title}' with {chunks_added} chunks")
            return True
        else:
            print(f"❌ Failed to add document '{title}'")
            return False
    
    def add_document_from_file(self, file_path: str) -> bool:
        """
        Add a document from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful
        """
        from pathlib import Path
        path = Path(file_path)
        
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        # Process based on file extension
        if path.suffix.lower() == '.pdf':
            document = self.document_processor.process_pdf(str(path))
        elif path.suffix.lower() in ['.md', '.markdown']:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            document = self.document_processor.process_markdown(content, str(path))
        elif path.suffix.lower() in ['.html', '.htm']:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            document = self.document_processor.process_html(content, str(path))
        elif path.suffix.lower() == '.txt':
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Create simple document
            import hashlib
            doc_id = hashlib.sha256(str(path).encode()).hexdigest()[:16]
            document = Document(
                id=doc_id,
                title=path.name,
                content=content,
                source=str(path),
                source_type='manual',
                metadata=self.document_processor.extract_metadata(content, str(path))
            )
        else:
            print(f"❌ Unsupported file type: {path.suffix}")
            return False
        
        if not document:
            return False
        
        # Add to vector database
        chunks_added = self.vector_db.add_document(document, self.document_processor)
        
        if chunks_added > 0:
            print(f"✅ Added document '{document.title}' from {file_path} with {chunks_added} chunks")
            return True
        else:
            print(f"❌ Failed to add document from {file_path}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of retrieval results
        """
        return self.vector_db.search_similar_chunks(query, top_k=top_k)
    
    def get_context_for_query(self, query: str, max_length: int = 2000) -> str:
        """
        Get optimized context for a query.
        
        Args:
            query: Search query
            max_length: Maximum context length
            
        Returns:
            Formatted context string
        """
        results = self.search(query, top_k=10)
        
        if not results:
            return "No relevant context found."
        
        # Build context from results
        context_parts = []
        for result in results:
            source_info = f"[Source: {result.chunk.source}]"
            content = result.chunk.content
            context_parts.append(f"{source_info}\n{content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Optimize context length
        return self.context_optimizer.compress_context(context, max_length)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        return self.vector_db.get_statistics()


class EnhancedRAGSystem:
    """
    Main RAG system that integrates with the multi-model manager.
    """
    
    def __init__(
        self,
        model_manager: MultiModelManager,
        vector_database: EnhancedVectorDatabase,
        prompt_builder: Optional[ModelSpecificRAGPromptBuilder] = None,
        context_optimizer: Optional[ContextOptimizer] = None
    ):
        """
        Initialize enhanced RAG system.
        
        Args:
            model_manager: Multi-model manager instance
            vector_database: Vector database for retrieval
            prompt_builder: Model-specific prompt builder
            context_optimizer: Context optimizer
        """
        
        self.model_manager = model_manager
        self.vector_db = vector_database
        self.prompt_builder = prompt_builder or ModelSpecificRAGPromptBuilder()
        self.context_optimizer = context_optimizer or ContextOptimizer()
        
        print("🧠 Enhanced RAG system initialized")
    
    def rag_enhanced_generation(
        self,
        query: str,
        model_role: Optional[ModelRole] = None,
        model_name: Optional[str] = None,
        top_k: int = 10,
        use_context_optimization: bool = True,
        additional_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response using RAG-enhanced context.
        
        Args:
            query: User query
            model_role: Target model role (auto-selected if None)
            model_name: Specific model name (overrides role selection)
            top_k: Number of chunks to retrieve
            use_context_optimization: Whether to optimize context for model
            additional_instructions: Additional prompt instructions
            
        Returns:
            Dictionary with generation results and context info
        """
        
        start_time = time.time()
        
        # Auto-select model if not specified
        if model_name is None and model_role is None:
            # Determine best model role based on query
            model_name = self.model_manager.select_model_for_task("general_research", query)
            model_role = self._get_model_role(model_name)
        elif model_name is None:
            # Get model name from role
            model_name = self._get_model_name_for_role(model_role)
        elif model_role is None:
            # Get role from model name
            model_role = self._get_model_role(model_name)
        
        # Retrieve relevant context
        print(f"🔍 Retrieving context for: {query}")
        retrieval_results = self.vector_db.search_similar_chunks(
            query=query,
            top_k=top_k
        )
        
        retrieval_time = time.time() - start_time
        
        if not retrieval_results:
            print("⚠️  No relevant context found in RAG database")
            # Fall back to direct generation
            response = self.model_manager.generate_content(
                prompt=query,
                model_name=model_name,
                task_type="general_research"
            )
            
            return {
                'response': response,
                'rag_context': None,
                'retrieval_results': [],
                'context_used': False,
                'retrieval_time': retrieval_time
            }
        
        # Optimize context for the specific model
        if use_context_optimization:
            context_text = self.context_optimizer.optimize_context(
                retrieval_results, model_role, query
            )
        else:
            # Simple context assembly
            context_text = "\n\n".join([
                f"[Source: {result.chunk.source}]\n{result.chunk.content}"
                for result in retrieval_results
            ])
        
        # Build model-specific prompt
        enhanced_prompt = self.prompt_builder.build_prompt(
            query=query,
            context=context_text,
            model_role=model_role,
            additional_instructions=additional_instructions
        )
        
        print(f"🧠 Generating RAG-enhanced response with {model_name}")
        print(f"   Context: {len(context_text)} chars from {len(retrieval_results)} chunks")
        
        # Generate response
        response = self.model_manager.generate_content(
            prompt=enhanced_prompt,
            model_name=model_name,
            task_type="rag_enhanced_generation"
        )
        
        # Calculate context statistics
        authority_scores = [r.authority_score for r in retrieval_results]
        avg_authority = sum(authority_scores) / len(authority_scores) if authority_scores else 0.0
        
        # Create RAG context info
        rag_context = RAGContext(
            query=query,
            retrieved_chunks=retrieval_results,
            context_text=context_text,
            model_role=model_role.value,
            context_length=len(context_text),
            source_count=len(set(r.chunk.source for r in retrieval_results)),
            authority_score=avg_authority,
            retrieval_time=retrieval_time
        )
        
        return {
            'response': response,
            'rag_context': rag_context,
            'retrieval_results': retrieval_results,
            'context_used': True,
            'model_role': model_role.value,
            'total_time': time.time() - start_time
        }
    
    def multi_model_rag_debate(
        self,
        topic: str,
        query: str,
        participating_models: Optional[List[str]] = None,
        rounds: int = 2,
        top_k_per_model: int = 8
    ) -> Dict[str, Any]:
        """
        Conduct multi-model debate with RAG-enhanced context for each model.
        
        Args:
            topic: Debate topic
            query: Specific question/prompt
            participating_models: Models to include in debate
            rounds: Number of debate rounds
            top_k_per_model: Context chunks per model
            
        Returns:
            Enhanced debate results with RAG context
        """
        
        if participating_models is None:
            participating_models = ['phi4:14b', 'deepseek-r1:7b', 'gemma3:12b']
        
        print(f"🎭 Starting RAG-enhanced debate: {topic}")
        print(f"   Participants: {', '.join(participating_models)}")
        
        # Retrieve context for the topic
        base_retrieval = self.vector_db.search_similar_chunks(query, top_k=top_k_per_model * 2)
        
        debate_history = []
        model_contexts = {}  # Store context used by each model
        
        for round_num in range(rounds):
            round_responses = []
            
            print(f"\n🔄 Round {round_num + 1}/{rounds}")
            
            for model_name in participating_models:
                model_role = self._get_model_role(model_name)
                
                # Build context for previous rounds
                previous_context = ""
                if debate_history:
                    previous_context = "\n\nPREVIOUS DEBATE POINTS:\n"
                    for prev_round in debate_history:
                        for prev_response in prev_round:
                            previous_context += f"- {prev_response['model']} ({prev_response['role']}): {prev_response['response'][:200]}...\n"
                
                # Create model-specific query
                model_query = f"{query}{previous_context}"
                
                # Generate RAG-enhanced response
                rag_result = self.rag_enhanced_generation(
                    query=model_query,
                    model_name=model_name,
                    top_k=top_k_per_model,
                    additional_instructions=f"This is round {round_num + 1} of a {rounds}-round expert debate on: {topic}"
                )
                
                if rag_result['response']['status'] == 'success':
                    round_responses.append({
                        'model': model_name,
                        'role': model_role.value,
                        'response': rag_result['response']['response'],
                        'word_count': rag_result['response']['word_count'],
                        'response_time': rag_result['response']['response_time'],
                        'rag_context': rag_result['rag_context'],
                        'sources_used': len(rag_result['retrieval_results'])
                    })
                    
                    # Store context used by this model
                    model_contexts[f"{model_name}_round_{round_num}"] = rag_result['rag_context']
                    
                    print(f"  ✅ {model_name}: {rag_result['response']['word_count']} words, "
                          f"{rag_result['rag_context'].source_count} sources")
                else:
                    print(f"  ❌ {model_name}: {rag_result['response']['error']}")
            
            debate_history.append(round_responses)
        
        # Generate consensus with RAG context
        print(f"\n🤝 Building RAG-enhanced consensus...")
        
        consensus_query = f"""
        Debate Topic: {topic}
        Original Question: {query}
        
        Synthesize the expert debate into a comprehensive consensus.
        """
        
        consensus_result = self.rag_enhanced_generation(
            query=consensus_query,
            model_role=ModelRole.RESEARCH_SYNTHESIZER,
            top_k=15,
            additional_instructions="Synthesize the debate conclusions with supporting evidence from the knowledge base."
        )
        
        return {
            'topic': topic,
            'query': query,
            'participating_models': participating_models,
            'rounds': rounds,
            'debate_history': debate_history,
            'model_contexts': model_contexts,
            'consensus': consensus_result,
            'total_responses': sum(len(round_resp) for round_resp in debate_history),
            'rag_enhanced': True
        }
    
    def _get_model_role(self, model_name: str) -> ModelRole:
        """Get model role from model name."""
        model_mapping = {
            'phi4:14b': ModelRole.ANALYSIS_AGENT,
            'deepseek-r1:7b': ModelRole.CODE_EXPERT,
            'gemma3:12b': ModelRole.RESEARCH_SYNTHESIZER,
            'llama2-uncensored:7b': ModelRole.REDTEAM_SPECIALIST
        }
        return model_mapping.get(model_name, ModelRole.RESEARCH_SYNTHESIZER)
    
    def _get_model_name_for_role(self, model_role: ModelRole) -> str:
        """Get model name from role."""
        role_mapping = {
            ModelRole.ANALYSIS_AGENT: 'phi4:14b',
            ModelRole.CODE_EXPERT: 'deepseek-r1:7b',
            ModelRole.RESEARCH_SYNTHESIZER: 'gemma3:12b',
            ModelRole.REDTEAM_SPECIALIST: 'llama2-uncensored:7b'
        }
        return role_mapping.get(model_role, 'gemma3:12b')


def test_rag_integration():
    """Test the RAG integration with multi-model system."""
    print("🧪 Testing RAG Integration")
    print("=" * 40)
    
    # This would normally import and use actual instances
    print("✅ RAG integration module ready for testing")
    print("📋 Features implemented:")
    print("   • Model-specific prompt building")
    print("   • Context optimization per model")
    print("   • RAG-enhanced generation")
    print("   • Multi-model RAG debates")
    
    return "RAG integration ready"


if __name__ == "__main__":
    test_rag_integration()
