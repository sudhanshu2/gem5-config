from pathlib import Path
from typing import Optional

from gem5.components.boards.abstract_board import AbstractBoard
from gem5.isas import ISA
from gem5.resources.resource import DiskImageResource, KernelResource

import component
from board import parallel, serial


def setup_board(
    config: dict, m5_cmd: str, restore: Optional[Path] = None
) -> AbstractBoard:
    processor = component.cpu.setup_processor(
        start_cpu=component.cpu.get_start_cpu(config),
        switch_cpu=component.cpu.get_switch_cpu(config),
        num_cores=component.cpu.get_num_cores(config),
        clk_freq=component.cpu.get_frequency(config),
    )
    memory = component.dram.setup_dram(config)
    cache_hierarchy = component.cache.setup_cache(config)

    if config["parallel-gem5"]["enable"] == True:
        board = parallel.ParallelBoard(
            sim_quantum=int(config["parallel-gem5"]["sim-quantum"]),
            clk_freq=component.cpu.get_frequency(config),
            processor=processor,
            memory=memory,
            cache_hierarchy=cache_hierarchy,
            benchmark_image=DiskImageResource(local_path=config["image"]["benchmark"]),
            mount_benchmark_as_cow=True,
        )
    else:
        board = serial.SerialBoard(
            clk_freq=component.cpu.get_frequency(config),
            processor=processor,
            memory=memory,
            cache_hierarchy=cache_hierarchy,
            benchmark_image=DiskImageResource(local_path=config["image"]["benchmark"]),
            mount_benchmark_as_cow=True,
        )
    return setup_kernel(config, board, m5_cmd, restore)


def setup_kernel(
    config: dict, board: AbstractBoard, m5_cmd: str, p_restore: Optional[Path]
) -> AbstractBoard:
    if p_restore is not None:
        if p_restore.is_dir() == False:
            m5.util.fatal(
                f"[CONFIG, BOARD]: Checkpoint directory {p_restore} does not exist"
            )
    kernel_args = board.get_default_kernel_args()
    if bool(config["linux"]["skip_systemd"]) == True:
        kernel_args.append("no_systemd")
    board.set_kernel_disk_workload(
        kernel=KernelResource(
            local_path=config["linux"]["path"],
            architecture=ISA.X86,
        ),
        disk_image=DiskImageResource(
            local_path=config["image"]["ubuntu"],
            root_partition="2",
        ),
        readfile_contents=m5_cmd,
        kernel_args=kernel_args,
        checkpoint=p_restore,
    )
    return board
