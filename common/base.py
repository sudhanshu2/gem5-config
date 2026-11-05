import os
import time
import yaml

REPO_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def parse_yaml(yaml_path: str) -> dict:
    with open(yaml_path) as f_yaml:
        yaml_obj = yaml.safe_load(f_yaml)
        return dict(yaml_obj)


def save_yaml(yaml_obj: dict, yaml_path: str) -> None:
    f_yaml = open(yaml_path, "w")
    yaml.dump(yaml_obj, f_yaml)
    f_yaml.close()


def get_paths(args: dict) -> dict:
    import m5
    from gem5.resources.resource import obtain_resource

    not_none_args = {}
    for key, value in args.items():
        if value is not None:
            not_none_args[key] = value
    args = not_none_args

    if "config" in args:
        config_path = args["config"]
    else:
        config_path = f"{REPO_PATH}/config.yaml"
    m5.util.inform(f"[CONFIG, BASE]: Config: {config_path}")

    if "os_image" in args:
        os_path = args["os_image"]
    else:
        os_path = obtain_resource("x86-ubuntu-22.04-img").get_local_path()
    m5.util.inform(f"[CONFIG, BASE]: OS image: {os_path}")

    if "benchmark_image" in args:
        benchmark_path = args["benchmark_image"]
    else:
        benchmark_path = None
    m5.util.inform(f"[CONFIG, BASE]: Benchmark image: {benchmark_path}")

    if "kernel" in args:
        kernel_path = args["kernel"]
    else:
        kernel_path = obtain_resource("x86-linux-kernel-5.4.49").get_local_path()
    m5.util.inform(f"[CONFIG, BASE]: Kernel: {kernel_path}")

    if "outdir" in args:
        output_path = args["outdir"]
    else:
        output_path = f"{m5.options.outdir}/{time.strftime('%Y.%m.%d_%H.%M.%S')}"
    m5.options.outdir = output_path
    m5.util.inform(f"[CONFIG, BASE]: Output: {output_path}")

    if "restore" in args:
        restore_path = args["restore"]
    else:
        restore_path = None
    m5.util.inform(f"[CONFIG, BASE]: Restore: {restore_path}")

    return {
        "config": config_path,
        "image": {
            "os": os_path,
            "benchmark": benchmark_path,
        },
        "kernel": kernel_path,
        "output": output_path,
        "restore": restore_path,
    }


def setup(paths: dict) -> [dict, str]:
    import m5

    config = parse_yaml(paths["config"])
    output_path = paths["output"]
    os.makedirs(output_path, exist_ok=True)
    config["paths"] = paths
    save_yaml(config, f"{output_path}/config.yaml")
    m5.util.inform(f"[CONFIG, BASE]: Output directory: {output_path}")
    return config, output_path
