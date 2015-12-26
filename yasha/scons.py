from SCons.Builder import BuilderBase
import SCons.Scanner
import SCons.Action

class CBuilderBase(BuilderBase):
    def _execute(self, env, target, source, overwarn={}, executor_kw={}):
        """
        Override _execute() to remove C header files from the sources list
        """
        def is_not_header(file):
            headers = ["h", "hh", "hpp"]
            if str(file).rsplit(".", 1)[1] not in headers:
                return True
            return False

        src = BuilderBase._execute(self, env, target, source, overwarn, executor_kw)
        return [x for x in src if is_not_header(x)]

def CBuilder():
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
        action = SCons.Action.Action("yasha -MD $SOURCE"),
        emitter = emit,
        target_scanner = SCons.Scanner.Scanner(function=scan),
        single_source = True
    )

