import argparse
import pathlib
import sys
import time

import m5

from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator

sys.path.append(f"{pathlib.Path(__file__).resolve().parent.parent}/common")

import base
import component

sys.stdout.reconfigure(line_buffering=True)

parser = argparse.ArgumentParser()
parser.add_argument("--outdir", type=str)
parser.add_argument("--restore", type=str)
parser.add_argument("--config", type=str)
parser.add_argument("--os-image", type=str)
parser.add_argument("--benchmark-image", type=str)
parser.add_argument("--kernel", type=str)
args = parser.parse_args()

paths = base.get_paths(vars(args))
config, output_path = base.setup(paths)

board = component.board.setup_board(config, paths, "gem5-bridge exit 0;")

start_time = time.time()
exit_reason = None


def save_checkpoint():
    insts = simulator.get_instruction_count()
    checkpoint_insts_path = f"{output_path}/checkpoint-{insts}"
    checkpoint_start_time = time.time()
    m5.util.inform(
        f"[{time.time() - start_time}s] CHECKPOINT: Saving at {insts} instructions"
    )
    simulator.save_checkpoint(checkpoint_insts_path)
    m5.util.inform(
        f"[{time.time() - start_time}s] CHECKPOINT: Saved at {checkpoint_insts_path} in {time.time() - checkpoint_start_time}s"
    )


def exit_event_handler():
    global exit_reason
    assert exit_reason is None
    exit_reason = "exit"
    m5.util.inform(f"[{time.time() - start_time}s] Received exit")
    save_checkpoint()
    yield True


def checkpoint_poll_handler():
    global exit_reason
    assert exit_reason is None
    exit_reason = "checkpoint"
    m5.util.inform(f"[{time.time() - start_time}s] Reached checkpoint tick")
    save_checkpoint()
    yield True


simulator = Simulator(
    board=board,
    outdir=output_path,
    on_exit_event={
        ExitEvent.EXIT: exit_event_handler(),
        ExitEvent.SCHEDULED_TICK: checkpoint_poll_handler(),
    },
)

simulator._instantiate()

checkpoint_rate = (
    int(config["fast-forward"]["checkpoint-rate"]) * component.cpu.get_ticks_per_cycle()
)
m5.util.inform(f"[CONFIG, CHECKPOINT]: Saving checkpoint at {checkpoint_rate} ticks")

m5.scheduleTickExitFromCurrent(checkpoint_rate)
simulator.run()
