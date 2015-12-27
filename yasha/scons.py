"""
The MIT License (MIT)

Copyright (c) 2015 Kim Blomqvist

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

from SCons.Builder import BuilderBase
from SCons.Scanner import Scanner
from SCons.Action import Action, CommandGeneratorAction

class CBuilderBase(BuilderBase):
    def _execute(self, env, target, source, ow={}, exec_kw={}):
        """
        Override _execute() to remove C header files from the sources list
        """
        def is_not_header(file):
            suffix = str(file).rsplit(".", 1)[1]
            headers = ["h", "hh", "hpp"]
            return True if suffix not in headers else False

        src = BuilderBase._execute(self, env, target, source, ow, exec_kw)
        return [x for x in src if is_not_header(x)]

def CBuilder(action="yasha -MD $SOURCE -o $TARGET"):
    """Yasha SCons builder for C"""
    def target_scan(node, env, path):
        try: # Resolve template dependencies from the generated .d file
            with open(str(node) + ".d") as f:
                deps = f.readline().split()[1:]
                return env.File(deps)
        except:
            return []

    def source_scan(node, env, path):
        return []

    def emit(target, source, env):
        env.Clean(target[0], str(target[0]) + ".d")
        return target, source

    def gtor(source, target, env, for_signature):
        cmd = action.replace("$SOURCE", str(source[0]))
        cmd = cmd.replace("$TARGET", str(target[0]))
        return cmd

    return CBuilderBase(
        action = CommandGeneratorAction(gtor, {}),
        #action = Action(action),
        emitter = emit,
        target_scanner = Scanner(function=target_scan),
        source_scanner = Scanner(function=source_scan),
        single_source = True,
    )
