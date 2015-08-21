from setuptools import setup, find_packages

setup(
    name="yasha",
    version="1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
        "Jinja2",
        "pytoml",
        "pyyaml",
    ],
    entry_points='''
        [console_scripts]
        yasha=yasha.scripts.yasha:cli
    ''',
)