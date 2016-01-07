from yasha import __version__
from setuptools import setup, find_packages

setup(
    name="yasha",
    author="Kim Blomqvist",
    author_email="kblomqvist@iki.fi",
    version=__version__,
    description="A command-line tool to render Jinja templates",
    keywords=["jinja", "code generator"],
    license="MIT",
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
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Code Generators",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
    ],
    url="https://github.com/kblomqvist/yasha",
    download_url="https://github.com/kblomqvist/yasha/tarball/" + __version__,
)
