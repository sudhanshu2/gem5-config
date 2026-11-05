import argparse
import os
import subprocess
import sys
import time

sys.path.append(os.path.abspath("common"))

import base

parser = argparse.ArgumentParser()
parser.add_argument("--gem5", type=str, required=True)
parser.add_argument("--outdir", type=str, required=True)
parser.add_argument("--restore", type=str)
parser.add_argument("--config", type=str)
parser.add_argument("--os-image", type=str)
parser.add_argument("--benchmark-image", type=str)
parser.add_argument("--kernel", type=str)
args = parser.parse_args()

base_output_path = args.outdir
runner_output_path = (
    f"{base_output_path}/checkpoint-runner-{time.strftime('%Y.%m.%d_%H.%M.%S')}"
)
os.makedirs(runner_output_path)

last_checkpoint = args.restore
while True:
    execution_output_path = f"{runner_output_path}/{time.strftime('%Y.%m.%d_%H.%M.%S')}"
    execution_output_path = execution_output_path.replace("//", "/")
    os.makedirs(execution_output_path)
    gem5_env = os.environ.copy()
    gem5_env[
        "TSAN_OPTIONS"
    ] = f"{gem5_env.get('TSAN_OPTIONS', '')} halt_on_error=1 exitcode=66".strip()
    command = ["setarch", os.uname().machine, "-R"]
    command += [args.gem5]
    command += ["--remote-gdb-port=7000", "--unsafe-remote-gdb"]
    command += [f"--outdir={execution_output_path}"]
    command += [f"{base.REPO_PATH}/configs/checkpoint.py"]
    command += [f"--outdir={execution_output_path}"]
    if last_checkpoint is not None:
        command += ["--restore", last_checkpoint]
    if args.config is not None:
        command += ["--config", args.config]
    if args.os_image is not None:
        command += ["--os-image", args.os_image]
    if args.benchmark_image is not None:
        command += ["--benchmark-image", args.benchmark_image]
    if args.kernel is not None:
        command += ["--kernel", args.kernel]
    print(f"Executing: {' ' .join(command)}")
    with open(f"{execution_output_path}/command.log", "w") as f_command:
        f_command.write(
            f"TSAN_OPTIONS='{gem5_env['TSAN_OPTIONS']}' {' '.join(command)}\n"
        )
    with open(f"{execution_output_path}/stdout.log", "w") as f_stdout, open(
        f"{execution_output_path}/stderr.log", "w"
    ) as f_stderr:
        subprocess.run(
            command, env=gem5_env, stdout=f_stdout, stderr=f_stderr, check=True
        )

    checkpoints = []
    for entry in os.listdir(execution_output_path):
        if entry.startswith("checkpoint-") == False:
            continue
        if os.path.isdir(f"{execution_output_path}/{entry}") == False:
            continue
        checkpoints.append(entry)
    if len(checkpoints) != 1:
        sys.exit(
            f"Expected one checkpoint-* directory in {execution_output_path} but found {len(checkpoints)}: {checkpoints}"
        )
    last_checkpoint = f"{execution_output_path}/{checkpoints[0]}"
    print(f"Checkpoint: {last_checkpoint}", flush=True)
