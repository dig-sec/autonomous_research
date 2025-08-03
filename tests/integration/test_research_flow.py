"""
Autonomous Research Integration Test

Demonstrates the full workflow combining:
- MultiModelManager for specialized AI analysis
- GitHub Intelligence for repository research
- Debate system for consensus building

This implements the core vision from PROJECT_TODO.md
"""

import sys
import os
import time
from typing import Dict, List, Optional

project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
src_path = os.path.join(project_root, 'src')
if os.path.exists(src_path):
    sys.path.insert(0, src_path)

try:
    from autonomous_research.models.model_manager import MultiModelManager
    from autonomous_research.research.github_intel import GitHubIntelligence
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'autonomous_research'))
    from models.model_manager import MultiModelManager
    from research.github_intel import GitHubIntelligence


class IntegratedSecurityResearch:
    """
    Integrated security research system combining multiple AI models and GitHub intelligence.
    
    This demonstrates the PROJECT_TODO.md vision of leveraging:
    - phi4:14b for complex analysis
    - deepseek-r1:7b for code expertise  
    - gemma3:12b for research synthesis
    - llama2-uncensored:7b for red team analysis
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize the integrated research system."""
        
        print("🚀 Initializing Integrated Security Research System")
        print("=" * 60)
        
        # Initialize components
        self.model_manager = MultiModelManager()
        self.github_intel = GitHubIntelligence(github_token)
        
        print("✅ All components initialized successfully!")
        print()

    def research_security_technique(
        self,
        technique_id: str,
        technique_name: str,
        max_repos: int = 10
    ) -> Dict:
        """
        Conduct comprehensive research on a security technique.
        
        Args:
            technique_id: MITRE ATT&CK technique ID (e.g., "T1003")
            technique_name: Human-readable technique name
            max_repos: Maximum repositories to analyze
            
        Returns:
            Comprehensive research results
        """
        
        print(f"🎯 COMPREHENSIVE SECURITY TECHNIQUE RESEARCH")
        print(f"📋 Technique: {technique_id} - {technique_name}")
        print("=" * 60)
        
        research_results = {
            'technique_id': technique_id,
            'technique_name': technique_name,
            'github_repositories': [],
            'ai_analysis': {},
            'debate_results': {},
            'final_synthesis': {},
            'timestamp': time.time()
        }
        
        # Phase 1: GitHub Intelligence Gathering
        print("🔍 Phase 1: GitHub Repository Research")
        print("-" * 40)
        
        repos = self.github_intel.search_security_repositories(
            technique_name,
            technique_id=technique_id,
            max_results=max_repos
        )
        
        if repos:
            print(f"✅ Found {len(repos)} repositories")
            
            # Analyze top repositories
            for i, repo in enumerate(repos[:3], 1):
                print(f"  {i}. {repo['full_name']} (⭐{repo['stars']}, Score: {repo['security_score']:.1f})")
                
                # Detailed analysis of top repository
                if i == 1:
                    detailed_analysis = self.github_intel.analyze_repository(repo['full_name'])
                    repo['detailed_analysis'] = detailed_analysis
            
            research_results['github_repositories'] = repos[:5]  # Keep top 5
        else:
            print("❌ No repositories found")
        
        # Phase 2: Multi-Model AI Analysis
        print(f"\n🤖 Phase 2: Multi-Model AI Analysis")
        print("-" * 40)
        
        # Generate specialized analysis from each model
        analysis_tasks = [
            {
                'model': 'phi4:14b',
                'role': 'Strategic Analysis',
                'task_type': 'threat_analysis',
                'prompt': f"""
                Analyze MITRE ATT&CK technique {technique_id} ({technique_name}) from a strategic security perspective.
                
                Please provide:
                1. Strategic threat assessment and risk implications
                2. Advanced detection strategies
                3. Recommended defensive measures
                4. Long-term security architecture considerations
                
                Focus on high-level strategic thinking and complex threat modeling.
                """
            },
            {
                'model': 'deepseek-r1:7b', 
                'role': 'Technical Implementation',
                'task_type': 'code_analysis',
                'prompt': f"""
                Analyze MITRE ATT&CK technique {technique_id} ({technique_name}) from a technical implementation perspective.
                
                Please provide:
                1. Technical implementation details and methods
                2. Code examples or pseudo-code for detection
                3. API calls and system interactions involved
                4. Forensic artifacts and evidence to look for
                
                Focus on technical depth and implementation specifics.
                """
            },
            {
                'model': 'llama2-uncensored:7b',
                'role': 'Red Team Perspective', 
                'task_type': 'red_team_analysis',
                'prompt': f"""
                Analyze MITRE ATT&CK technique {technique_id} ({technique_name}) from an adversarial/red team perspective.
                
                Please provide:
                1. Attack execution methods and variations
                2. Evasion techniques and detection bypasses
                3. Real-world usage by threat actors
                4. Advanced persistent threat (APT) implementations
                
                Focus on adversarial tactics and uncensored security analysis.
                """
            }
        ]
        
        # Execute analysis tasks
        for task in analysis_tasks:
            print(f"  🔬 {task['role']} ({task['model']})...")
            
            result = self.model_manager.generate_content(
                task['prompt'],
                model_name=task['model'],
                task_type=task['task_type']
            )
            
            if result['status'] == 'success':
                print(f"    ✅ Complete: {result['word_count']} words in {result['response_time']}s")
                research_results['ai_analysis'][task['role']] = {
                    'model': task['model'],
                    'response': result['response'],
                    'metrics': {
                        'word_count': result['word_count'],
                        'response_time': result['response_time']
                    }
                }
            else:
                print(f"    ❌ Failed: {result['error']}")
                research_results['ai_analysis'][task['role']] = {
                    'model': task['model'],
                    'error': result['error']
                }
        
        # Phase 3: Multi-Model Debate
        print(f"\n🎭 Phase 3: Multi-Model Expert Debate")
        print("-" * 40)
        
        debate_prompt = f"""
        Based on the research into MITRE ATT&CK technique {technique_id} ({technique_name}), 
        what are the most effective detection and prevention strategies for enterprise environments?
        
        Consider:
        - Implementation complexity vs effectiveness
        - False positive rates
        - Resource requirements
        - Evasion resistance
        """
        
        debate_results = self.model_manager.multi_model_debate(
            topic=f"{technique_id} Detection Strategies",
            debate_prompt=debate_prompt,
            participating_models=['phi4:14b', 'deepseek-r1:7b', 'llama2-uncensored:7b'],
            rounds=2
        )
        
        research_results['debate_results'] = debate_results
        
        print(f"✅ Debate completed: {debate_results['successful_responses']}/{debate_results['total_responses']} responses")
        
        # Phase 4: Final Synthesis
        print(f"\n📋 Phase 4: Research Synthesis")
        print("-" * 40)
        
        # Build comprehensive synthesis prompt
        synthesis_prompt = f"""
        Synthesize all research findings for MITRE ATT&CK technique {technique_id} ({technique_name}).
        
        GITHUB INTELLIGENCE:
        """
        
        if repos:
            synthesis_prompt += f"Found {len(repos)} relevant repositories:\n"
            for repo in repos[:3]:
                synthesis_prompt += f"- {repo['full_name']}: {repo['description'][:100]}...\n"
        
        synthesis_prompt += "\nAI ANALYSIS SUMMARY:\n"
        for role, analysis in research_results['ai_analysis'].items():
            if 'response' in analysis:
                synthesis_prompt += f"- {role}: {analysis['response'][:200]}...\n"
        
        synthesis_prompt += f"\nDEBATE CONSENSUS:\n"
        if debate_results.get('consensus', {}).get('status') == 'success':
            consensus_preview = debate_results['consensus']['response'][:300]
            synthesis_prompt += f"{consensus_preview}...\n"
        
        synthesis_prompt += """
        
        Please provide a comprehensive synthesis including:
        1. Executive summary of the technique and its implications
        2. Key findings from GitHub repository analysis
        3. Synthesis of multi-model AI analysis
        4. Consensus recommendations from the expert debate
        5. Actionable security recommendations
        6. Areas requiring further research
        
        Create a cohesive, comprehensive security intelligence report.
        """
        
        print("  📝 Generating final synthesis with gemma3:12b...")
        
        synthesis_result = self.model_manager.generate_content(
            synthesis_prompt,
            model_name='gemma3:12b',
            task_type='research_synthesis'
        )
        
        if synthesis_result['status'] == 'success':
            print(f"    ✅ Synthesis complete: {synthesis_result['word_count']} words")
            research_results['final_synthesis'] = synthesis_result
        else:
            print(f"    ❌ Synthesis failed: {synthesis_result['error']}")
            research_results['final_synthesis'] = {'error': synthesis_result['error']}
        
        return research_results

    def generate_research_report(self, research_results: Dict) -> str:
        """Generate a formatted research report."""
        
        technique_id = research_results['technique_id']
        technique_name = research_results['technique_name']
        
        report = f"""
# Security Intelligence Report: {technique_id} - {technique_name}

**Generated by Autonomous Research System**  
**Timestamp:** {time.ctime(research_results['timestamp'])}

## Executive Summary

{research_results.get('final_synthesis', {}).get('response', 'Synthesis not available')[:500]}...

## Repository Intelligence

**Found {len(research_results['github_repositories'])} relevant repositories:**

"""
        
        for i, repo in enumerate(research_results['github_repositories'][:5], 1):
            report += f"""
### {i}. [{repo['full_name']}]({repo['url']})
- **Stars:** {repo['stars']} | **Security Score:** {repo['security_score']:.1f}
- **Description:** {repo['description']}
- **Language:** {repo['language']} | **Last Updated:** {repo['updated_at'][:10]}
"""
        
        report += "\n## AI Analysis Results\n"
        
        for role, analysis in research_results['ai_analysis'].items():
            if 'response' in analysis:
                report += f"""
### {role} ({analysis['model']})
**Response Time:** {analysis['metrics']['response_time']}s | **Words:** {analysis['metrics']['word_count']}

{analysis['response'][:300]}...

"""
        
        debate = research_results.get('debate_results', {})
        if debate:
            report += f"""
## Expert Debate Results

**Topic:** {debate['topic']}  
**Participants:** {', '.join(debate['participating_models'])}  
**Rounds:** {debate['rounds']}  
**Success Rate:** {debate['successful_responses']}/{debate['total_responses']}

### Consensus
{debate.get('consensus', {}).get('response', 'No consensus available')[:400]}...

"""
        
        report += """
## Recommendations

Based on the comprehensive analysis combining GitHub intelligence, multi-model AI analysis, and expert debate:

1. **Immediate Actions:** Implement detection rules and monitoring
2. **Medium-term:** Enhance security architecture based on threat model
3. **Long-term:** Develop advanced detection and response capabilities

---

*This report was generated by the Autonomous Security Research System using multiple AI models and open source intelligence.*
"""
        
        return report


