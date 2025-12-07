"""
Demo script for CLI Tester

This script demonstrates the CLI Tester functionality by running
a series of automated tests.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import the main module
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.cli_tester.main import RAGTester, Colors


async def run_demo():
    """Run automated demo of CLI Tester functionality"""
    tester = RAGTester()
    
    # Print demo header
    tester.print_header("CLI Tester Automated Demo")
    print(f"This demo will showcase the CLI Tester's capabilities.\n")
    
    # Step 1: Health Check
    print(f"\n{Colors.BOLD}Step 1: Checking Service Health{Colors.ENDC}")
    print("-" * 60)
    healthy = await tester.check_services()
    
    if not healthy:
        tester.print_warning("Some services are not available. Demo will continue anyway.")
    
    await asyncio.sleep(2)
    
    # Step 2: Chat Test
    print(f"\n{Colors.BOLD}Step 2: Testing Chat Functionality{Colors.ENDC}")
    print("-" * 60)
    
    test_queries = [
        "What is machine learning?",
        "Explain the main findings of the research.",
        "What are the key contributions?"
    ]
    
    for query in test_queries:
        await tester.chat(query)
        await asyncio.sleep(2)
    
    # Step 3: Show History
    print(f"\n{Colors.BOLD}Step 3: Viewing Conversation History{Colors.ENDC}")
    print("-" * 60)
    tester.show_history()
    
    await asyncio.sleep(2)
    
    # Step 4: Summary
    tester.print_header("Demo Summary")
    print(f"✓ Tested service health checks")
    print(f"✓ Tested chat functionality with {len(test_queries)} queries")
    print(f"✓ Tested conversation history")
    print(f"\nTotal conversations: {len(tester.conversation_history)}")
    
    if tester.conversation_history:
        total_citations = sum(len(conv['citations']) for conv in tester.conversation_history)
        print(f"Total citations retrieved: {total_citations}")
    
    print(f"\n{Colors.OKGREEN}Demo completed successfully!{Colors.ENDC}")
    print(f"\nTo run the interactive CLI Tester, use: {Colors.OKCYAN}uv run poe test-cli{Colors.ENDC}")


if __name__ == "__main__":
    asyncio.run(run_demo())
