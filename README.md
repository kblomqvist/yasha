# yasha

Yasha is a code generator based on [Jinja](http://jinja.pocoo.org/) template engine.

For example, the following command-line call

```
$ yasha foo.jinja
```

will render `foo.jinja` Jinja template file into a new file named as `foo`. See how the `.jinja` file extension is removed.

Template variables can be defined in a separate configuration file. [TOML](https://github.com/toml-lang/toml) and [YAML](http://www.yaml.org/start.html) are supported. Yasha will look for this file if not given explicitly. For example, the above example call tries to find `foo.toml` or `foo.yaml` (or `foo.yml`) first from the same folder with `foo.jinja` and if not found there subfolders will be checked.

An example of explicit use of configuration file would be:

```
$ yasha foo.jinja --conf foo.toml
```

Finally if the configuration file shouldn't be used in spite of its existence, ``--no-conf`` can be used.

## Configuration file sharing

Imagine that you would be writing a C code and have the following template files in two separate folders

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

## Custom Jinja filters and tests

Seems like the day has arrived when you would like to use [custom Jinja filters](http://jinja.pocoo.org/docs/dev/api/#custom-filters) or [tests](http://jinja.pocoo.org/docs/dev/api/#custom-tests) in your template file. Fortunately yasha has been a far-wise and supports this out of box. The functionality is the same as above for the configuration file. So for a given `foo.jinja` template file, yasha will automatically seek `foo.py` file where you can define your custom Jinja filter and test functions.

An example of `foo.py` file could be:

```python
import math

def filter_datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)
    
def test_is_prime(n):
    if n == 2:
        return True
    for i in xrange(2, int(math.ceil(math.sqrt(n))) + 1):
        if n % i == 0:
            return False
    return True
```

When these custom filters and tests are used in the template file, `filter_` and `test_` function prefixes are removed:

```jinja
{{ pub_date|datetimeformat }}
{{ pub_date|datetimeformat('%d-%m-%Y') }}

{% if 42 is prime %}
    42 is a prime number
{% else %}
    42 is not a prime number
{% endif %}
```

Instead of relying on the automatic custom file look up, it can be given explicitly too:

```
$ yasha foo.jinja --conf foo.toml --custom foo.py
```

There's also `--no-custom` option operating in a similar manner with `--no-conf`. It's also worth mentioning that the file sharing works for custom file as it works for the configuration file.
