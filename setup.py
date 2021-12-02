import setuptools

__version__ = '0.0.1'

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
  name = 'pyssianutils',
  version = __version__,
  packages = ['pyssianutils',],
  description = """ Command line utils developed with pyssian for everyday tasks
                    in computational chemistry """,
  author = 'Raúl Pérez-Soto',
  author_email = 'rperezsoto.research@gmail.com',
  long_description=long_description,
  long_description_content_type="text/x-rst",
  url = 'https://github.com/fmaserasgroup-repo/pyssian-utils',
  keywords = ['compchem', 'gaussian','parser'],
  classifiers = ['License :: OSI Approved :: MIT License',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: 3.9',
                 ],
  install_requires=['setuptools','pathlib','numpy', 'pyssian'],
  extras_require={'plotting functions':'matplotlib'},
  python_requires='>=3.6',
  include_package_data=True,
  scripts = ['pyssianutils/pyssian-thermo.py',
             'pyssianutils/pyssian-potential.py',
             'pyssianutils/pyssian-submit.py',
             'pyssianutils/pyssian-inputHT.py',
             'pyssianutils/pyssian-asinput.py',
             'pyssianutils/pyssian-tddft-cubes.py',
             'pyssianutils/pyssian-track.py'],
  project_urls={'Bug Reports': 'https://github.com/maserasgroup-repo/pyssian-utils/issues',
                'Source': 'https://github.com/maserasgroup-repo/pyssian-utils',
                'Docs' : 'https://maserasgroup-repo.github.io/pyssian-utils/'
               },
)
