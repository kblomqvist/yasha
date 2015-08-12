# yasha

Yasha is a code generator based on [Jinja](http://jinja.pocoo.org/) template engine. For example:

```
$ yasha foo.jinja
```

will render `foo.jinja` Jinja template file into new file called `foo`.

Template variables can be defined in a separate configuration file. [TOML](https://github.com/toml-lang/toml) and [YAML](http://yaml.org/) are supported. Yasha will look for this file if not given explicitly. For example, the above example call tries to find `foo.toml` or `foo.yaml` (or `foo.yml`) first from the same folder with `foo.jinja` and if not found there subfolders will be checked.

An example of explicit use of configuration file would be:

```
$ yasha foo.jinja --conf foo.toml
```

And finally if configuration file shouldn't be used in spite of its existence, ``--no-conf`` can be used.

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

the `foo.toml` configuration file is used for both templates. And just for your convenience here is the file listing after the above two yasha calls:

```
  include/
    foo.h
    foo.h.jinja
  source/
    foo.c
    foo.c.jinja
  foo.toml
```

## Custom Jinja filters

Seems like the day has arrived when you would like use a [custom Jinja filter](http://jinja.pocoo.org/docs/dev/api/#custom-filters) in your template file. Fortunately yasha has been far-wise and supports this out of box. Like configuration file, yasha will automatically look for `foo.py` file for custom filters.

An example of explicit use of filters file would be:

```
$ yasha foo.jinja --conf foo.toml --filters foo.py
```

There's also `--no-filters` option operating in a similar manner with `--no-conf`. And finally I want to mention that the file sharing works for filters as it works for the configuration file.
