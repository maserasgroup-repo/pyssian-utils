import setuptools

__version__ = '0.0.1'

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
  name = 'pyssianutils',
  version = __version__,
  packages = setuptools.find_packages(),
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
  install_requires=['setuptools','pathlib','numpy', 'pyssian>=1.1'],
  extras_require={'plotting functions':'matplotlib'},
  python_requires='>=3.6',
  package_data = {'resources': ['pyssianutils/resources/defaults.ini',
                                'pyssianutils/resources/templates/empty.txt']},
  include_package_data=True,
  scripts = ['pyssianutils/pyssianutils'],
  project_urls={'Bug Reports': 'https://github.com/maserasgroup-repo/pyssian-utils/issues',
                'Source': 'https://github.com/maserasgroup-repo/pyssian-utils',
                'Docs' : 'https://maserasgroup-repo.github.io/pyssian-utils/'
               },
)
