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

parser = argparse.ArgumentParser()
parser.add_argument("--restore", type=str)
args = parser.parse_args()

if args.restore is not None:
    restore_path = pathlib.Path(args.restore).resolve()
else:
    restore_path = None

config, paths, output_path, checkpoint_path = base.setup(restore=restore_path)
board = component.board.setup_board(
    config, paths, "gem5-bridge exit 0;", restore=restore_path
)

checkpoint_rate = None
start_time = time.time()


def exit_event_handler():
    m5.util.inform(f"[{time.time() - start_time}s] BOOTEXIT: 1 -> Kernel Loaded")
    yield False
    m5.util.inform(f"[{time.time() - start_time}s] BOOTEXIT: 2 -> Ubuntu Booted")
    simulator.save_checkpoint(checkpoint_path)
    yield False
    m5.util.inform(f"[{time.time() - start_time}s] BOOTEXIT: 3 -> Checkpoint Created")
    yield True


def checkpoint_poll_handler():
    while True:
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
        m5.scheduleTickExitFromCurrent(checkpoint_rate)
        yield False


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
m5.util.inform(f"[CONFIG, CHECKPOINT]: Checkpoints per ticks: {checkpoint_rate}")

m5.scheduleTickExitFromCurrent(checkpoint_rate)
simulator.run()
