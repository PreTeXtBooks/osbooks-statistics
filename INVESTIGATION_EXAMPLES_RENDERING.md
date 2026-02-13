# Investigation: Examples with Task Elements Rendering Issue

## Issue Report
**Date**: 2026-02-13
**Issue**: Example 2.2.6 (xml:id="exampid2") reportedly not rendering fully - only showing from "Calculate the width..." onwards

## Issue Description
The reported problem was that examples containing `<task>` elements were not rendering paragraphs before and after the task, specifically:
- Missing: Introductory paragraphs with data listing
- Missing: Paragraphs after `</task>` closes
- Missing: Figure after the task

## Investigation Results

### Environment
- **PreTeXt CLI Version**: 0.8.3
- **Build Target**: HTML
- **Repository**: PreTeXtBooks/osbooks-statistics

### Examples Identified
Found 2 examples in the codebase with `<task>` elements and content after them:
1. **exampid2** (ch02-descriptive-statistics.ptx, lines 1828-1856)
2. **element-649** (ch02-descriptive-statistics.ptx)

### Test Results
Built HTML output and inspected rendering:

#### Example 2.2.6 (exampid2)
✅ **ALL CONTENT RENDERS CORRECTLY**
- Paragraph (p-386): Data listing
- Paragraph (p-387): "Eleven students buy one book..."  
- Task (a): "Calculate the width..." with solution
- Paragraph (p-390): "Notice that we may choose different rational numbers..."
- Paragraph (p-391): "The following histogram displays..."
- Figure 2.2.7: Histogram image

#### Example 2.7.8 (element-649)
✅ **ALL CONTENT RENDERS CORRECTLY**
- Task statement and solution
- Paragraph (p-1075): "The long left whisker in the box plot..."

### XML Structure
Both examples use an informal structure:
```xml
<example>
  <p>Intro paragraph</p>
  <p>More intro</p>
  <task>
    <statement>...</statement>
    <solution>...</solution>
  </task>
  <p>Content after task</p>
  <figure>...</figure>
</example>
```

This structure mixes narrative content (paragraphs, figures) directly with the `<task>` element at the same level.

### Alternative Approach Tested
Attempted using PreTeXt's structured authoring pattern:
```xml
<example>
  <statement>
    <p>Intro content</p>
  </statement>
  <task>...</task>
  <conclusion>
    <p>Content after</p>
  </conclusion>
</example>
```

**Result**: This caused the conclusion content to NOT render inline with the example. The conclusion was omitted from the output.

## Conclusion

**STATUS**: ✅ NO ISSUE FOUND - Content renders correctly

The reported rendering issue **could not be reproduced** with PreTeXt CLI version 0.8.3. All examples with tasks and surrounding content render completely and correctly.

### Possible Explanations
1. **Version-specific**: Issue may have existed in an older PreTeXt version but is resolved in 0.8.3
2. **Environment-specific**: Issue may occur in specific deployment or viewing contexts not tested
3. **Resolution**: PreTeXt may have been updated to support the informal structure properly

### Recommendation
**No code changes needed**. The current XML structure works correctly and produces the expected output.

## Screenshots
- Before-click: Shows collapsed knowl
- Scrolled view: Shows Example 2.2.6 fully expanded with all content visible
- All paragraphs, task, and figure render as expected

## Files Investigated
- `/home/runner/work/osbooks-statistics/osbooks-statistics/pretext/source/ch02-descriptive-statistics.ptx`
- Lines 1828-1856: Example xml:id="exampid2"
- Output: `/home/runner/work/osbooks-statistics/osbooks-statistics/pretext/output/html/sec-histograms-frequency-polygons.html`
