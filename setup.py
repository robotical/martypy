try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as f:
    readme = f.read()


setup(
    name="martypy",
    version="2.0",
    description="Python library to communicate with Marty the Robot V1 and V2",
    long_description=readme,
    author="Robotical",
    author_email="hello@robotical.io",
    copyright="Robotical",
    maintainer='Robotical',
    maintainer_email='hello@robotical.io',
    packages=['martypy'],
    url='http://github.com/robotical/martypy',
    license='Apache 2.0',
    install_requires=[
        'requests>=2.22.0',
    ],
    keywords=[
        'ros',
        'robot',
        'marty',
        'marty the robot',
        'robotical',
    ],
    classifiers=(
        # As from https://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        #'Environment :: Web Environment',
        #'Operating System :: POSIX',
        'License :: OSI Approved :: Apache Software License',
    )
)

# To Publish:
# First, build a source distribution:
# $ python setup.py sdist
# Then upload this to PyPi (have ~/.pypirc exist)
# $ twine upload dist/*

