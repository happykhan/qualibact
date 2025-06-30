#!/usr/bin/env python3
import typer
import os
import logging
from dotenv import load_dotenv
from genomeqc.prepare import prepare_genomeqc_dataframes
from genomeqc.species_run import species_run
from genomeqc.summary import summary as final_summary

app = typer.Typer()

def load_environment(dotenv_path: str = ".genomeqc.env"):
    """Load the environment variables and configurations."""
    if os.path.exists(dotenv_path):
        return load_dotenv(dotenv_path)
    else:
        raise FileNotFoundError(f"Environment file {dotenv_path} not found.")

@app.command()
def prepare(dotenv_path: str = ".genomeqc.env", submit: bool = False):
    """Run the ATB fetch script."""
    load_environment(dotenv_path)
    logging.info("Environment loaded and logging set up.")
    typer.echo("Preparing genomeqc dataframes...")
    metadata_path = os.environ["GENOMEQC_ATB_METADATA"] 
    GENOMEQC_OUTPUT_DIR = os.environ["GENOMEQC_OUTPUT_DIR"]
    prepare_genomeqc_dataframes(metadata_path=metadata_path, workdir=GENOMEQC_OUTPUT_DIR, submit=submit)


@app.command()
def calculate(species: str,
              workdir: str,
              dotenv_path: str = ".genomeqc.env", ):
    """calculate genomeqc for a specific species."""
    load_environment(dotenv_path)
    typer.echo("Running genomeqc for species...")
    species_run(species, workdir)

@app.command()
def summary(
    calculate_dir = typer.Argument(..., help="Path to the species directory containing genomeqc results."),
    dotenv_path: str = ".genomeqc.env"
):
    """Perform final summary of genomeqc results."""
    load_environment(dotenv_path)
    typer.echo("Final summary...")
    final_summary(calculate_dir)

@app.command()
def make_docs(
    calculate_dir = typer.Argument(..., help="Path to the species directory containing genomeqc results."),
    docs_dir: str = typer.Argument('docs', help="Path to the directory where documentation will be generated."),
    dotenv_path: str = ".genomeqc.env"
):
    """Generate documentation for genomeqc results."""
    load_environment(dotenv_path)
    from genomeqc.docs import generate_docs
    typer.echo("Generating documentation...")
    generate_docs(calculate_dir, docs_dir)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    app()
