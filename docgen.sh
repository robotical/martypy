#!/bin/sh
pip install -r dev-requirements.txt
pydoc-markdown
python -c "from docgen.ReformatDocs import reformatDocs as rD; rD()"
pbcopy < "$(dirname $0)/build/docs/content/docs/api-documentation-edited.md"