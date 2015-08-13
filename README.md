# yasha

Yasha is a code generator based on [Jinja](http://jinja.pocoo.org/) template engine.

For example, the following command-line call

```
$ yasha foo.jinja
```

will render `foo.jinja` template into a new file named as `foo`. See how the created file is named according to the template. The template itself remains unchanged.

Template variables can be defined in a separate configuration file: [TOML](https://github.com/toml-lang/toml) and [YAML](http://www.yaml.org/start.html) are supported. Yasha will look for the config file if not given explicitly. For example, the above example tries to find `foo.toml` or `foo.yaml` (or `foo.yml`) from the same folder with the tamplate. If the file is not found, subfolders will be checked until the root directory.

An example of explicit use of configuration file would be:

```
$ yasha foo.jinja --conf foo.toml
```

Yasha accept configuration file given via environment variables as well:

```
$ export YASHA_CONF=$HOME/foo.toml
$ yasha foo.jinja
```

In case the configuration file shouldn't be used in spite of its existence there's an option ``--no-conf``:

```
$ yasha foo.jinja --no-conf
```

## Configuration file sharing

Imagine that you would be writing C code and have the following two templates in two different folders

```
  include/
    foo.h.jinja
  source/
    foo.c.jinja
```

and you would like to share the same configuration file between these two templates. So instead of creating separate `foo.h.toml` and `foo.c.toml` files you can make one `foo.toml` like this:

```
  include/
    foo.h.jinja
  source/
    foo.c.jinja
  foo.toml
```

Now when you call

```
$ yasha include/foo.h.jinja
$ yasha source/foo.c.jinja
```

the `foo.toml` configuration file is used for both templates. For your convenience here is the file listing after the above two yasha calls:

```
  include/
    foo.h
    foo.h.jinja
  source/
    foo.c
    foo.c.jinja
  foo.toml
```

## Custom Jinja extensions

Seems like the day has arrived when you would like to use custom [Jinja filters](http://jinja.pocoo.org/docs/dev/api/#custom-filters) and/or [tests](http://jinja.pocoo.org/docs/dev/api/#custom-tests) within your templates. Fortunately yasha has been a far-wise and supports these out of box. The functionality is similar to the configuration file usage described above. So for a given `foo.jinja` template file, yasha will automatically seek `foo.jinja-ext` file.

Here is an example of the `foo.jinja-ext` file containing a filter and a test.

```python
import math

def filter_datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)
    
def test_prime(n):
    if n == 2:
        return True
    for i in xrange(2, int(math.ceil(math.sqrt(n))) + 1):
        if n % i == 0:
            return False
    return True
```

As can be seen the file is standard Python, although the file extension is not `.py` but `.jinja-ext`. Furthermore, note that the functions intended to work as a filter hves to be prefixed by `filter_`. Similarly test functions have to be prefixed by `test_`.

Here is shown how the two extensions described above would be used within a template.

```jinja
{{ pub_date|datetimeformat }}
{{ pub_date|datetimeformat('%d-%m-%Y') }}

{% if 42 is prime %}
    42 is a prime number
{% else %}
    42 is not a prime number
{% endif %}
```

In addition to filters and tests, larger extensions ([extension classes](http://jinja.pocoo.org/docs/dev/extensions/#module-jinja2.ext)) are also supported. Meaning that all defined classes having an _Extension_ suffix in their name are available within the template.

And as you might guess, instead of relying on the automatic extension file look up, it can be given explicitly as well.

```
$ yasha foo.jinja --extensions foo.py
```

There's also `--no-extensions` option operating in a similar manner with `--no-conf`. It's also worth mentioning that the file sharing works for the extensions file as it works for the configuration file and that the environment variable name for the extensions is YASHA_EXTENSIONS.
