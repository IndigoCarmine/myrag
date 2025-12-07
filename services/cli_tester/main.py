"""
CLI Tester Service

This service provides a command-line interface to test the RAG system,
simulating the same interactions that the Frontend performs.
It allows testing of:
1. Chat functionality (Gateway Service)
2. Document upload functionality (Ingestion Service)
"""

import os
import sys
import httpx
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import json


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class RAGTester:
    """Interactive CLI tester for the RAG system"""
    
    def __init__(self):
        self.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8000")
        self.ingestion_url = os.getenv("INGESTION_URL", "http://localhost:8002")
        self.conversation_history: List[Dict[str, Any]] = []
    
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    
    async def check_services(self) -> bool:
        """Check if all required services are running"""
        self.print_header("Service Health Check")
        
        all_healthy = True
        
        # Check Gateway Service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.gateway_url}/health", timeout=5.0)
                if response.status_code == 200:
                    self.print_success(f"Gateway Service (Port 8000): OK")
                else:
                    self.print_error(f"Gateway Service (Port 8000): Unhealthy")
                    all_healthy = False
        except Exception as e:
            self.print_error(f"Gateway Service (Port 8000): Not reachable - {e}")
            all_healthy = False
        
        # Check Ingestion Service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ingestion_url}/health", timeout=5.0)
                if response.status_code == 200:
                    self.print_success(f"Ingestion Service (Port 8002): OK")
                else:
                    self.print_error(f"Ingestion Service (Port 8002): Unhealthy")
                    all_healthy = False
        except Exception as e:
            self.print_error(f"Ingestion Service (Port 8002): Not reachable - {e}")
            all_healthy = False
        
        return all_healthy
    
    async def chat(self, query: str):
        """Send a chat message to the Gateway Service"""
        self.print_header("Chat Request")
        self.print_info(f"Query: {query}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.gateway_url}/chat",
                    json={"query": query},
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display answer
                    print(f"\n{Colors.BOLD}Answer:{Colors.ENDC}")
                    print(f"{data.get('answer', 'No answer received')}\n")
                    
                    # Display citations
                    citations = data.get('citations', [])
                    if citations:
                        print(f"{Colors.BOLD}📚 Sources ({len(citations)}):{Colors.ENDC}")
                        for idx, citation in enumerate(citations, 1):
                            print(f"\n{Colors.OKCYAN}[{idx}] {citation.get('title', citation.get('doi'))}{Colors.ENDC}")
                            
                            if citation.get('authors'):
                                authors = citation['authors'][:3]
                                author_str = ', '.join(authors)
                                if len(citation['authors']) > 3:
                                    author_str += ' et al.'
                                print(f"    Authors: {author_str}")
                            
                            if citation.get('journal'):
                                print(f"    Journal: {citation['journal']}")
                            
                            if citation.get('published_date'):
                                print(f"    Published: {citation['published_date']}")
                            
                            print(f"    DOI: {citation.get('doi')}")
                            print(f"    URL: {citation.get('url')}")
                            
                            if citation.get('pages'):
                                print(f"    Pages: {', '.join(map(str, citation['pages']))}")
                            
                            if citation.get('pdf_url'):
                                print(f"    PDF: {citation['pdf_url']}")
                    
                    # Save to history
                    self.conversation_history.append({
                        "query": query,
                        "answer": data.get('answer'),
                        "citations": citations
                    })
                    
                    self.print_success("Chat request completed successfully")
                else:
                    self.print_error(f"Chat request failed with status {response.status_code}")
                    print(f"Response: {response.text}")
        
        except Exception as e:
            self.print_error(f"Chat request failed: {e}")
    
    async def upload_document(self, file_path: str):
        """Upload a PDF document to the Ingestion Service"""
        self.print_header("Document Upload")
        
        path = Path(file_path)
        
        if not path.exists():
            self.print_error(f"File not found: {file_path}")
            return
        
        if not path.suffix.lower() == '.pdf':
            self.print_error(f"File must be a PDF: {file_path}")
            return
        
        self.print_info(f"Uploading: {path.name}")
        self.print_info(f"Size: {path.stat().st_size / 1024:.2f} KB")
        
        try:
            async with httpx.AsyncClient() as client:
                with open(file_path, 'rb') as f:
                    files = {'file': (path.name, f, 'application/pdf')}
                    
                    response = await client.post(
                        f"{self.ingestion_url}/ingest",
                        files=files,
                        timeout=120.0  # PDF processing can take time
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    self.print_success("Document uploaded and processed successfully")
                    
                    # Display processing details if available
                    if 'chunks_created' in data:
                        self.print_info(f"Chunks created: {data['chunks_created']}")
                    if 'metadata' in data:
                        print(f"\n{Colors.BOLD}Metadata:{Colors.ENDC}")
                        for key, value in data['metadata'].items():
                            print(f"  {key}: {value}")
                else:
                    self.print_error(f"Upload failed with status {response.status_code}")
                    print(f"Response: {response.text}")
        
        except Exception as e:
            self.print_error(f"Upload failed: {e}")
    
    def show_history(self):
        """Display conversation history"""
        self.print_header("Conversation History")
        
        if not self.conversation_history:
            self.print_info("No conversation history yet")
            return
        
        for idx, item in enumerate(self.conversation_history, 1):
            print(f"\n{Colors.BOLD}[{idx}] Query:{Colors.ENDC} {item['query']}")
            print(f"{Colors.BOLD}    Answer:{Colors.ENDC} {item['answer'][:100]}...")
            if item['citations']:
                print(f"{Colors.BOLD}    Citations:{Colors.ENDC} {len(item['citations'])} sources")
    
    def show_menu(self):
        """Display the main menu"""
        print(f"\n{Colors.BOLD}Available Commands:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}chat{Colors.ENDC}     - Send a chat message")
        print(f"  {Colors.OKCYAN}upload{Colors.ENDC}   - Upload a PDF document")
        print(f"  {Colors.OKCYAN}history{Colors.ENDC}  - View conversation history")
        print(f"  {Colors.OKCYAN}health{Colors.ENDC}   - Check service health")
        print(f"  {Colors.OKCYAN}help{Colors.ENDC}     - Show this menu")
        print(f"  {Colors.OKCYAN}quit{Colors.ENDC}     - Exit the tester")
        print()
    
    async def run(self):
        """Run the interactive CLI tester"""
        self.print_header("RAG System CLI Tester")
        print(f"{Colors.BOLD}Welcome to the RAG System CLI Tester!{Colors.ENDC}")
        print(f"This tool simulates the same interactions as the Frontend.\n")
        
        # Initial health check
        await self.check_services()
        
        self.show_menu()
        
        while True:
            try:
                command = input(f"{Colors.BOLD}> {Colors.ENDC}").strip().lower()
                
                if not command:
                    continue
                
                if command == 'quit' or command == 'exit':
                    self.print_info("Goodbye!")
                    break
                
                elif command == 'help':
                    self.show_menu()
                
                elif command == 'health':
                    await self.check_services()
                
                elif command == 'history':
                    self.show_history()
                
                elif command == 'chat':
                    query = input(f"{Colors.OKCYAN}Enter your question: {Colors.ENDC}").strip()
                    if query:
                        await self.chat(query)
                    else:
                        self.print_warning("Query cannot be empty")
                
                elif command == 'upload':
                    file_path = input(f"{Colors.OKCYAN}Enter PDF file path: {Colors.ENDC}").strip()
                    if file_path:
                        # Remove quotes if present
                        file_path = file_path.strip('"').strip("'")
                        await self.upload_document(file_path)
                    else:
                        self.print_warning("File path cannot be empty")
                
                else:
                    self.print_warning(f"Unknown command: {command}")
                    self.print_info("Type 'help' to see available commands")
            
            except KeyboardInterrupt:
                print()
                self.print_info("Use 'quit' to exit")
            except Exception as e:
                self.print_error(f"Unexpected error: {e}")


async def main():
    """Main entry point"""
    tester = RAGTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())
