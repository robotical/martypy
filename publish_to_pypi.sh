#!/bin/bash

# install necessary tools
python -m pip install --upgrade setuptools wheel
python -m pip install --upgrade twine

# create source and wheel distributions (do we need a wheel distribution?)
python setup.py sdist # bdist_wheel

# upload to Test PyPI
twine upload --repository-url https://test.pypi.org/legacy/ dist/* -u robotical -p <password>

# install the package from Test PyPI
# python -m pip install --index-url https://test.pypi.org/simple/ martypy

# pause and wait for user confirmation
echo "Press enter to continue with uploading to PyPI, or Ctrl+C to cancel"
read

# upload to PyPI
twine upload dist/* -u robotical -p <password>

echo "Martypy package has been uploaded to PyPI"
