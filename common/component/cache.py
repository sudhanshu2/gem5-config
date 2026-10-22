import m5

from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.cachehierarchies.abstract_cache_hierarchy import (
    AbstractCacheHierarchy,
)
from gem5.components.cachehierarchies.classic.no_cache import NoCache
from gem5.components.cachehierarchies.ruby.mesi_three_level_cache_hierarchy import (
    MESIThreeLevelCacheHierarchy,
)
from gem5.utils.requires import requires


def setup_cache(config: dict) -> AbstractCacheHierarchy:
    cache_type = config["cache"]["type"]
    if cache_type == "nocache":
        return build_nocache(config)
    if cache_type == "ruby":
        return build_ruby(config)
    if cache_type == "simple":
        return build_simple(config)
    m5.util.fatal(f"[CONFIG, CACHE]: Unknown type {cache_type}")


def build_nocache(config: dict) -> AbstractCacheHierarchy:
    m5.util.inform("[CONFIG, CACHE]: Use No Cache")
    return NoCache()


def build_ruby(config: dict) -> AbstractCacheHierarchy:
    cache_config = config["cache"]
    levels = int(cache_config["levels"])

    if levels == 3:
        requires(
            coherence_protocol_required=CoherenceProtocol.MESI_THREE_LEVEL,
        )

        from gem5.components.cachehierarchies.ruby.mesi_three_level_cache_hierarchy import (
            MESIThreeLevelCacheHierarchy,
        )

        m5.util.inform("[CONFIG, CACHE]: Use MESI Three Level Cache")
        return MESIThreeLevelCacheHierarchy(
            l1d_size=cache_config["l1d"]["size"],
            l1d_assoc=cache_config["l1d"]["assoc"],
            l1i_size=cache_config["l1i"]["size"],
            l1i_assoc=cache_config["l1i"]["assoc"],
            l2_size=cache_config["l2"]["size"],
            l2_assoc=cache_config["l2"]["assoc"],
            l3_size=cache_config["l3"]["size"],
            l3_assoc=cache_config["l3"]["assoc"],
            num_l3_banks=cache_config["l3"]["slices"],
        )

    m5.util.fatal(f"[CONFIG, CACHE]: Unsupported Ruby cache levels {levels}")


def build_simple(config: dict) -> AbstractCacheHierarchy:
    cache_config = config["cache"]
    levels = int(cache_config["levels"])

    if levels == 3:
        from gem5.components.cachehierarchies.classic.private_l1_private_l2_shared_l3_cache_hierarchy import (
            PrivateL1PrivateL2SharedL3CacheHierarchy,
        )

        m5.util.inform("[CONFIG, CACHE]: Simple Three Level Cache")
        return PrivateL1PrivateL2SharedL3CacheHierarchy(
            l1d_size=cache_config["l1d"]["size"],
            l1d_assoc=cache_config["l1d"]["assoc"],
            l1i_size=cache_config["l1i"]["size"],
            l1i_assoc=cache_config["l1i"]["assoc"],
            l2_size=cache_config["l2"]["size"],
            l2_assoc=cache_config["l2"]["assoc"],
            l3_size=cache_config["l3"]["size"],
            l3_assoc=cache_config["l3"]["assoc"],
        )

    m5.util.fatal(f"[CONFIG, CACHE]: Unsupported simple cache levels {levels}")


def parallelize(cache_hierarchy: AbstractCacheHierarchy, eventq_indices: list) -> None:
    if type(cache_hierarchy) == MESIThreeLevelCacheHierarchy:
        return parallelize_mesi_three_level(cache_hierarchy, eventq_indices)
    if type(cache_hierarchy) == NoCache:
        return parallelize_nocache(cache_hierarchy, eventq_indices)
    m5.util.fatal(f"[CONFIG, CACHE]: Cannot parallelize {type(cache_hierarchy)}")


def parallelize_mesi_three_level(
    cache_hierarchy: MESIThreeLevelCacheHierarchy, eventq_indices: list
) -> None:
    if len(eventq_indices) != len(cache_hierarchy.ruby_system.l1_controllers):
        m5.util.fatal(
            f"[CONFIG, CACHE]: Expected L1 caches: {len(eventq_indices)} but got: {len(cache_hierarchy.ruby_system.l1_controllers)}"
        )
    if len(eventq_indices) != len(cache_hierarchy.ruby_system.l2_controllers):
        m5.util.fatal(
            f"[CONFIG, CACHE]: Expected L2 caches: {len(eventq_indices)} but got: {len(cache_hierarchy.ruby_system.l2_controllers)}"
        )
    for i in range(len(eventq_indices)):
        m5.util.inform(
            f"[CONFIG, CACHE]: Assigning Ruby MESIThreeLevelCacheHierarchy L1 ({i}) and L2 ({i}) caches: {eventq_indices[i]}"
        )
        cache_hierarchy.ruby_system.l1_controllers[i].eventq_index = eventq_indices[i]
        cache_hierarchy.ruby_system.l2_controllers[i].eventq_index = eventq_indices[i]


def parallelize_nocache(cache_hierarchy: NoCache, eventq_indices: list) -> None:
    m5.util.warn("[CONFIG, CACHE]: Skipped parallelizing NoCache")
