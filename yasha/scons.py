from SCons.Builder import BuilderBase
from SCons.Scanner import Scanner
from SCons.Action import Action

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

def CBuilder(action="yasha -MD $SOURCE"):
    """Yasha SCons builder for C"""
    def scan(node, env, path):
        try: # Resolve template dependencies from the generated .d file
            with open(str(node) + ".d") as f:
                return env.File(f.readline().split()[1:])
        except:
            return []

    def emit(target, source, env):
        env.Clean(target[0], str(target[0]) + ".d")
        return target, source

    return CBuilderBase(
        action = Action(action),
        emitter = emit,
        target_scanner = Scanner(function=scan),
        single_source = True
    )

