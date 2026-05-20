#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click>=8.1",
# ]
# ///
"""Write a manifest for rendered geometric-spring ablation figures."""

from __future__ import annotations

from pathlib import Path

import click


def parse_plot_path(sweep_root: Path, plot: Path) -> dict[str, str]:
    rel = plot.relative_to(sweep_root / "figures")
    parts = rel.parts
    return {
        "system": parts[0],
        "spring_mode": parts[1],
        "images": parts[2].removeprefix("images_"),
        "plot_type": parts[3],
        "path": str(plot),
    }


@click.command()
@click.option("--sweep-root", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output", required=True, type=click.Path(dir_okay=False, path_type=Path))
def main(sweep_root: Path, output: Path) -> None:
    plots = sorted((sweep_root / "figures").glob("*/*/images_*/*/plot.png"))
    rows = [parse_plot_path(sweep_root, plot) for plot in plots]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as handle:
        handle.write("system\tspring_mode\timages\tplot_type\tpath\n")
        for row in rows:
            handle.write(
                f"{row['system']}\t{row['spring_mode']}\t{row['images']}\t{row['plot_type']}\t{row['path']}\n"
            )


if __name__ == "__main__":
    main()
