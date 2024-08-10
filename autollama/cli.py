"""Main script for the autollama package."""
import click


@click.group(invoke_without_command=True)
@click.option("-c", "--continuous", is_flag=True, help="Enable Continuous Mode")
@click.option(
    "--skip-reprompt",
    "-y",
    is_flag=True,
    help="Skips the re-prompting messages at the beginning of the script",
)
@click.option(
    "--ai-settings",
    "-C",
    help="Specifies which ai_settings.yaml file to use, will also automatically skip the re-prompt.",
)
@click.option(
    "-l",
    "--continuous-limit",
    type=int,
    help="Defines the number of times to run in continuous mode",
)
@click.option("--debug", is_flag=True, help="Enable Debug Mode")
@click.option(
    "--use-memory",
    "-m",
    "memory_type",
    type=str,
    help="Defines which Memory backend to use",
)
@click.option(
    "-b",
    "--browser-name",
    help="Specifies which web-browser to use when using selenium to scrape the web.",
)
@click.option(
    "--allow-downloads",
    is_flag=True,
    help="Dangerous: Allows Auto-Llama to download files natively.",
)
@click.option(
    # TODO: this is a hidden option for now, necessary for integration testing.
    #   We should make this public once we're ready to roll out agent specific workspaces.
    "--workspace-directory",
    "-w",
    type=click.Path(),
    hidden=True,
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
    """
    Welcome to AutoLlama an experimental open-source application showcasing the capabilities of Llama3 pushing the boundaries of AI.

    Start an Auto-Llama assistant.
    """
    # Put imports inside function to avoid importing everything when starting the CLI
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
