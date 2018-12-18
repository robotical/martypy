try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as f:
    readme = f.read()


setup(
    name="martypy",
    version="1.2.post1",
    description="Client library for Marty the Robot by Robotical Ltd",
    long_description=readme,
    author="Robotical Ltd",
    author_email="hello@robotical.io",
    maintainer='Robotical Ltd',
    maintainer_email='hello@robotical.io',
    packages=['martypy'],
    url='http://github.com/robotical/martypy',
    license='Apache 2.0',
    install_requires=[
        'six>=1.10.0',
        'requests>=2.21.0',
        'urllib3>=1.24.1',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
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

