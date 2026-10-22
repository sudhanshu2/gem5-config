import pathlib
import time
import yaml
from typing import Optional

import m5

from gem5.resources.resource import obtain_resource

PATHS_CONFIG = f"{pathlib.Path.home()}/gem5-paths.yaml"
REPO_PATH = pathlib.Path(__file__).resolve().parent.parent


def parse_yaml(p_yaml: str) -> "yaml.YAMLObject":
    with open(p_yaml) as f_yaml:
        try:
            yaml_obj = yaml.safe_load(f_yaml)
            return yaml_obj
        except yaml.YAMLError as err:
            m5.util.fatal(err)


def save_yaml(yaml_obj: "yaml.YAMLObject", p_yaml: str) -> None:
    f_yaml = open(p_yaml, "w")
    yaml.dump(yaml_obj, f_yaml)
    f_yaml.close()


def get_paths() -> dict:
    p_config = f"{REPO_PATH}/config.yaml"
    if pathlib.Path(PATHS_CONFIG).is_file() == True:
        m5.util.inform(f"[CONFIG, BASE]: Reading paths from {PATHS_CONFIG}")
        d_paths = parse_yaml(PATHS_CONFIG)
    else:
        m5.util.warn("[CONFIG, BASE]: Using default paths without benchmark image")
        d_paths = {
            "image": {
                "os": obtain_resource("x86-ubuntu-22.04-img").get_local_path(),
                "benchmark": None,
            },
            "linux": obtain_resource("x86-linux-kernel-5.4.49").get_local_path(),
            "output": f"{REPO_PATH}/m5out",
        }
    d_paths["config"] = p_config
    m5.util.inform(str(d_paths))
    return d_paths


def setup() -> [dict, dict, str, str]:
    paths = get_paths()
    config = parse_yaml(paths["config"])
    p_output_base = paths["output"]
    p_output = f"{p_output_base}/{time.strftime('%Y.%m.%d_%H.%M.%S')}"
    pathlib.Path(p_output).mkdir(parents=True, exist_ok=True)
    m5.options.outdir = p_output
    p_checkpoint = f"{p_output}/checkpoint"
    config["paths"] = paths
    save_yaml(config, f"{p_output}/config.yaml")
    m5.util.inform(f"[CONFIG, BASE]: Output directory: {p_output}")
    return config, paths, p_output, p_checkpoint
