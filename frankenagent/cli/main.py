"""CLI interface for FrankenAgent Lab.

This module provides command-line interface for executing agents from blueprints
and managing the blueprint library.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from frankenagent.runtime.service import RuntimeService, ExecutionError
from frankenagent.config.loader import (
    BlueprintNotFoundError,
    ValidationError,
)
from frankenagent.compiler.compiler import CompilationError


# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@click.group()
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging"
)
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """🧟 FrankenAgent Lab - Build AI agents from body parts.
    
    FrankenAgent Lab lets you compose AI agents using a Frankenstein-inspired
    metaphor: head (LLM), arms (tools), legs (execution mode), heart (memory),
    and spine (guardrails).
    """
    ctx.ensure_object(dict)
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        ctx.obj["debug"] = True
    else:
        ctx.obj["debug"] = False


@cli.command()
@click.argument("blueprint_path", type=click.Path(exists=True))
@click.argument("message")
@click.option(
    "--blueprints-dir",
    default="./blueprints",
    help="Directory containing blueprints (default: ./blueprints)"
)
@click.option(
    "--show-trace",
    is_flag=True,
    default=True,
    help="Show execution trace (default: True)"
)
@click.pass_context
def run(
    ctx: click.Context,
    blueprint_path: str,
    message: str,
    blueprints_dir: str,
    show_trace: bool
) -> None:
    """Execute an agent from a blueprint file.
    
    BLUEPRINT_PATH: Path to the blueprint YAML or JSON file
    MESSAGE: Message to send to the agent
    
    Examples:
    
        # Run a simple assistant
        frankenagent run blueprints/simple_assistant.yaml "What is AI?"
        
        # Run with custom blueprints directory
        frankenagent run my_agent.yaml "Hello" --blueprints-dir ./my_blueprints
        
        # Run without showing trace
        frankenagent run agent.yaml "Query" --show-trace=False
    """
    debug = ctx.obj.get("debug", False)
    
    try:
        # Initialize runtime service
        runtime = RuntimeService(blueprints_dir=blueprints_dir)
        
        # Extract blueprint ID from path
        blueprint_id = Path(blueprint_path).stem
        
        if debug:
            click.echo(f"🔧 Loading blueprint: {blueprint_path}")
            click.echo(f"💬 Message: {message}")
        
        # Execute agent
        click.echo("⚡ Executing agent...\n")
        result = runtime.execute(blueprint_id, message)
        
        # Display response
        click.echo("=" * 80)
        click.echo("📝 AGENT RESPONSE")
        click.echo("=" * 80)
        click.echo()
        click.echo(result.response)
        click.echo()
        
        # Display execution trace if requested
        if show_trace and result.execution_trace:
            click.echo("=" * 80)
            click.echo("🔍 EXECUTION TRACE")
            click.echo("=" * 80)
            click.echo()
            
            for i, trace in enumerate(result.execution_trace, 1):
                click.echo(f"[{i}] {trace.tool_name}")
                click.echo(f"    ⏱️  Timestamp: {trace.timestamp}")
                click.echo(f"    ⚙️  Duration: {trace.duration_ms:.2f}ms")
                
                # Show inputs (truncate if too long)
                inputs_str = str(trace.inputs)
                if len(inputs_str) > 200:
                    inputs_str = inputs_str[:200] + "..."
                click.echo(f"    📥 Inputs: {inputs_str}")
                
                # Show outputs (truncate if too long)
                outputs_str = str(trace.outputs)
                if len(outputs_str) > 200:
                    outputs_str = outputs_str[:200] + "..."
                click.echo(f"    📤 Outputs: {outputs_str}")
                click.echo()
            
            click.echo(f"⏱️  Total Duration: {result.total_duration_ms:.2f}ms")
            click.echo(f"🔧 Total Tool Calls: {len(result.execution_trace)}")
        
        # Show error if present
        if result.error:
            click.echo()
            click.echo("=" * 80)
            click.secho("⚠️  EXECUTION ERROR", fg="yellow", bold=True)
            click.echo("=" * 80)
            click.echo()
            click.secho(result.error, fg="yellow")
            sys.exit(1)
        
    except BlueprintNotFoundError as e:
        click.secho(f"\n❌ Blueprint Not Found", fg="red", bold=True)
        click.secho(f"{e}", fg="red")
        sys.exit(1)
        
    except ValidationError as e:
        click.secho(f"\n❌ Blueprint Validation Error", fg="red", bold=True)
        click.secho(f"{e}", fg="red")
        click.echo()
        click.echo("💡 Tip: Check your blueprint schema against the documentation")
        sys.exit(1)
        
    except CompilationError as e:
        click.secho(f"\n❌ Blueprint Compilation Error", fg="red", bold=True)
        click.secho(f"{e}", fg="red")
        sys.exit(1)
        
    except ExecutionError as e:
        click.secho(f"\n❌ Agent Execution Error", fg="red", bold=True)
        click.secho(f"{e}", fg="red")
        sys.exit(1)
        
    except Exception as e:
        click.secho(f"\n❌ Unexpected Error", fg="red", bold=True)
        click.secho(f"{e}", fg="red")
        if debug:
            import traceback
            click.echo()
            click.echo(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--blueprints-dir",
    default="./blueprints",
    help="Directory containing blueprints (default: ./blueprints)"
)
@click.pass_context
def list(ctx: click.Context, blueprints_dir: str) -> None:
    """List all available blueprints.
    
    Scans the blueprints directory for YAML and JSON files and displays
    their names and descriptions.
    
    Examples:
    
        # List blueprints in default directory
        frankenagent list
        
        # List blueprints in custom directory
        frankenagent list --blueprints-dir ./my_blueprints
    """
    debug = ctx.obj.get("debug", False)
    
    try:
        # Initialize runtime service
        runtime = RuntimeService(blueprints_dir=blueprints_dir)
        
        # Get list of blueprints
        blueprint_ids = runtime.list_blueprints()
        
        if not blueprint_ids:
            click.secho(f"\n📭 No blueprints found in {blueprints_dir}", fg="yellow")
            click.echo()
            click.echo("💡 Tip: Create a blueprint YAML or JSON file in the blueprints directory")
            return
        
        # Display header
        click.echo()
        click.secho("🧟 Available Blueprints", fg="green", bold=True)
        click.echo("=" * 80)
        click.echo()
        
        # Load and display each blueprint
        for blueprint_id in blueprint_ids:
            try:
                # Resolve path
                blueprint_path = runtime._resolve_blueprint_path(blueprint_id)
                
                # Load blueprint to get metadata
                blueprint = runtime.loader.load_from_file(str(blueprint_path))
                
                # Display blueprint info
                click.secho(f"📄 {blueprint_id}", fg="cyan", bold=True)
                click.echo(f"   Name: {blueprint.name}")
                if blueprint.description:
                    click.echo(f"   Description: {blueprint.description}")
                click.echo(f"   Version: {blueprint.version}")
                click.echo(f"   Mode: {blueprint.legs.execution_mode}")
                click.echo(f"   Tools: {len(blueprint.arms)}")
                click.echo(f"   File: {blueprint_path.name}")
                click.echo()
                
            except Exception as e:
                # Show error but continue listing
                click.secho(f"📄 {blueprint_id}", fg="cyan", bold=True)
                click.secho(f"   ⚠️  Error loading: {e}", fg="yellow")
                click.echo()
                
                if debug:
                    import traceback
                    click.echo(traceback.format_exc())
        
        click.echo(f"Found {len(blueprint_ids)} blueprint(s)")
        click.echo()
        
    except Exception as e:
        click.secho(f"\n❌ Error listing blueprints", fg="red", bold=True)
        click.secho(f"{e}", fg="red")
        if debug:
            import traceback
            click.echo()
            click.echo(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    cli()
