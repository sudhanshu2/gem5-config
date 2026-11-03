import argparse
import os
import subprocess
import sys
import time

sys.path.append(os.path.abspath("common"))

import base

parser = argparse.ArgumentParser()
parser.add_argument("--gem5", type=str, required=True)
args = parser.parse_args()

if os.path.isfile(base.PATHS_CONFIG) == True:
    output_path = base.parse_yaml(base.PATHS_CONFIG)["output"]
else:
    output_path = f"{base.REPO_PATH}/m5out"

last_checkpoint = None
while True:
    execution_output_path = f"{output_path}/{time.strftime('%Y.%m.%d_%H.%M.%S')}"
    gem5_env = os.environ.copy()
    gem5_env[
        "TSAN_OPTIONS"
    ] = f"{gem5_env.get('TSAN_OPTIONS', '')} halt_on_error=1 abort_on_error=1".strip()
    command = [
        "setarch",
        os.uname().machine,
        "-R",
        args.gem5,
        "--remote-gdb-port=7050",
        "--unsafe-remote-gdb",
        f"--outdir={execution_output_path}",
        f"{base.REPO_PATH}/configs/checkpoint.py",
        "--outdir",
        execution_output_path,
    ]
    if last_checkpoint is not None:
        command += ["--restore", last_checkpoint]
    print(f"Executing: {' ' .join(command)}")
    os.makedirs(execution_output_path, exist_ok=True)
    with open(f"{execution_output_path}/command.log", "w") as f_command:
        f_command.write(
            f"TSAN_OPTIONS='{gem5_env['TSAN_OPTIONS']}' {' '.join(command)}\n"
        )
    with open(f"{execution_output_path}/stdout.log", "w") as f_stdout, open(
        f"{execution_output_path}/stderr.log", "w"
    ) as f_stderr:
        process = subprocess.Popen(
            command, env=gem5_env, stdout=f_stdout, stderr=f_stderr
        )
        print(f"Launched PID: {process.pid}", flush=True)
        returncode = process.wait()
    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, command)

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
