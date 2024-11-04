import numpy

from distutils.core import setup
from Cython.Build import cythonize

modules = cythonize(["inpaint.pyx", "newton.pyx", "collate.pyx", "feature_sign.pyx"], language_level = "2")
for e in modules:
    e.include_dirs.append(numpy.get_include())

setup(
    ext_modules=modules,
    options={'build_ext': {'build_lib': 'rebook'}}
)
