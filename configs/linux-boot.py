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

config, paths, p_output, p_checkpoint = base.setup()
board = component.board.setup_board(config, paths, "gem5-bridge exit 0;")

start_time = time.time()


def exit_event_handler():
    m5.util.inform(f"[{time.time() - start_time}s] BOOTEXIT: 1 -> Kernel Loaded")
    yield False
    m5.util.inform(f"[{time.time() - start_time}s] BOOTEXIT: 2 -> Ubuntu Booted")
    simulator.save_checkpoint(p_checkpoint)
    yield False
    m5.util.inform(f"[{time.time() - start_time}s] BOOTEXIT: 3 -> Checkpoint Created")
    yield True


simulator = Simulator(
    board=board,
    outdir=p_output,
    on_exit_event={
        ExitEvent.EXIT: exit_event_handler(),
    },
)

simulator.run()
