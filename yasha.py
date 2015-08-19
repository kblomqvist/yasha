import os
import click
import yaml
import pytoml as toml


CONF_EXTENSIONS = {"toml": [".toml"], "yaml": [".yaml", ".yml"]}
CONF_EXTENSIONS_LIST = sum(CONF_EXTENSIONS.values(), [])

class TomlParser():
    file_extensions = [".toml"]

    def parse(file):
        import pytoml as toml
        return toml.load(file)

class YamlParser():
    file_extensions = [".yaml", ".yml"]

    def parse(file):
        import yaml
        return yaml.load(file)

def possible_variables_filepaths(template):
    paths = ["."]
    src_path = os.path.abspath(template.name)
    for _ in range(src_path.count(os.path.sep)):
        paths.append(os.path.join(paths[-1], ".."))
    return paths

def possible_variables_filenames(template):
    files = []
    src_name, src_extension = os.path.splitext(template.name)
    src_name = os.path.basename(src_name)
    src_name = src_name.split(".")
    for i, _ in enumerate(src_name):
        files.insert(0, ".".join(src_name[0:i+1]))
    return files

def find_variables(template, extensions=CONF_EXTENSIONS_LIST):
    variables = None
    filepaths = possible_variables_filepaths(template)
    filenames = possible_variables_filenames(template)
    
    for path in filepaths:
        if variables:
            break
        for variables_name in filenames:
            if variables:
                break
            for ext in extensions:
                test = os.path.join(path, variables_name + ext)
                if os.path.isfile(test):
                    variables = os.path.abspath(test)
                    break

    return variables

def parse_variables(template, file):
    jinja_params = {}

    if not file:
        file = find_variables(template)
        file = click.open_file(file, "rb") if file else None

    if file:
        conf_name, conf_extension = os.path.splitext(file.name)
        if conf_extension in CONF_EXTENSIONS["toml"]:
            jinja_params = toml.load(file)
        if conf_extension in CONF_EXTENSIONS["yaml"]:
            jinja_params = yaml.load(file)

    return jinja_params

def load_extensions(template, file):
    if not file:
        file = find_variables(template, [".jinja-ext"])
        file = click.open_file(file, "rb") if file else None

    if file:
        import imp
        pathname = os.path.basename(file.name)
        name = os.path.splitext(pathname)[0]
        name = name.replace(".", "_")
        desc = (".py", "rb", imp.PY_SOURCE)
        return imp.load_module(name, file, pathname, desc)

def load_jinja(searchpath, extmodule):
    import inspect
    import jinja2

    if not extmodule:
        return jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath))

    extattr = [getattr(extmodule, x) for x in dir(extmodule) if not x.startswith("__")]
    tests = []; filters = []; classes = []

    for x in extattr:
        if inspect.isfunction(x):
            if x.__name__.startswith("test_"):
                tests.append(x)
            elif x.__name__.startswith("filter_"):
                filters.append(x)
        elif inspect.isclass(x):
            if issubclass(x, jinja2.ext.Extension):
                classes.append(x)

    jinja = jinja2.Environment(extensions=classes,
        loader=jinja2.FileSystemLoader(searchpath))

    for test in tests:
        jinja.tests[test.__name__.replace("test_", "")] = test
    for filt in filters:
        jinja.filters[filt.__name__.replace("filter_", "")] = filt
    return jinja

@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("template", type=click.File("rb"))
@click.option("--variables", "-a", type=click.File("rb"), envvar="YASHA_VARIABLES", help="Template variables file name.")
@click.option("--extensions", "-e", type=click.File("rb"), envvar="YASHA_EXTENSIONS", help="Custom Jinja extensions file name.")
@click.option("--output", "-o", type=click.File("wb"), help="Output file name. Standard output works too.")
@click.option("--no-variables", is_flag=True, help="Omit template variables.")
@click.option("--no-extensions", is_flag=True, help="Omit Jinja extensions.")
def cli(template, variables, extensions, output, no_variables, no_extensions):
    """This script reads the given Jinja template and renders its content
    into new file, which name is derived from the given template name. For
    example the rendered foo.c.jinja template will be written into foo.c if
    not explicitly specified."""

    vardict = parse_variables(template, variables) if not no_variables else {}
    extmodule = load_extensions(template, extensions) if not no_extensions else None

    t_realpath = os.path.realpath(template.name)
    t_basename = os.path.basename(t_realpath)
    t_dirname = os.path.dirname(t_realpath)

    jinja = load_jinja(t_dirname, extmodule)
    t = jinja.get_template(t_basename)

    if not output:
        o_realpath = os.path.splitext(t_realpath)[0]
        output = click.open_file(o_realpath, "wb")

    output.write(t.render(vardict))
