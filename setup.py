import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
  name = 'pyssianutils',
  packages = ['pyssianutils',],
  description = """ Command line utils developed with pyssian for everyday tasks
                    in computational chemistry """,
  author = 'Raúl Pérez-Soto',
  author_email = 'rperezsoto.research@gmail.com',
  long_description=long_description,
  long_description_content_type="text/x-rst",
  url = 'https://github.com/fmaserasgroup-repo/pyssian-utils',
  keywords = ['compchem', 'gaussian','parser'],
  classifiers = ["Programming Language :: Python :: 3",],
  install_requires=['setuptools','pathlib','numpy', 'pyssian','matplotlib'],
  python_requires='>=3.6',
  include_package_data=True,
  scripts = ['pyssianutils/pyssian-thermo.py',
             'pyssianutils/pyssian-potential.py',
             'pyssianutils/pyssian-submit.py',
             'pyssianutils/pyssian-inputHT.py',
             'pyssianutils/pyssian-asinput.py',
             'pyssianutils/pyssian-tddft-cubes.py',
             'pyssianutils/pyssian-track.py'],
)
