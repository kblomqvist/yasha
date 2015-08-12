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

def parse_conf(src, file):
    jinja_params = {}

    if not file:
        file = find_conf(src)
        file = click.open_file(file, "rb") if file else None

    if file:
        conf_name, conf_extension = os.path.splitext(file.name)
        if conf_extension in CONF_EXTENSIONS["toml"]:
            jinja_params = toml.load(file)
        if conf_extension in CONF_EXTENSIONS["yaml"]:
            jinja_params = yaml.load(file)

    return jinja_params

def load_filters(src, file):
    if not file:
        file = find_conf(src, [".py"])
        file = click.open_file(file, "rb") if file else None

    if file:
        import imp
        pathname = os.path.basename(file.name)
        name = os.path.splitext(pathname)[0]
        name = name.replace(".", "_")
        desc = (".py", "rb", imp.PY_SOURCE)
        return imp.load_module(name, file, pathname, desc)

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


