from typing import Optional

from m5.objects import Root

from gem5.utils.override import overrides
from board import serial
import component


class ParallelBoard(serial.SerialBoard):
    def __init__(self, sim_quantum: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self._sim_quantum = sim_quantum

    @overrides(serial.SerialBoard)
    def _pre_instantiate(self, full_system: Optional[bool] = None) -> Root:
        root = super()._pre_instantiate(full_system)
        eventq_indices = list(range(1, len(self.get_processor().get_cores()) + 1))
        component.cpu.parallelize(self.get_processor(), eventq_indices)
        component.cache.parallelize(self.cache_hierarchy, eventq_indices)
        root.sim_quantum = self._sim_quantum * component.cpu.get_ticks_per_cycle()
        return root
