import pathlib
import time
import yaml
from typing import Optional

import m5

from gem5.resources.resource import obtain_resource

PATHS_CONFIG = f"{pathlib.Path.home()}/gem5-paths.yaml"
REPO_PATH = pathlib.Path(__file__).resolve().parent.parent


def parse_yaml(yaml_path: str) -> dict:
    with open(yaml_path) as f_yaml:
        try:
            yaml_obj = yaml.safe_load(f_yaml)
            return dict(yaml_obj)
        except yaml.YAMLError as err:
            m5.util.fatal(err)


def save_yaml(yaml_obj: dict, yaml_path: str) -> None:
    f_yaml = open(yaml_path, "w")
    yaml.dump(yaml_obj, f_yaml)
    f_yaml.close()


def get_paths() -> dict:
    config_path = f"{REPO_PATH}/config.yaml"
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
    d_paths["config"] = config_path
    m5.util.inform(str(d_paths))
    return d_paths


def setup(restore: str = None) -> [dict, dict, str, str]:
    paths = get_paths()
    config = parse_yaml(paths["config"])
    output_path_base = paths["output"]
    output_path = f"{output_path_base}/{time.strftime('%Y.%m.%d_%H.%M.%S')}"
    pathlib.Path(output_path).mkdir(parents=True, exist_ok=True)
    m5.options.outdir = output_path
    checkpoint_path = f"{output_path}/checkpoint"
    config["paths"] = paths
    if restore is not None:
        config["paths"]["restore"] = restore
    save_yaml(config, f"{output_path}/config.yaml")
    m5.util.inform(f"[CONFIG, BASE]: Output directory: {output_path}")
    return config, paths, output_path, checkpoint_path
