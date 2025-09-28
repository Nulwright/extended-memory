#!/usr/bin/env python3
"""
Extended Sienna Memory CLI Tool

Usage:
    esm add <assistant> <content> [--type=<type>] [--importance=<imp>] [--tags=<tags>]
    esm search <assistant> <query> [--limit=<n>] [--semantic]
    esm list <assistant> [--limit=<n>] [--type=<type>]
    esm get <memory_id>
    esm update <memory_id> [--content=<content>] [--importance=<imp>]
    esm delete <memory_id>
    esm stats <assistant>
    esm export <assistant> [--format=<fmt>] [--output=<file>]
    esm import <assistant> <file> [--format=<fmt>]
    esm health
    esm --help
    esm --version

Options:
    --type=<type>           Memory type [default: general]
    --importance=<imp>      Importance (1-10) [default: 5]
    --tags=<tags>          Comma-separated tags
    --limit=<n>            Limit results [default: 10]
    --semantic             Use semantic search
    --format=<fmt>         Export/import format [default: json]
    --output=<file>        Output file path
    --help                 Show this help message
    --version              Show version information
"""

import asyncio
import json
import csv
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import click
import httpx
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text

from esm.config import get_settings
from esm.database import get_db_context, init_db
from esm.models import Assistant, Memory
from esm.schemas import MemoryCreate, MemoryUpdate, SearchRequest, SearchType
from esm.services.memory_service import MemoryService
from esm.services.search_service import SearchService
from esm.services.export_service import ExportService
from esm.utils.exceptions import ESMException

console = Console()
settings = get_settings()


