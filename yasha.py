import os
import click
import pytoml as toml
import yaml

CONF_EXTENSIONS = {"toml": [".toml"], "yaml": [".yaml", ".yml"]}
CONF_EXTENSIONS_LIST = sum(CONF_EXTENSIONS.values(), [])

def possible_conf_names(src_name):
    conf_names = []
    src_name = src_name.split(".")
    for i, _ in enumerate(src_name):
        conf_names.insert(0, ".".join(src_name[0:i+1]))
    return conf_names

def parse_conf(src, conf):
    jinja_params = {}

    if not conf:
        src_path = os.path.abspath(src.name)
        src_name, src_extension = os.path.splitext(src.name)

        conf_path = "." + os.path.sep
        conf_names = possible_conf_names(src_name)
        for _ in range(src_path.count(os.path.sep)):
            if conf:
                break
            for conf_name in conf_names:
                for ext in CONF_EXTENSIONS_LIST:
                    f = conf_path + conf_name + ext
                    print f
                    try: conf = click.open_file(f, "rb")
                    except: pass
            conf_path = conf_path + ".." + os.path.sep

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
def cli(src, conf):
    """Example"""
    jinja_params = parse_conf(src, conf)
    click.echo(jinja_params)


