#!/bin/sh
pip install -r dev-requirements.txt
API_DOCS_DIR="$(dirname $0)/build/docs/content/docs"
pydoc-markdown
python -c "from docgen.ReformatDocs import reformatDocs as rD; rD()"
pbcopy < $API_DOCS_DIR/api-documentation-edited.md

# if pandoc fails it might be because pandoc is not installed
if ! pandoc -r markdown_mmd $API_DOCS_DIR/api-documentation-edited.md -t dokuwiki -o $API_DOCS_DIR/docs-wiki.wiki; then
    echo "An error occurred with pandoc. Please ensure that pandoc is installed on your system."
    exit 1
fi

echo "Documentation has been generated!"