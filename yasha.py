import os
import click
import yaml
import pytoml as toml

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

def find_conf(src, extensions=CONF_EXTENSIONS_LIST):
    conf = None
    conf_paths = possible_conf_paths(src)
    conf_names = possible_conf_names(src)
    
    for conf_path in conf_paths:
        if conf:
            break
        for conf_name in conf_names:
            if conf:
                break
            for ext in extensions:
                test = os.path.join(conf_path, conf_name + ext)
                if os.path.isfile(test):
                    conf = os.path.abspath(test)
                    break

    return conf

def parse_conf(src, conf):
    jinja_params = {}

    if not conf:
        conf = find_conf(src)
        conf = click.open_file(conf, "rb")

    if conf:
        conf_name, conf_extension = os.path.splitext(conf.name)
        if conf_extension in CONF_EXTENSIONS["toml"]:
            jinja_params = toml.load(conf)
        if conf_extension in CONF_EXTENSIONS["yaml"]:
            jinja_params = yaml.load(conf)

    return jinja_params

def load_filters(src, module):
    if not module:
        module = find_conf(src, [".py"])
    else: # is click file
        module = module.name

    if module:
        import sys, importlib
        sys.path.append(os.path.dirname(module))
        module = os.path.basename(module)
        module = os.path.splitext(module)[0]
        return importlib.import_module(module)

@click.command()
@click.argument("src", type=click.File("rb"))
@click.option("--conf", type=click.File("rb"))
@click.option("--no-conf", is_flag=True)
@click.option("--filters", type=click.File("rb"))
@click.option("--no-filters", is_flag=True)
def cli(src, conf, no_conf, filters, no_filters):
    jinja_params = parse_conf(src, conf) if not no_conf else {}
    filters = load_filters(src, filters) if not no_filters else None

    click.echo(jinja_params)

    if filters:
        print dir(filters)


