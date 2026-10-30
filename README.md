# BlastRadius — Python Code Impact Analyzer

BlastRadius is a small developer tool that uses Python's Abstract Syntax Tree (AST) to find functions and in-file function-call relationships. Select a function you plan to change and it reports direct and transitive callers that may need regression testing.

## MVP features
- Paste Python code or upload a `.py` file.
- Parse function definitions with Python AST.
- Build a lightweight caller → callee relationship list.
- Traverse reverse dependencies to estimate a change's impact radius.
- Suggest focused tests and document static-analysis limitations.
- Includes unit tests for dependency traversal and invalid targets.

## Run locally
Requires Python 3.10 or newer.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser and click **Load sample**, then **Analyze impact**.

## Run tests
```bash
python -m unittest discover -s tests -v
```

## Example
Given `leaf()`, `middle()` calling `leaf()`, and `top()` calling `middle()`, selecting `leaf` should identify `middle` as a direct caller and `top` as an indirect caller.

## Current limitations
This is a first prototype, not a complete static analyzer. It may miss dynamic dispatch, aliases, reflection, imported call relationships, decorators, and runtime-generated calls. Attribute calls are matched by method name only, so results can include false positives (for example, unrelated `.save()` methods). It analyzes one source file at a time and does not execute uploaded code.

## Security notes
- The app parses source without executing it.
- The upload size is limited to 1 MB.
- The development server binds to `127.0.0.1`; do not expose it publicly as-is.
- Use only source code you are authorized to analyze.

## Roadmap
1. Resolve same-name functions more precisely.
2. Add directory/repository scanning.
3. Add pytest test discovery and coverage integration.
4. Add a dependency graph visualization.
5. Evaluate accuracy on small real repositories and document missed/extra dependencies.

## Project status
MVP starter implementation. Validate its behavior with the included tests before describing it as complete.