class ESMClient:
    """ESM API client for CLI operations"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or f"http://localhost:{settings.port}"
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {"status": "error", "error": f"Connection failed: {e}"}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "error": f"HTTP {e.response.status_code}"}
    
    async def get_assistants(self) -> List[Dict[str, Any]]:
        """Get list of assistants"""
        response = await self.client.get("/api/v1/assistants/")
        response.raise_for_status()
        return response.json()
    
    async def search_memories(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories"""
        response = await self.client.post("/api/v1/search/", json=search_data)
        response.raise_for_status()
        return response.json()
    
    async def create_memory(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a memory"""
        response = await self.client.post("/api/v1/memories/", json=memory_data)
        response.raise_for_status()
        return response.json()
    
    async def get_memory(self, memory_id: int) -> Dict[str, Any]:
        """Get a memory by ID"""
        response = await self.client.get(f"/api/v1/memories/{memory_id}")
        response.raise_for_status()
        return response.json()
    
    async def update_memory(self, memory_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a memory"""
        response = await self.client.put(f"/api/v1/memories/{memory_id}", json=update_data)
        response.raise_for_status()
        return response.json()
    
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory"""
        response = await self.client.delete(f"/api/v1/memories/{memory_id}")
        response.raise_for_status()
        return True
    
    async def get_assistant_stats(self, assistant_id: int) -> Dict[str, Any]:
        """Get assistant statistics"""
        response = await self.client.get(f"/api/v1/analytics/assistant/{assistant_id}/stats")
        response.raise_for_status()
        return response.json()
    
    async def list_memories(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List memories with filters"""
        response = await self.client.get("/api/v1/memories/", params=params)
        response.raise_for_status()
        return response.json()


async def get_assistant_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get assistant by name"""
    try:
        async with ESMClient() as client:
            assistants = await client.get_assistants()
            for assistant in assistants:
                if assistant['name'].lower() == name.lower():
                    return assistant
            return None
    except Exception as e:
        console.print(f"[red]Error getting assistant: {e}[/red]")
        return None


def format_memory_table(memories: List[Dict[str, Any]]) -> Table:
    """Format memories as a table"""
    table = Table()
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Importance", style="yellow")
    table.add_column("Content Preview", style="white")
    table.add_column("Created", style="blue")
    
    for memory in memories:
        content_preview = memory.get('content', '')[:100] + "..." if len(memory.get('content', '')) > 100 else memory.get('content', '')
        created_at = datetime.fromisoformat(memory['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
        
        table.add_row(
            str(memory['id']),
            memory.get('memory_type', 'general'),
            str(memory.get('importance', 0)),
            content_preview,
            created_at
        )
    
    return table


def format_search_results(results: Dict[str, Any]) -> Table:
    """Format search results as a table"""
    table = Table()
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Score", style="yellow")
    table.add_column("Type", style="green")
    table.add_column("Content Preview", style="white")
    table.add_column("Match Type", style="magenta")
    
    for result in results.get('results', []):
        memory = result['memory']
        content_preview = memory.get('content', '')[:100] + "..." if len(memory.get('content', '')) > 100 else memory.get('content', '')
        
        table.add_row(
            str(memory['id']),
            f"{result['score']:.3f}",
            memory.get('memory_type', 'general'),
            content_preview,
            result.get('match_type', 'unknown')
        )
    
    return table


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def cli(ctx, version):
    """Extended Sienna Memory CLI Tool"""
    if version:
        console.print("[bold blue]ESM CLI v1.0.0[/bold blue]")
        console.print("Extended Sienna Memory - AI Memory Management System")
        return
    
    if ctx.invoked_subcommand is None:
        console.print(Panel.fit(
            "[bold blue]Extended Sienna Memory (ESM)[/bold blue]\n"
            "AI Memory Management System\n\n"
            "Use --help to see available commands",
            title="ESM CLI"
        ))


@cli.command()
@click.argument('assistant_name')
@click.argument('content')
@click.option('--type', 'memory_type', default='general', help='Memory type')
@click.option('--importance', default=5, type=int, help='Importance (1-10)')
@click.option('--tags', help='Comma-separated tags')
@click.option('--source', help='Memory source')
@click.option('--context', help='Additional context')
@click.option('--shared', is_flag=True, help='Make memory shared')
@click.option('--shared-category', help='Shared category if shared')
def add(assistant_name, content, memory_type, importance, tags, source, context, shared, shared_category):
    """Add a new memory"""
    async def _add():
        try:
            assistant = await get_assistant_by_name(assistant_name)
            if not assistant:
                console.print(f"[red]Assistant '{assistant_name}' not found[/red]")
                return
            
            memory_data = {
                "assistant_id": assistant['id'],
                "content": content,
                "memory_type": memory_type,
                "importance": importance,
                "tags": tags,
                "source": source,
                "context": context,
                "is_shared": shared,
                "shared_category": shared_category if shared else None
            }
            
            # Remove None values
            memory_data = {k: v for k, v in memory_data.items() if v is not None}
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Creating memory...", total=None)
                
                async with ESMClient() as client:
                    memory = await client.create_memory(memory_data)
                
                progress.update(task, completed=True)
            
            console.print(f"[green]✓ Memory created with ID: {memory['id']}[/green]")
            
            if memory.get('summary'):
                console.print(f"[dim]Summary: {memory['summary']}[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error creating memory: {e}[/red]")
    
    asyncio.run(_add())


@cli.command()
@click.argument('assistant_name')
@click.argument('query')
@click.option('--limit', default=10, type=int, help='Maximum results')
@click.option('--semantic', is_flag=True, help='Use semantic search')
@click.option('--type', 'memory_type', help='Filter by memory type')
@click.option('--min-importance', type=int, help='Minimum importance')
@click.option('--no-shared', is_flag=True, help='Exclude shared memories')
def search(assistant_name, query, limit, semantic, memory_type, min_importance, no_shared):
    """Search memories"""
    async def _search():
        try:
            assistant = await get_assistant_by_name(assistant_name)
            if not assistant:
                console.print(f"[red]Assistant '{assistant_name}' not found[/red]")
                return
            
            search_data = {
                "query": query,
                "assistant_id": assistant['id'],
                "limit": limit,
                "search_type": "semantic" if semantic else "hybrid",
                "memory_type": memory_type,
                "min_importance": min_importance,
                "include_shared": not no_shared
            }
            
            # Remove None values
            search_data = {k: v for k, v in search_data.items() if v is not None}
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Searching...", total=None)
                
                async with ESMClient() as client:
                    results = await client.search_memories(search_data)
                
                progress.update(task, completed=True)
            
            if not results.get('results'):
                console.print("[yellow]No memories found[/yellow]")
                return
            
            console.print(f"\n[bold]Found {len(results['results'])} memories[/bold]")
            console.print(f"[dim]Search took {results.get('execution_time_ms', 0):.1f}ms[/dim]\n")
            
            table = format_search_results(results)
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error searching memories: {e}[/red]")
    
    asyncio.run(_search())


@cli.command()
@click.argument('assistant_name')
@click.option('--limit', default=20, type=int, help='Maximum results')
@click.option('--type', 'memory_type', help='Filter by memory type')
@click.option('--min-importance', type=int, help='Minimum importance')
def list(assistant_name, limit, memory_type, min_importance):
    """List memories for an assistant"""
    async def _list():
        try:
            assistant = await get_assistant_by_name(assistant_name)
            if not assistant:
                console.print(f"[red]Assistant '{assistant_name}' not found[/red]")
                return
            
            params = {
                "assistant_id": assistant['id'],
                "limit": limit,
                "memory_type": memory_type,
                "min_importance": min_importance
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Loading memories...", total=None)
                
                async with ESMClient() as client:
                    memories = await client.list_memories(params)
                
                progress.update(task, completed=True)
            
            if not memories:
                console.print("[yellow]No memories found[/yellow]")
                return
            
            console.print(f"\n[bold]{assistant['name']} has {len(memories)} memories[/bold]\n")
            
            table = format_memory_table(memories)
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error listing memories: {e}[/red]")
    
    asyncio.run(_list())


@cli.command()
@click.argument('memory_id', type=int)
def get(memory_id):
    """Get a specific memory"""
    async def _get():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Loading memory...", total=None)
                
                async with ESMClient() as client:
                    memory = await client.get_memory(memory_id)
                
                progress.update(task, completed=True)
            
            console.print(Panel.fit(
                f"[bold]Memory ID: {memory['id']}[/bold]\n"
                f"[green]Type:[/green] {memory.get('memory_type', 'general')}\n"
                f"[yellow]Importance:[/yellow] {memory.get('importance', 0)}/10\n"
                f"[blue]Created:[/blue] {memory['created_at']}\n"
                f"[cyan]Access Count:[/cyan] {memory.get('access_count', 0)}\n"
                f"[magenta]Tags:[/magenta] {memory.get('tags', 'None')}\n"
                f"[dim]Shared:[/dim] {'Yes' if memory.get('is_shared') else 'No'}",
                title="Memory Details"
            ))
            
            console.print("\n[bold]Content:[/bold]")
            console.print(memory.get('content', ''))
            
            if memory.get('summary'):
                console.print(f"\n[bold]Summary:[/bold]\n{memory['summary']}")
            
            if memory.get('context'):
                console.print(f"\n[bold]Context:[/bold]\n{memory['context']}")
            
        except Exception as e:
            console.print(f"[red]Error getting memory: {e}[/red]")
    
    asyncio.run(_get())


@cli.command()
@click.argument('memory_id', type=int)
@click.option('--content', help='New content')
@click.option('--importance', type=int, help='New importance (1-10)')
@click.option('--tags', help='New tags')
@click.option('--type', 'memory_type', help='New memory type')
def update(memory_id, content, importance, tags, memory_type):
    """Update a memory"""
    async def _update():
        try:
            update_data = {
                "content": content,
                "importance": importance,
                "tags": tags,
                "memory_type": memory_type
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_data:
                console.print("[yellow]No updates specified[/yellow]")
                return
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Updating memory...", total=None)
                
                async with ESMClient() as client:
                    memory = await client.update_memory(memory_id, update_data)
                
                progress.update(task, completed=True)
            
            console.print(f"[green]✓ Memory {memory_id} updated successfully[/green]")
            
        except Exception as e:
            console.print(f"[red]Error updating memory: {e}[/red]")
    
    asyncio.run(_update())


@cli.command()
@click.argument('memory_id', type=int)
@click.option('--force', is_flag=True, help='Skip confirmation')
def delete(memory_id, force):
    """Delete a memory"""
    async def _delete():
        try:
            if not force:
                if not Confirm.ask(f"Delete memory {memory_id}?"):
                    console.print("[yellow]Cancelled[/yellow]")
                    return
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Deleting memory...", total=None)
                
                async with ESMClient() as client:
                    await client.delete_memory(memory_id)
                
                progress.update(task, completed=True)
            
            console.print(f"[green]✓ Memory {memory_id} deleted[/green]")
            
        except Exception as e:
            console.print(f"[red]Error deleting memory: {e}[/red]")
    
    asyncio.run(_delete())


@cli.command()
@click.argument('assistant_name')
def stats(assistant_name):
    """Show assistant statistics"""
    async def _stats():
        try:
            assistant = await get_assistant_by_name(assistant_name)
            if not assistant:
                console.print(f"[red]Assistant '{assistant_name}' not found[/red]")
                return
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Loading statistics...", total=None)
                
                async with ESMClient() as client:
                    stats = await client.get_assistant_stats(assistant['id'])
                
                progress.update(task, completed=True)
            
            console.print(Panel.fit(
                f"[bold]{stats['assistant_name']} Statistics[/bold]\n\n"
                f"[green]Total Memories:[/green] {stats['total_memories']}\n"
                f"[blue]Shared Memories:[/blue] {stats['total_shared_memories']}\n"
                f"[yellow]Average Importance:[/yellow] {stats['avg_importance']:.1f}/10\n"
                f"[cyan]Most Used Type:[/cyan] {stats.get('most_used_type', 'None')}\n"
                f"[magenta]Created Today:[/magenta] {stats['memories_created_today']}\n"
                f"[red]Accessed Today:[/red] {stats['memories_accessed_today']}",
                title="Assistant Statistics"
            ))
            
        except Exception as e:
            console.print(f"[red]Error getting statistics: {e}[/red]")
    
    asyncio.run(_stats())


@cli.command()
def health():
    """Check system health"""
    async def _health():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Checking health...", total=None)
                
                async with ESMClient() as client:
                    health_data = await client.health_check()
                
                progress.update(task, completed=True)
            
            status = health_data.get('status', 'unknown')
            color = 'green' if status == 'healthy' else 'red'
            
            console.print(f"[{color}]Status: {status}[/{color}]")
            
            if 'version' in health_data:
                console.print(f"[blue]Version: {health_data['version']}[/blue]")
            
            if 'error' in health_data:
                console.print(f"[red]Error: {health_data['error']}[/red]")
            
        except Exception as e:
            console.print(f"[red]Health check failed: {e}[/red]")
    
    asyncio.run(_health())


@cli.command()
def assistants():
    """List all assistants"""
    async def _assistants():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Loading assistants...", total=None)
                
                async with ESMClient() as client:
                    assistants = await client.get_assistants()
                
                progress.update(task, completed=True)
            
            if not assistants:
                console.print("[yellow]No assistants found[/yellow]")
                return
            
            table = Table()
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="bold")
            table.add_column("Status", style="green")
            table.add_column("Created", style="blue")
            
            for assistant in assistants:
                status = "Active" if assistant.get('is_active') else "Inactive"
                created_at = datetime.fromisoformat(assistant['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                
                table.add_row(
                    str(assistant['id']),
                    assistant['name'],
                    status,
                    created_at
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error listing assistants: {e}[/red]")
    
    asyncio.run(_assistants())


@cli.command()
def init():
    """Initialize the ESM database"""
    def _init():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                task = progress.add_task("Initializing database...", total=None)
                
                init_db()
                
                progress.update(task, completed=True)
            
            console.print("[green]✓ Database initialized successfully[/green]")
            console.print("[dim]Default assistants created: Sienna and Vale[/dim]")
            
        except Exception as e:
            console.print(f"[red]Database initialization failed: {e}[/red]")
    
    _init()


def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()