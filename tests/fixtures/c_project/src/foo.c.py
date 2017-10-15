import yasha.parsers

def postprocess(variables):
    variables["foo"] = "bar"  # foo should always be bar
    return variables

def parse_toml(file):
	variables = yasha.parsers.parse_toml(file)
	return postprocess(variables)
