"""
The MIT License (MIT)

Copyright (c) 2015-2016 Kim Blomqvist

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
from SCons.Builder import BuilderBase
from SCons.Scanner import Scanner
from SCons.Action import Action, CommandGeneratorAction

def is_c_file(file):
    suffix = os.path.splitext(str(file))[1]
    accept = [".c", ".cc", ".cpp", ".h", ".hh", ".hpp", ".s", ".S", ".asm"]
    return True if suffix in accept else False

class CBuilderBase(BuilderBase):
    def _execute(self, env, target, source, ow={}, exec_kw={}):
        """
        Override _execute() to remove C header files from the sources list
        """
        sources = BuilderBase._execute(self, env, target,source, ow, exec_kw)
        return [x for x in sources if is_c_file(x)]

def CBuilder(action="yasha -MD $SOURCE -o $TARGET"):
    """
    Yasha SCons builder for C
    """

    def target_scan(node, env, path):
        """No used. Most likely will be removed."""
        try: # Resolve template dependencies from the generated .d file
            with open(str(node) + ".d") as f:
                # IMPORTANT! Don't duplicate template dependency, thus [2:]
                deps = f.readline().split()[2:]
                return env.File(deps)
        except:
            return []

    def source_scan(node, env, path):
        """
        TODO: Doesn't take custom parses into account.
        """
        deps = []
        file, extension = os.path.splitext(str(node))
        while extension:
            for suffix in [".toml", ".yml", ".yaml", ".j2ext", ".jinja-ext"]:
                dep = file + suffix
                if os.path.isfile(dep):
                    deps.append(dep)
            file, extension = os.path.splitext(file)
        return env.File(deps)

    def emit(target, source, env):
        env.Clean(target[0], str(target[0]) + ".d")
        return target, source

    def gtor(source, target, env, for_signature):
        cmd = ""
        if is_c_file(target[0]):
            cmd = action.replace("$SOURCE", str(source[0]))
            cmd = cmd.replace("$TARGET", str(target[0]))
        return cmd

    return CBuilderBase(
        action = CommandGeneratorAction(gtor, {}),
        #action = Action(action),
        emitter = emit,
        #target_scanner = Scanner(function=target_scan),
        #source_scanner = Scanner(function=source_scan),
        single_source = True
    )
