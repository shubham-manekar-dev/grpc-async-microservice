"""Generate gRPC stubs for the care plan microservice."""

from __future__ import annotations

import pathlib
import subprocess
import sys


def main() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    proto_dir = repo_root / "backend" / "app" / "proto"
    output_dir = proto_dir / "generated"

    command = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
        str(proto_dir / "care_plan.proto"),
    ]

    print("Running:", " ".join(command))
    subprocess.check_call(command)
    print("gRPC stubs generated under", output_dir)


if __name__ == "__main__":
    main()
