# Distribution
```bash
# Package
pip install setuptools

# Distribute
# Instal to local system: $ pip install dist/cicv-0.0.1.tar.gz
python setup.py sdist --no-compile bdist_wheel

# Update load to PyPI
pip install twine
twine upload dist/*
```