@echo off

pip install -r dev-requirements.txt
pydoc-markdown
python -c "from docgen.ReformatDocs import reformatDocs as rD; rD()"
clip < "%~dp0\build\docs\content\docs\api-documentation-edited.md"

REM Change to the directory where pandoc command needs to be executed
cd /d "%~dp0\build\docs\content\docs"

REM Execute pandoc and check if it fails
pandoc -r markdown_mmd api-documentation-edited.md -t dokuwiki -o docs-wiki.wiki
if ERRORLEVEL 1 (
    echo An error occurred with pandoc. Please ensure that pandoc is installed on your system.
    exit /b 1
)

REM Documentation has been generated!