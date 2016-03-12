import yasha

def postprocess(vars):
    vars["foo"] = "bar" # foo should always be bar
    return vars

class TomlParser(yasha.TomlParser):
    def parse(self, file):
        vars = yasha.TomlParser.parse(self, file)
        return postprocess(vars)