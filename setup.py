from setuptools import setup
import io, re, os

def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

version = find_version('pycamhd', '__init__.py')

setup(
    name='pycamhd',
    version=version,
    description='Module for interacting with OOI CamHD video data',
    long_description='README.rst',
    install_requires=[
        'numpy',
        'av>=0.4.0',
        'requests',
    ],
    url='https://github.com/tjcrone/pycamhd',
    author='Timothy Crone',
    author_email='tjcrone@gmail.com',
    license='MIT',
    packages=['pycamhd'])
