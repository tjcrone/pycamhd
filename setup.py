from setuptools import setup
import re

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

version = find_version('serial', '__init__.py')

setup(name='pycamhd',
      version=version,
      description='Module for interacting with OOI CamHD video data',
      long_description='README.rst',
      url='https://bitbucket.org/tjcrone/pycamhd',
      author='Timothy Crone',
      author_email='tjcrone@gmail.com',
      license='MIT',
      packages=['camhd'])
