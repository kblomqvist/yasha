import os
import click
import pytoml as toml
import yaml

CONF_EXTENSIONS = {"toml": [".toml"], "yaml": [".yaml", ".yml"]}
CONF_EXTENSIONS_LIST = sum(CONF_EXTENSIONS.values(), [])

def possible_conf_paths(src):
    conf_paths = ["."]
    src_path = os.path.abspath(src.name)
    for _ in range(src_path.count(os.path.sep)):
        conf_paths.append(os.path.join(conf_paths[-1], ".."))
    return conf_paths

def possible_conf_names(src):
    conf_names = []
    src_name, src_extension = os.path.splitext(src.name)
    src_name = os.path.basename(src_name)
    src_name = src_name.split(".")
    for i, _ in enumerate(src_name):
        conf_names.insert(0, ".".join(src_name[0:i+1]))
    return conf_names

def parse_conf(src, conf):
    jinja_params = {}

    if not conf:
        conf_paths = possible_conf_paths(src)
        conf_names = possible_conf_names(src)
        for conf_path in conf_paths:
            if conf:
                break
            for conf_name in conf_names:
                for extension in CONF_EXTENSIONS_LIST:
                    f = os.path.join(conf_path, conf_name + extension)
                    try: conf = click.open_file(f, "rb")
                    except: pass

    if conf:
        conf_name, conf_extension = os.path.splitext(conf.name)
        if conf_extension in CONF_EXTENSIONS["toml"]:
            jinja_params = toml.load(conf)
        if conf_extension in CONF_EXTENSIONS["yaml"]:
            jinja_params = yaml.load(conf)

    return jinja_params

@click.command()
@click.argument("src", type=click.File("rb"))
@click.option("--conf", type=click.File("rb"))
@click.option("--no-conf", is_flag=True)
@click.option("--filters", type=click.File("rb"))
@click.option("--no-filters", is_flag=True)
def cli(src, conf, no_conf, filters, no_filters):
    """Example"""
    jinja_params = parse_conf(src, conf) if not no_conf else {}
    #print possible_conf_paths(src)
    #print possible_conf_names(src)
    click.echo(jinja_params)


