from setuptools import setup

setup(
    name="yasha",
    version="0.1",
    py_modules=["yasha"],
    install_requires=[
        "Click",
        "Jinja2",
        "pytoml",
        "pyyaml",
    ],
    entry_points='''
        [console_scripts]
        yasha=yasha:cli
    ''',
)