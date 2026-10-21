import shutil
import pathlib
import time
import yaml

import m5


def parse_yaml(p_yaml: str) -> "yaml.YAMLObject":
    with open(p_yaml) as f_yaml:
        try:
            yaml_obj = yaml.safe_load(f_yaml)
            return yaml_obj
        except yaml.YAMLError as err:
            m5.util.fatal(err)


def setup(p_config: str) -> ["yaml.YAMLObject", str, str]:
    config = parse_yaml(p_config)
    p_output = f"{config['output']}/{time.strftime('%Y.%m.%d_%H.%M.%S')}"
    pathlib.Path(p_output).mkdir(parents=True, exist_ok=True)
    m5.options.outdir = p_output
    p_checkpoint = f"{p_output}/checkpoint"
    shutil.copy(p_config, f"{p_output}/config.yaml")
    m5.util.inform(f"[CONFIG, BASE]: Output directory: {p_output}")
    return config, p_output, p_checkpoint
