from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name="martypy",
    version="3.2.0",
    description="Python library for Marty the Robot V1 and V2",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Robotical",
    author_email="hello@robotical.io",
    copyright="Robotical",
    maintainer='Robotical',
    maintainer_email='hello@robotical.io',
    packages=find_packages(),
    url='http://github.com/robotical/martypy',
    license='Apache 2.0',
    install_requires=[
        'pyserial',
    ],
    extras_require={
        "tests": [
            "pytest",
        ],
    },
    keywords=[
        'ros',
        'robot',
        'marty',
        'marty the robot',
        'robotical',
    ],
    classifiers= [
        # As from https://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        "Operating System :: OS Independent",
        'License :: OSI Approved :: Apache Software License',
    ]
)

# To Publish:
# First, build a source distribution:
# $ python setup.py sdist
# Then upload this to PyPi (have ~/.pypirc exist)
# $ twine upload dist/*

