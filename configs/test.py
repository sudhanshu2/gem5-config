import pathlib
import time
from typing import Optional

import m5
from m5.objects import Root

from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.ruby.mesi_three_level_cache_hierarchy import (
    MESIThreeLevelCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.override import overrides

# Values from config.yaml
SKIP_SYSTEMD = True
CPU_CORES = 8
CPU_START = CPUTypes.TIMING
CPU_SWITCH = CPUTypes.TIMING  # switch_cpu: false, so same as start
CPU_FREQUENCY = "3.3GHz"
L1D_SIZE = "48KiB"
L1D_ASSOC = 12
L1I_SIZE = "32KiB"
L1I_ASSOC = 8
L2_SIZE = "1280KiB"
L2_ASSOC = 20
L3_SIZE = "18MiB"
L3_ASSOC = 12
L3_SLICES = 8
DRAM_SIZE = "3GiB"
SIM_QUANTUM = 1

# Default paths from base.get_paths() when ~/gem5-paths.yaml does not exist
OS_RESOURCE = "x86-ubuntu-22.04-img"
LINUX_RESOURCE = "x86-linux-kernel-5.4.49"
OUTPUT_BASE = f"{pathlib.Path(__file__).resolve().parent.parent}/m5out"


def get_ticks_per_cycle(processor: SimpleSwitchableProcessor) -> int:
    m5.ticks.fixGlobalFrequency()

    core_simobj = processor.get_cores()[0].get_simobject()
    clk_domain = core_simobj.clk_domain

    # Resolve proxy if necessary
    if m5.proxy.isproxy(clk_domain):
        clk_domain = clk_domain.unproxy(core_simobj)

    # clk_domain.clock is a VectorParam.Clock. Get the first one.
    clock = clk_domain.clock[0]
    if m5.proxy.isproxy(clock):
        clock = clock.unproxy(clk_domain)

    return clock.getValue()


class ParallelBoard(X86Board):
    def __init__(self, sim_quantum: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._sim_quantum = sim_quantum

    @overrides(X86Board)
    def _pre_instantiate(self, full_system: Optional[bool] = None) -> Root:
        root = super()._pre_instantiate(full_system)
        processor = self.get_processor()
        ruby_system = self.get_cache_hierarchy().ruby_system
        for i in range(CPU_CORES):
            m5.util.inform(
                f"[CONFIG, CPU]: Assigning SimpleSwitchableProcessor start ({i}) and stop ({i}) cores: {i + 1}"
            )
            processor._switchable_cores[processor._start_key][i].eventq_index = i + 1
            processor._switchable_cores[processor._switch_key][i].eventq_index = i + 1
            m5.util.inform(
                f"[CONFIG, CACHE]: Assigning Ruby MESIThreeLevelCacheHierarchy L1 ({i}) and L2 ({i}) caches: {i + 1}"
            )
            ruby_system.l1_controllers[i].eventq_index = i + 1
            ruby_system.l2_controllers[i].eventq_index = i + 1
        root.sim_quantum = self._sim_quantum * get_ticks_per_cycle(processor)
        return root


output_path = f"{OUTPUT_BASE}/{time.strftime('%Y.%m.%d_%H.%M.%S')}"
pathlib.Path(output_path).mkdir(parents=True, exist_ok=True)
m5.options.outdir = output_path
m5.util.inform(f"[CONFIG, BASE]: Output directory: {output_path}")

processor = SimpleSwitchableProcessor(
    starting_core_type=CPU_START,
    switch_core_type=CPU_SWITCH,
    isa=ISA.X86,
    num_cores=CPU_CORES,
    clk_freq=CPU_FREQUENCY,
)
memory = SingleChannelDDR4_2400(size=DRAM_SIZE)
cache_hierarchy = MESIThreeLevelCacheHierarchy(
    l1d_size=L1D_SIZE,
    l1d_assoc=L1D_ASSOC,
    l1i_size=L1I_SIZE,
    l1i_assoc=L1I_ASSOC,
    l2_size=L2_SIZE,
    l2_assoc=L2_ASSOC,
    l3_size=L3_SIZE,
    l3_assoc=L3_ASSOC,
    num_l3_banks=L3_SLICES,
)

board = ParallelBoard(
    sim_quantum=SIM_QUANTUM,
    clk_freq=CPU_FREQUENCY,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

kernel_args = board.get_default_kernel_args()
if SKIP_SYSTEMD == True:
    kernel_args.append("no_systemd")
board.set_kernel_disk_workload(
    kernel=obtain_resource(LINUX_RESOURCE),
    disk_image=obtain_resource(OS_RESOURCE),
    readfile_contents="gem5-bridge exit 0;",
    kernel_args=kernel_args,
)

start_time = time.time()


def exit_event_handler():
    m5.util.inform(f"[{time.time() - start_time}s] BOOTEXIT: 1 -> Kernel Loaded")
    yield False
    m5.util.inform(f"[{time.time() - start_time}s] BOOTEXIT: 2 -> Ubuntu Booted")
    yield False
    m5.util.inform(f"[{time.time() - start_time}s] BOOTEXIT: 3 -> Checkpoint Created")
    yield True


simulator = Simulator(
    board=board,
    outdir=output_path,
    on_exit_event={
        ExitEvent.EXIT: exit_event_handler(),
    },
)

simulator.run()
