import os

def reformatDocs():
    # Path to the directory where the documentation is kept
    docDir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "build", "docs", "content", "docs")
    docPath = os.path.join(docDir, "api-documentation.md")

    if os.path.exists(docPath):
        with open(docPath, "r", encoding="utf-8") as f:
            docLines = f.readlines()

        # For each line:
        # - If it contains :one: or :two: replace it with 1️⃣ or 2️⃣ respectively
        # - If it contains multiple #s, reduce the number of #s by 1

        newDocLines = []
        for i in range(len(docLines)):
            line = docLines[i]
            if ":one:" in line:
                line = line.replace(":one:", "1️⃣")
            if ":two:" in line:
                line = line.replace(":two:", "2️⃣")
            if line.startswith("#"):
                line = line[1:]
            newDocLines.append(line)

        # Write the new documentation to the file "api-documentation-edited.md" in the same directory
        with open(os.path.join(os.path.dirname(docPath), "api-documentation-edited.md"), "w", encoding="utf-8") as f:
            f.writelines(newDocLines)
        return True 
    else:
        return False

if __name__ == "__main__":
    if reformatDocs():
        print("Documentation reformatted")
    else:
        print("Documentation not found")