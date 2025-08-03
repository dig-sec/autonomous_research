#!/usr/bin/env python3
"""
Test script to verify all local models are working properly.
"""

import requests
import time
import json
from typing import Dict, List, Optional


class ModelTester:
    """Test suite for local Ollama models."""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.api_url = f"{ollama_host}/api/generate"
        
    def test_model(self, model_name: str, test_prompt: Optional[str] = None) -> Dict:
        """Test a specific model with a security-focused prompt."""
        
        if test_prompt is None:
            test_prompt = (
                "Briefly explain the MITRE ATT&CK technique T1003 (OS Credential Dumping). "
                "Include the main attack methods and one detection strategy."
            )
        
        payload = {
            "model": model_name,
            "prompt": test_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "max_tokens": 500
            }
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.api_url, 
                json=payload, 
                timeout=60
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                return {
                    'status': 'success',
                    'model': model_name,
                    'response_time': round(response_time, 2),
                    'response_length': len(response_text),
                    'word_count': len(response_text.split()),
                    'response_preview': response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    'full_response': response_text
                }
            else:
                return {
                    'status': 'error',
                    'model': model_name,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'response_time': round(response_time, 2)
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'model': model_name,
                'error': 'Request timed out after 60 seconds'
            }
        except Exception as e:
            return {
                'status': 'error',
                'model': model_name,
                'error': str(e)
            }
    
    def test_all_models(self) -> List[Dict]:
        """Test all specified models."""
        
        models_to_test = [
            "phi4:14b",
            "deepseek-r1:7b", 
            "gemma3:12b",
            "llama2-uncensored:7b"
        ]
        
        results = []
        
        print("🧪 Testing Local LLM Models for Security Research")
        print("=" * 60)
        
        for i, model in enumerate(models_to_test, 1):
            print(f"\n[{i}/{len(models_to_test)}] Testing {model}...")
            
            result = self.test_model(model)
            results.append(result)
            
            # Print immediate feedback
            if result['status'] == 'success':
                print(f"✅ {model}: Working ({result['response_time']}s, {result['word_count']} words)")
                print(f"📝 Preview: {result['response_preview']}")
            else:
                print(f"❌ {model}: {result['error']}")
            
            # Small delay between tests
            time.sleep(1)
        
        return results
    
    def analyze_results(self, results: List[Dict]):
        """Analyze and summarize test results."""
        
        print("\n" + "=" * 60)
        print("📊 MODEL PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] != 'success']
        
        print(f"\n✅ Working Models: {len(successful)}/{len(results)}")
        print(f"❌ Failed Models: {len(failed)}/{len(results)}")
        
        if successful:
            print("\n🚀 SUCCESSFUL MODELS:")
            print("-" * 40)
            
            # Sort by response time
            successful.sort(key=lambda x: x['response_time'])
            
            for result in successful:
                print(f"• {result['model']}")
                print(f"  ⏱️  Response Time: {result['response_time']}s")
                print(f"  📝 Word Count: {result['word_count']}")
                print(f"  💭 Quality: {'High' if result['word_count'] > 50 else 'Low'}")
                print()
        
        if failed:
            print("🚨 FAILED MODELS:")
            print("-" * 40)
            for result in failed:
                print(f"• {result['model']}: {result['error']}")
        
        # Recommendations
        print("\n🎯 RECOMMENDATIONS:")
        print("-" * 40)
        
        if len(successful) >= 2:
            fastest = min(successful, key=lambda x: x['response_time'])
            most_verbose = max(successful, key=lambda x: x['word_count'])
            
            print(f"🏃 Fastest Model: {fastest['model']} ({fastest['response_time']}s)")
            print(f"📚 Most Detailed: {most_verbose['model']} ({most_verbose['word_count']} words)")
            
            print(f"\n💡 Suggested Roles:")
            
            # Role suggestions based on model characteristics
            for result in successful:
                model = result['model']
                if 'phi4' in model:
                    print(f"  {model} → Complex Analysis & Strategic Thinking")
                elif 'deepseek' in model:
                    print(f"  {model} → Code Analysis & Technical Implementation")
                elif 'gemma' in model:
                    print(f"  {model} → Research Synthesis & Documentation")
                elif 'llama2-uncensored' in model:
                    print(f"  {model} → Red Team Analysis & Adversarial TTPs")
                else:
                    print(f"  {model} → General Purpose")
        
        elif len(successful) == 1:
            print("⚠️  Only one model working - consider installing additional models")
        else:
            print("🚨 No models working - check Ollama installation")
            print("   Run: ollama list")
            print("   Install models: ollama pull <model-name>")
    
    def specialized_tests(self):
        """Run specialized tests for each model type."""
        
        print("\n" + "=" * 60)
        print("🎯 SPECIALIZED MODEL TESTS")
        print("=" * 60)
        
        specialized_prompts = {
            "phi4:14b": "Analyze the strategic implications of supply chain attacks in enterprise environments. Consider threat actor motivations, attack vectors, and long-term defensive strategies.",
            
            "deepseek-r1:7b": "Write a Python function that detects process injection techniques by monitoring for specific Windows API calls. Include error handling and comments.",
            
            "gemma3:12b": "Synthesize information from multiple sources: How do the MITRE ATT&CK framework, NIST Cybersecurity Framework, and ISO 27001 complement each other in enterprise security?",
            
            "llama2-uncensored:7b": "Describe advanced evasion techniques used by sophisticated threat actors to bypass endpoint detection and response (EDR) systems. Include specific technical methods."
        }
        
        for model, prompt in specialized_prompts.items():
            print(f"\n🔬 Testing {model} Specialization:")
            print(f"📋 Task: {prompt[:80]}...")
            
            result = self.test_model(model, prompt)
            
            if result['status'] == 'success':
                print(f"✅ Response ({result['response_time']}s, {result['word_count']} words)")
                print(f"📄 Quality Assessment:")
                
                response = result['full_response'].lower()
                
                # Simple quality heuristics
                technical_terms = ['api', 'dll', 'registry', 'memory', 'process', 'kernel', 'payload']
                security_terms = ['attack', 'defense', 'detection', 'mitigation', 'threat', 'vulnerability']
                
                tech_score = sum(1 for term in technical_terms if term in response)
                sec_score = sum(1 for term in security_terms if term in response)
                
                print(f"   Technical Depth: {tech_score}/7")
                print(f"   Security Focus: {sec_score}/6")
                print(f"   Overall Quality: {'High' if (tech_score + sec_score) > 6 else 'Medium' if (tech_score + sec_score) > 3 else 'Basic'}")
            else:
                print(f"❌ Failed: {result['error']}")


def main():
    """Run the complete model test suite."""
    
    print("🚀 Autonomous Research System - Model Test Suite")
    print("Testing local models for security research capabilities...\n")
    
    tester = ModelTester()
    
    # Test basic functionality
    results = tester.test_all_models()
    
    # Analyze results
    tester.analyze_results(results)
    
    # Run specialized tests if any models are working
    successful_models = [r for r in results if r['status'] == 'success']
    if successful_models:
        tester.specialized_tests()
    
    print("\n" + "=" * 60)
    print("🎉 MODEL TESTING COMPLETE")
    print("=" * 60)
    
    if len(successful_models) >= 2:
        print("✅ You're ready to implement multi-model debates!")
        print("📋 Next steps:")
        print("   1. Review QUICK_START_IMPLEMENTATION.md")
        print("   2. Implement MultiModelManager")
        print("   3. Start with GitHub intelligence integration")
    elif len(successful_models) == 1:
        print("⚠️  Limited to single-model operation")
        print("📋 Consider installing additional models for debates")
    else:
        print("🚨 No working models found")
        print("📋 Check Ollama installation and model availability")


if __name__ == "__main__":
    main()