def main():
    """Main demonstration of the integrated research system."""
    
    print("🎯 AUTONOMOUS SECURITY RESEARCH DEMONSTRATION")
    print("Implementing PROJECT_TODO.md Phase 1-2 Integration")
    print("=" * 70)
    
    # Initialize system
    research_system = IntegratedSecurityResearch()
    
    # Research a specific technique
    technique_id = "T1003"
    technique_name = "OS Credential Dumping"
    
    print(f"\n🔬 Researching {technique_id}: {technique_name}")
    print("This demonstrates the full workflow from the PROJECT_TODO.md")
    print()
    
    # Conduct research
    results = research_system.research_security_technique(
        technique_id=technique_id,
        technique_name=technique_name,
        max_repos=5
    )
    
    # Generate report
    print(f"\n📄 Generating Research Report")
    print("-" * 40)
    
    report = research_system.generate_research_report(results)
    
    # Save report
    report_filename = f"research_report_{technique_id}_{int(time.time())}.md"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"✅ Report saved to: {report_filename}")
    
    # Show summary
    print(f"\n🎉 RESEARCH COMPLETE")
    print("=" * 40)
    print(f"Technique: {technique_id} - {technique_name}")
    print(f"Repositories analyzed: {len(results['github_repositories'])}")
    print(f"AI models used: {len(results['ai_analysis'])}")
    print(f"Debate rounds: {results.get('debate_results', {}).get('rounds', 0)}")
    
    # Show model performance
    print(f"\n📊 Model Performance:")
    stats = research_system.model_manager.get_model_statistics()
    for model, data in stats.items():
        if data['total_requests'] > 0:
            print(f"  {model}: {data['total_requests']} requests, {data['avg_response_time']}s avg")
    
    print(f"\n✨ This demonstrates the PROJECT_TODO.md vision in action!")
    print(f"🚀 Ready to implement the remaining phases!")


if __name__ == "__main__":
    main()
