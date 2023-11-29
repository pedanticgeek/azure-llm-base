from typing import Any, List, Optional, Dict
import base64
import subprocess
from utils.message_builder import MessageBuilder


def filename_to_id(filename: str) -> str:
    filename_hash = base64.b16encode(filename.encode("utf-8")).decode("ascii")
    return filename_hash


def run_az_cli_command(command: str | List[str]):
    process = subprocess.run(
        command,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process.stdout.strip()


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def build_filters(overrides: Dict[str, Any]) -> Optional[str]:
    """Builds Azure Cognitive Search Filters from the provided parameters"""
    filters = []
    if len(exclude_categories := overrides.get("exclude_categories", [])) > 0:
        for exclude_category in exclude_categories:
            filters.append(
                "category ne '{}'".format(exclude_category.replace("'", "''"))
            )

    if len(sourcefiles := overrides.get("sourcefiles", [])) > 0:
        formatted_sourcefiles = ",".join(sourcefiles)
        filters.append(f"search.in(sourcefile, '{formatted_sourcefiles}', ',')")
    return None if len(filters) == 0 else " and ".join(filters)


def nonewlines(s: str) -> str:
    return s.replace("\n", " ").replace("\r", " ")
