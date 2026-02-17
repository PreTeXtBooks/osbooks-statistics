# PreTeXt Version of Statistics

This directory contains the PreTeXt version of the OpenStax Statistics textbook.

## Disclaimer

**Important:** This PreTeXt version is currently **incomplete and under active development**. This is an unofficial conversion of the [OpenStax Statistics textbook](https://openstax.org/details/books/statistics) to PreTeXt format. While we have made every effort to accurately convert the content and maintain fidelity with the original OpenStax version, some content may be missing, incorrectly formatted, or differ from the original.

**Please refer to the [official OpenStax Statistics textbook](https://openstax.org/details/books/statistics) as the authoritative source.**

Full credit goes to OpenStax, Barbara Illowsky, Susan Dean, and all contributors to the original Statistics textbook for creating this valuable educational resource. This PreTeXt conversion is provided as an alternative format option and maintains the same Creative Commons Attribution 4.0 International License as the original work.

## Directory Structure

```
pretext/
├── project.ptx          # Build configuration file
├── publication.ptx      # Publication settings
├── source/              # Source files for the book
│   ├── main.ptx         # Main book structure
│   ├── ch01-sampling-and-data.ptx
│   ├── ch02-descriptive-statistics.ptx
│   ├── ch03-probability-topics.ptx
│   ├── ch04-discrete-random-variables.ptx
│   ├── ch05-continuous-random-variables.ptx
│   ├── ch06-normal-distribution.ptx
│   ├── ch07-central-limit-theorem.ptx
│   ├── ch08-confidence-intervals.ptx
│   ├── ch09-hypothesis-testing-one-sample.ptx
│   ├── ch10-hypothesis-testing-two-samples.ptx
│   ├── ch11-chi-square-distribution.ptx
│   ├── ch12-linear-regression-correlation.ptx
│   └── ch13-f-distribution-anova.ptx
└── output/              # Generated output (created during build)
```

## About PreTeXt

PreTeXt is an XML-based authoring and publishing system for scholarly documents, particularly designed for textbooks in mathematics and science. It allows authors to write content once and publish to multiple formats including HTML, PDF, EPUB, and more.

Learn more at: https://pretextbook.org/

## Current Status

The PreTeXt structure has been initialized with:

- ✅ Basic project configuration (`project.ptx`)
- ✅ Publication settings (`publication.ptx`)
- ✅ Main book structure with frontmatter and backmatter (`source/main.ptx`)
- ✅ All 13 chapter files with section placeholders
- ⏳ Chapter content (to be migrated from CNXML modules)

## Next Steps

The following steps are needed to complete the PreTeXt version:

1. **Content Migration**: Convert content from CNXML modules to PreTeXt XML format
2. **Media Files**: Add and reference images, diagrams, and other media
3. **Exercises**: Convert interactive exercises and problems
4. **Examples**: Format worked examples and "Try It" problems
5. **Mathematical Content**: Ensure all mathematical notation is properly formatted using LaTeX
6. **Cross-References**: Add internal links and cross-references
7. **Index Terms**: Add index entries throughout the text

## Building the PreTeXt Book

Once content is added, you can build the book using the PreTeXt-CLI:

```bash
# Install PreTeXt-CLI (if not already installed)
pip install pretextbook

# Navigate to the pretext directory
cd pretext

# Build HTML version
pretext build html

# Build PDF version
pretext build pdf

# View the HTML output
pretext view html
```

### Media Files

The `pretext/media` directory is a symbolic link to the `../media` directory at the repository root, which contains all images and media files. This allows PreTeXt to access the images during the build process. The `publication.ptx` file is configured to look for external media in the `../media` directory relative to the `source/` directory.

## Chapter Structure

Each chapter follows this structure:

```xml
<chapter xml:id="unique-id">
  <title>Chapter Title</title>
  <introduction>
    <!-- Chapter introduction -->
  </introduction>
  
  <section xml:id="section-id">
    <title>Section Title</title>
    <!-- Section content -->
  </section>
  
  <!-- More sections... -->
  
  <conclusion>
    <!-- Chapter conclusion -->
  </conclusion>
</chapter>
```

## File Mapping

The PreTeXt chapters correspond to the following CNXML collections:

| PreTeXt Chapter | CNXML Collection | Module IDs |
|----------------|------------------|------------|
| ch01 | Sampling and Data | m79592-m79598 |
| ch02 | Descriptive Statistics | m79599-m79608 |
| ch03 | Probability Topics | m79609-m79618 |
| ch04 | Discrete Random Variables | m79620-m79629 |
| ch05 | Continuous Random Variables | m79631-m79637 |
| ch06 | The Normal Distribution | m79640-m79645 |
| ch07 | The Central Limit Theorem | m79647-m79652 |
| ch08 | Confidence Intervals | m79653-m79659 |
| ch09 | Hypothesis Testing with One Sample | m79660-m79666 |
| ch10 | Hypothesis Testing with Two Samples | m79667-m79672 |
| ch11 | The Chi-Square Distribution | m79673-m79685 |
| ch12 | Linear Regression and Correlation | m79686-m79700 |
| ch13 | F Distribution and One-Way ANOVA | m79701-m79708 |

## License

This work is licensed under a Creative Commons Attribution 4.0 International License, consistent with the OpenStax Statistics textbook.
