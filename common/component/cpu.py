import m5

from gem5.isas import ISA
from gem5.components.processors.abstract_processor import AbstractProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
import base

_ticks_per_cycle = None


def select_cpu(cpu: str) -> CPUTypes:
    if cpu == "o3":
        return CPUTypes.O3
    elif cpu == "atomic":
        return CPUTypes.ATOMIC
    elif cpu == "kvm":
        return CPUTypes.KVM
    elif cpu == "timing":
        return CPUTypes.TIMING
    m5.util.fatal(f"[CONFIG, CPU]: Unknown CPU type {cpu}")


def setup_processor(
    start_cpu: str, switch_cpu: "CPUTypes", num_cores: int, clk_freq: str
) -> SimpleSwitchableProcessor:
    processor = SimpleSwitchableProcessor(
        starting_core_type=select_cpu(start_cpu),
        switch_core_type=switch_cpu,
        isa=ISA.X86,
        num_cores=num_cores,
        clk_freq=clk_freq,
    )
    m5.util.inform(
        f"[CONFIG, CPU]: Using CPU start: {select_cpu(start_cpu)} and switch: {switch_cpu}"
    )
    if select_cpu(start_cpu) == CPUTypes.KVM:
        m5.util.inform("[CONFIG, CPU]: Disabling performance counters for KVM")
        for proc in processor.start:
            proc.core.usePerf = False
    set_ticks_per_cycle(processor)
    return processor


def get_frequency(config: dict) -> CPUTypes:
    return config["cpu"]["frequency"]


def get_start_cpu(config: dict) -> CPUTypes:
    return config["cpu"]["cpu_type"]["start"]


def get_switch_cpu(config: dict) -> CPUTypes:
    if bool(config["cpu"]["switch_cpu"]) == False:
        return select_cpu(config["cpu"]["cpu_type"]["start"])
    return select_cpu(config["cpu"]["cpu_type"]["switch"])


def get_num_cores(config: dict) -> int:
    return int(config["cpu"]["cores"])


def set_ticks_per_cycle(processor: AbstractProcessor) -> int:
    global _ticks_per_cycle
    if _ticks_per_cycle is not None:
        m5.util.fatal(f"[CONFIG, CPU]: Ticks per cycle cannot be recalculated")

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

    _ticks_per_cycle = clock.getValue()


def get_ticks_per_cycle() -> int:
    global _ticks_per_cycle
    if _ticks_per_cycle is None:
        m5.util.fatal(f"[CONFIG, CPU]: Ticks per cycle not calculated")
    return _ticks_per_cycle


def setup_cpu(p_yaml: str) -> "Processor":
    config = base.parse_yaml(p_yaml)
    return setup_processor(
        start_cpu=config["cpu"]["cpu_type"]["start"],
        switch_cpu=get_switch_cpu(config),
        num_cores=get_num_cores(config),
        clk_freq=config["cpu"]["frequency"],
    )


def parallelize(processor: AbstractProcessor, eventq_indices: list) -> None:
    if type(processor) == SimpleSwitchableProcessor:
        return parallelize_simple_switchable(processor, eventq_indices)
    m5.util.fatal(f"[CONFIG, CPU]: Cannot parallelize {type(processor)}")


def parallelize_simple_switchable(
    processor: SimpleSwitchableProcessor, eventq_indices: list
) -> None:
    if len(eventq_indices) != len(processor._switchable_cores[processor._start_key]):
        m5.util.fatal(
            f"[CONFIG, CPU]: Expected starting cores: {len(eventq_indices)} but got: {len(processor._switchable_cores[processor._start_key])}"
        )
    if len(eventq_indices) != len(processor._switchable_cores[processor._switch_key]):
        m5.util.fatal(
            f"[CONFIG, CPU]: Expected switchable cores: {len(eventq_indices)} but got: {len(processor._switchable_cores[processor._switch_key])}"
        )
    for i in range(len(eventq_indices)):
        m5.util.inform(
            f"[CONFIG, CPU]: Assigning SimpleSwitchableProcessor start ({i}) and stop ({i}) cores: {eventq_indices[i]}"
        )
        processor._switchable_cores[processor._start_key][
            i
        ].eventq_index = eventq_indices[i]
        processor._switchable_cores[processor._switch_key][
            i
        ].eventq_index = eventq_indices[i]
