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
parser.add_argument("config", type=str)
parser.add_argument("checkpoint", type=str)
args = parser.parse_args()
p_config = args.config
p_restore = pathlib.Path(args.checkpoint).resolve()

config, p_output, p_checkpoint = base.setup(p_config)
board = component.board.setup_board(config, "gem5-bridge exit 0;", restore=p_restore)

start_time = time.time()


def exit_event_handler():
    m5.util.inform(f"[{time.time() - start_time}s] RESTOREEXIT: 1 -> Command finished")
    yield True


simulator = Simulator(
    board=board,
    outdir=p_output,
    on_exit_event={
        ExitEvent.EXIT: exit_event_handler(),
    },
)

m5.util.inform(f"[CONFIG, RESTORE]: Restoring from {p_restore}")
simulator.run()
