"""Main script for the autollama package."""
import click

@click.group(invoke_without_command=True)
@click.option("-c", "--continuous", is_flag=True, help="Enable Continuous Mode")
@click.option(
    "-y", "--skip-reprompt",
    is_flag=True,
    help="Skip initial re-prompt messages"
)
@click.option(
    "-C", "--ai-settings",
    help="Specify the ai_settings.yaml file to use (automatically skips re-prompt)"
)
@click.option(
    "-l", "--continuous-limit",
    type=int,
    help="Number of times to run in continuous mode"
)
@click.option("--debug", is_flag=True, help="Enable Debug Mode")
@click.option(
    "-m", "--use-memory", "memory_type",
    type=str,
    help="Define which Memory backend to use"
)
@click.option(
    "-b", "--browser-name",
    help="Specify the web-browser to use with selenium"
)
@click.option(
    "--allow-downloads",
    is_flag=True,
    help="Dangerous: Allow Auto-Llama to download files natively"
)
@click.option(
    "-w", "--workspace-directory",
    type=click.Path(),
    hidden=True,
    help="(Hidden) Specify the workspace directory for agent-specific workspaces"
)
@click.pass_context
def main(
    ctx: click.Context,
    continuous: bool,
    continuous_limit: int,
    ai_settings: str,
    skip_reprompt: bool,
    debug: bool,
    memory_type: str,
    browser_name: str,
    allow_downloads: bool,
    workspace_directory: str,
) -> None:
    """Start an Auto-Llama assistant."""
    from autollama.main import run_auto_llama

    if ctx.invoked_subcommand is None:
        run_auto_llama(
            continuous,
            continuous_limit,
            ai_settings,
            skip_reprompt,
            debug,
            memory_type,
            browser_name,
            allow_downloads,
            workspace_directory,
        )

if __name__ == "__main__":
    main()
