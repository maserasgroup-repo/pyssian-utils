import setuptools
import re

with open('pyssianutils/_version.py','r') as F: 
    __version__ = re.findall(r'[0-9]*\.[0-9]*\.[0-9]',F.read())[0]

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
  name = 'pyssianutils',
  version = __version__,
  packages = setuptools.find_packages(),
  description = "A CLI with utils for everyday tasks in CompChem developed with pyssian",
  author = 'Raúl Pérez-Soto',
  author_email = 'rperezsoto.research@gmail.com',
  long_description=long_description,
  long_description_content_type="text/x-rst",
  url = 'https://github.com/maserasgroup-repo/pyssian-utils',
  keywords = ['compchem', 'gaussian','parser'],
  classifiers = ['Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: 3.9',
                 ],
  install_requires=['setuptools',
                    'pathlib',
                    'numpy',
                    'pyssian>=1.1',
                    'platformdirs'],
  extras_require={'plotting':['matplotlib','plotly']},
  python_requires='>=3.6',
  package_data = {'resources': ['pyssianutils/resources/defaults.ini',
                                'pyssianutils/resources/templates/slurm/example.txt',
                                'pyssianutils/resources/templates/slurm/example.json']},
  include_package_data=True,
  scripts = ['pyssianutils/pyssianutils'],
  project_urls={'Bug Reports': 'https://github.com/maserasgroup-repo/pyssian-utils/issues',
                'Source': 'https://github.com/maserasgroup-repo/pyssian-utils',
                'Docs' : 'https://maserasgroup-repo.github.io/pyssian-utils/'
               },
)
