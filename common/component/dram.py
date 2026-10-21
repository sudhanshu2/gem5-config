import m5

from gem5.components.memory.abstract_memory_system import AbstractMemorySystem


def setup_dram(config: dict) -> AbstractMemorySystem:
    config = config["dram"]
    memory_type = config["type"]
    if memory_type == "singlechannel":
        return create_singlechannel(config)
    m5.util.fatal(f"[CONFIG, DRAM]: Unknown type {memory_type}")


def create_singlechannel(config: dict) -> AbstractMemorySystem:
    standard = str(config["standard"]).lower()
    frequency = int(config["frequency"])

    if standard == "ddr4" and frequency == 2400:
        from gem5.components.memory.single_channel import SingleChannelDDR4_2400

        m5.util.inform("[CONFIG, DRAM]: Use Single Channel DDR4 2400")
        return SingleChannelDDR4_2400(size=config["size"])

    m5.util.fatal(
        f"[CONFIG, DRAM]: Unsupported single channel memory {standard} {frequency}"
    )
