"""
Service Check Script

This script performs detailed health checks on all RAG system services
and reports their status.
"""

import asyncio
import httpx
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.cli_tester.main import Colors


class ServiceChecker:
    """Detailed service health checker"""
    
    def __init__(self):
        self.services = {
            "Gateway": "http://localhost:8000",
            "Retrieval": "http://localhost:8001",
            "Ingestion": "http://localhost:8002",
            "Embedding": "http://localhost:8003",
            "Qdrant": "http://localhost:6333",
            "Ollama": "http://localhost:11434",
        }
        self.results = {}
    
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    async def check_service(self, name: str, url: str) -> dict:
        """Check a single service"""
        result = {
            "name": name,
            "url": url,
            "status": "Unknown",
            "details": "",
            "healthy": False
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Try health endpoint first
                try:
                    response = await client.get(f"{url}/health", timeout=5.0)
                    if response.status_code == 200:
                        result["status"] = "OK"
                        result["healthy"] = True
                        data = response.json()
                        result["details"] = str(data)
                    else:
                        result["status"] = f"Unhealthy (HTTP {response.status_code})"
                        result["details"] = response.text[:100]
                except httpx.HTTPStatusError as e:
                    result["status"] = f"Error (HTTP {e.response.status_code})"
                    result["details"] = str(e)[:100]
                except Exception:
                    # Try root endpoint for services without /health
                    try:
                        response = await client.get(url, timeout=5.0)
                        if response.status_code in [200, 404]:  # 404 is ok for some services
                            result["status"] = "Running"
                            result["healthy"] = True
                            result["details"] = f"HTTP {response.status_code}"
                        else:
                            result["status"] = f"Unexpected (HTTP {response.status_code})"
                    except Exception as e:
                        result["status"] = "Not Reachable"
                        result["details"] = str(e)[:100]
        
        except Exception as e:
            result["status"] = "Error"
            result["details"] = str(e)[:100]
        
        return result
    
    async def check_ollama_models(self) -> dict:
        """Check Ollama models"""
        result = {
            "models": [],
            "error": None
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    result["models"] = [model.get("name", "unknown") for model in data.get("models", [])]
                else:
                    result["error"] = f"HTTP {response.status_code}"
        except Exception as e:
            result["error"] = str(e)[:100]
        
        return result
    
    async def check_qdrant_collections(self) -> dict:
        """Check Qdrant collections"""
        result = {
            "collections": [],
            "error": None
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:6333/collections", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    collections = data.get("result", {}).get("collections", [])
                    result["collections"] = [c.get("name", "unknown") for c in collections]
                else:
                    result["error"] = f"HTTP {response.status_code}"
        except Exception as e:
            result["error"] = str(e)[:100]
        
        return result
    
    async def run_checks(self):
        """Run all service checks"""
        self.print_header("RAG System Service Health Check")
        
        print(f"{Colors.BOLD}Checking all services...{Colors.ENDC}\n")
        
        # Check all services
        tasks = [self.check_service(name, url) for name, url in self.services.items()]
        results = await asyncio.gather(*tasks)
        
        # Display results
        healthy_count = 0
        for result in results:
            self.results[result["name"]] = result
            
            if result["healthy"]:
                print(f"{Colors.OKGREEN}✓{Colors.ENDC} {result['name']:15} {Colors.OKGREEN}{result['status']}{Colors.ENDC}")
                healthy_count += 1
            else:
                print(f"{Colors.FAIL}✗{Colors.ENDC} {result['name']:15} {Colors.FAIL}{result['status']}{Colors.ENDC}")
            
            if result["details"]:
                print(f"  {Colors.OKCYAN}└─{Colors.ENDC} {result['details'][:80]}")
        
        # Check Ollama models
        print(f"\n{Colors.BOLD}Checking Ollama models...{Colors.ENDC}")
        ollama_models = await self.check_ollama_models()
        if ollama_models["error"]:
            print(f"{Colors.FAIL}✗ Error: {ollama_models['error']}{Colors.ENDC}")
        elif not ollama_models["models"]:
            print(f"{Colors.WARNING}⚠ No models installed{Colors.ENDC}")
            print(f"  {Colors.OKCYAN}└─ Install a model with: ollama pull llama3{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}✓ Models installed: {', '.join(ollama_models['models'])}{Colors.ENDC}")
        
        # Check Qdrant collections
        print(f"\n{Colors.BOLD}Checking Qdrant collections...{Colors.ENDC}")
        qdrant_collections = await self.check_qdrant_collections()
        if qdrant_collections["error"]:
            print(f"{Colors.FAIL}✗ Error: {qdrant_collections['error']}{Colors.ENDC}")
        elif not qdrant_collections["collections"]:
            print(f"{Colors.WARNING}⚠ No collections found{Colors.ENDC}")
            print(f"  {Colors.OKCYAN}└─ Upload a document to create collections{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}✓ Collections: {', '.join(qdrant_collections['collections'])}{Colors.ENDC}")
        
        # Summary
        self.print_header("Summary")
        total = len(self.services)
        print(f"Services checked: {total}")
        print(f"{Colors.OKGREEN}Healthy: {healthy_count}{Colors.ENDC}")
        print(f"{Colors.FAIL}Unhealthy: {total - healthy_count}{Colors.ENDC}")
        
        if healthy_count == total:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ All services are running!{Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ Some services need attention{Colors.ENDC}")
        
        # Recommendations
        if not self.results.get("Ollama", {}).get("healthy"):
            print(f"\n{Colors.WARNING}Recommendation:{Colors.ENDC}")
            print(f"  • Start Ollama service")
        elif not ollama_models["models"]:
            print(f"\n{Colors.WARNING}Recommendation:{Colors.ENDC}")
            print(f"  • Install Ollama model: {Colors.OKCYAN}ollama pull llama3{Colors.ENDC}")
        
        if not self.results.get("Qdrant", {}).get("healthy"):
            print(f"\n{Colors.WARNING}Recommendation:{Colors.ENDC}")
            print(f"  • Start Qdrant: {Colors.OKCYAN}uv run poe start-infra{Colors.ENDC}")


async def main():
    """Main entry point"""
    checker = ServiceChecker()
    await checker.run_checks()


if __name__ == "__main__":
    asyncio.run(main())
