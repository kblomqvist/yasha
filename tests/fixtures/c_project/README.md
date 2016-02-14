# Example project to test Yasha with C

Running

```bash
make
```

or

```bash
scons
```

under this folder will build the C source files from *src* folder into
separate build directory. The build directory will be created if not existed.

When using CMake the build directory needs to be manually created:

```bash
mkdir build && cd $_
cmake ..
make
```

From `src/` you will find yet another Makefile and SConstruct
files. Running `make` and `scons` there builds into the current
directory instead of build directory.
