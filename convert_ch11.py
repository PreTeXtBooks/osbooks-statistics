#!/usr/bin/env python3
"""
Complete conversion of Chapter 11 CNXML files to PreTeXt format
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

# Namespace definitions
CNXML_NS = {
    '': 'http://cnx.rice.edu/cnxml',
    'm': 'http://www.w3.org/1998/Math/MathML',
    'md': 'http://cnx.rice.edu/mdml'
}

# Register namespaces for parsing
for prefix, uri in CNXML_NS.items():
    if prefix:
        ET.register_namespace(prefix, uri)

def convert_mathml_to_latex(elem, namespaces=None):
    """Convert MathML to LaTeX"""
    if elem is None:
        return ""
    
    # Remove namespace prefix
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    
    # Handle text-only content (leaf nodes)
    text = (elem.text or '').strip()
    if text and len(list(elem)) == 0:
        # Apply symbol replacements for Greek letters and mathematical symbols
        # Note: Σ is mapped to \Sigma here, but gets special handling in
        # munder/munderover contexts where it becomes \sum (see those handlers)
        replacements = {
            'μ': r'\mu', 'σ': r'\sigma', 'π': r'\pi', 'θ': r'\theta',
            'χ': r'\chi', 'Σ': r'\Sigma',
            '−': '-', '–': '-', '≤': r'\leq', '≥': r'\geq',
            '≈': r'\approx', '∼': r'\sim', '~': r'\sim',
            '∞': r'\infty', '≠': r'\neq', '×': r'\times',
            '·': r'\cdot', '…': r'\ldots', '±': r'\pm'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    result = []
    
    for child in elem:
        ctag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        ctext = (child.text or '').strip()
        
        if ctag == 'mi':  # Identifier
            greek = {'μ': r'\mu', 'σ': r'\sigma', 'π': r'\pi', 'θ': r'\theta', 'Σ': r'\Sigma', 'χ': r'\chi'}
            result.append(greek.get(ctext, ctext))
        elif ctag == 'mn':  # Number
            result.append(ctext)
        elif ctag == 'mo':  # Operator
            ops = {'−': '-', '–': '-', '∼': r'\sim', '~': r'\sim',
                   '≤': r'\leq', '≥': r'\geq', '≈': r'\approx',
                   '×': r'\times', '·': r'\cdot', '≠': r'\neq',
                   '±': r'\pm', 'Σ': r'\sum'}
            result.append(ops.get(ctext, ctext))
        elif ctag == 'mtext':
            result.append(r'\text{' + ctext + '}' if ctext else '')
        elif ctag == 'mfrac':
            num = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            den = convert_mathml_to_latex(child[1]) if len(child) > 1 else ''
            result.append(r'\frac{' + num + '}{' + den + '}')
        elif ctag == 'msub':
            base = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            sub = convert_mathml_to_latex(child[1]) if len(child) > 1 else ''
            result.append(base + '_{' + sub + '}')
        elif ctag == 'msup':
            base = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            sup = convert_mathml_to_latex(child[1]) if len(child) > 1 else ''
            result.append(base + '^{' + sup + '}')
        elif ctag == 'msubsup':
            base = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            sub = convert_mathml_to_latex(child[1]) if len(child) > 1 else ''
            sup = convert_mathml_to_latex(child[2]) if len(child) > 2 else ''
            result.append(base + '_{' + sub + '}^{' + sup + '}')
        elif ctag == 'mover':
            base = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            over_elem = child[1] if len(child) > 1 else None
            if over_elem is not None:
                over_text = (over_elem.text or '').strip()
                if over_text == '¯' or over_text == '\u00AF':
                    result.append(r'\overline{' + base + '}')
                else:
                    result.append(base)
            else:
                result.append(base)
        elif ctag == 'msqrt':
            inner = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            result.append(r'\sqrt{' + inner + '}')
        elif ctag == 'munderover':
            # Handle operators with upper and lower limits (e.g., summation)
            # Note: In MathML, Σ is often encoded as <mi>Σ</mi>, but in LaTeX,
            # summation operators with limits should use \sum, not \Sigma
            base = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            if base == r'\Sigma':
                base = r'\sum'
            under = convert_mathml_to_latex(child[1]) if len(child) > 1 else ''
            over = convert_mathml_to_latex(child[2]) if len(child) > 2 else ''
            result.append(base + '_{' + under + '}^{' + over + '}')
        elif ctag == 'munder':
            # Handle operators with lower limits (e.g., summation without upper bound)
            # Note: Convert Σ to \sum in limit contexts for proper LaTeX rendering
            base = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            if base == r'\Sigma':
                base = r'\sum'
            under = convert_mathml_to_latex(child[1]) if len(child) > 1 else ''
            result.append(base + '_{' + under + '}')
        elif ctag == 'mrow':
            result.append(convert_mathml_to_latex(child))
        elif ctag == 'mtable':
            rows = []
            for row in child:
                cells = []
                for cell in row:
                    cells.append(convert_mathml_to_latex(cell))
                if cells:
                    rows.append(' '.join(cells))
            if rows:
                result.append(' \\\\ '.join(rows))
        else:
            # Recurse for unknown tags
            result.append(convert_mathml_to_latex(child))
        
        # Add tail
        if child.tail:
            tail = child.tail.strip()
            if tail:
                result.append(tail)
    
    return ''.join(result)

def xml_escape(text):
    """Escape XML special characters"""
    if not text:
        return text
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def extract_text(elem, namespaces):
    """Extract text with inline markup conversion"""
    if elem is None:
        return ""
    
    parts = []
    
    # Initial text
    if elem.text:
        parts.append(xml_escape(elem.text))
    
    # Process children
    for child in elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        if tag == 'math':
            latex = convert_mathml_to_latex(child)
            parts.append(f'<m>{latex}</m>')
        elif tag == 'emphasis':
            effect = child.get('effect', '')
            content = extract_text(child, namespaces)
            if effect == 'italics':
                # Check if it's likely a variable
                if len(content.strip()) <= 2 or content.strip() in ['X', 'Y', 'Z', 'P', 'Q', 'x', 'y', 'z', 'p', 'q', 'k', 'n']:
                    parts.append(f'<m>{content}</m>')
                else:
                    parts.append(f'<em>{content}</em>')
            elif effect == 'bold':
                parts.append(f'<alert>{content}</alert>')
            else:
                parts.append(content)
        elif tag == 'term':
            content = extract_text(child, namespaces)
            parts.append(f'<term>{content}</term>')
        elif tag == 'code':
            content = extract_text(child, namespaces)
            parts.append(f'<c>{content}</c>')
        elif tag == 'sup':
            content = extract_text(child, namespaces)
            parts.append(f'^{{{content}}}')
        elif tag == 'sub':
            content = extract_text(child, namespaces)
            parts.append(f'_{{{content}}}')
        elif tag == 'newline':
            count = int(child.get('count', '1'))
            parts.append('<nbsp/>' * count)
        elif tag == 'link':
            content = extract_text(child, namespaces)
            url = child.get('url', child.get('document', ''))
            if url:
                parts.append(f'<url href="{url}">{content}</url>')
            else:
                parts.append(content)
        else:
            # Recurse
            parts.append(extract_text(child, namespaces))
        
        # Tail text
        if child.tail:
            parts.append(xml_escape(child.tail))
    
    return ''.join(parts)

def process_para(para, namespaces, indent='    '):
    """Convert para to p"""
    text = extract_text(para, namespaces)
    text = text.strip()
    if not text:
        return ""
    return f'{indent}<p>{text}</p>\n'

def process_list(list_elem, namespaces, indent='    '):
    """Convert list to ul or ol"""
    list_type = list_elem.get('list-type', 'bulleted')
    tag = 'ol' if list_type == 'enumerated' else 'ul'
    
    result = f'{indent}<{tag}>\n'
    
    for item in list_elem.findall('.//{http://cnx.rice.edu/cnxml}item'):
        item_text = extract_text(item, namespaces).strip()
        result += f'{indent}  <li>{item_text}</li>\n'
    
    result += f'{indent}</{tag}>\n'
    return result

def process_equation(eq, namespaces, indent='    '):
    """Convert equation to me (display math)"""
    math_elem = eq.find('.//{http://www.w3.org/1998/Math/MathML}math')
    if math_elem is not None:
        latex = convert_mathml_to_latex(math_elem)
        return f'{indent}<me>{latex}</me>\n'
    return ""

def process_figure(fig, namespaces, indent='    '):
    """Convert figure"""
    fig_id = fig.get('id', '')
    
    result = f'{indent}<figure'
    if fig_id:
        result += f' xml:id="{fig_id}"'
    result += '>\n'
    
    # Caption
    caption = fig.find('.//{http://cnx.rice.edu/cnxml}caption')
    if caption is not None:
        cap_text = extract_text(caption, namespaces).strip()
        result += f'{indent}  <caption>{cap_text}</caption>\n'
    
    # Image
    image = fig.find('.//{http://cnx.rice.edu/cnxml}image')
    if image is not None:
        src = image.get('src', '')
        # Convert path
        src = src.replace('../../media/', 'media/')
        width = image.get('width', '')
        result += f'{indent}  <image source="{src}"'
        if width:
            # Convert pixel width to percentage if needed
            if width.isdigit():
                result += f' width="{int(width)//5}%"'
            else:
                result += f' width="{width}"'
        result += '/>\n'
    
    result += f'{indent}</figure>\n'
    return result

def process_example(ex, namespaces, indent='    '):
    """Convert example"""
    ex_id = ex.get('id', '')
    
    result = f'{indent}<example'
    if ex_id:
        result += f' xml:id="{ex_id}"'
    result += '>\n'
    
    # Title (if exists)
    title = ex.find('.//{http://cnx.rice.edu/cnxml}title')
    if title is not None and title.text:
        result += f'{indent}  <title>{title.text}</title>\n'
    
    # Process content
    content = ex.find('.//{http://cnx.rice.edu/cnxml}content')
    if content is None:
        content = ex
    
    # Handle problem/solution structure or direct content
    problem = ex.find('.//{http://cnx.rice.edu/cnxml}problem')
    solution = ex.find('.//{http://cnx.rice.edu/cnxml}solution')
    
    if problem is not None:
        result += f'{indent}  <statement>\n'
        for elem in problem:
            result += process_element(elem, namespaces, indent + '    ')
        result += f'{indent}  </statement>\n'
    else:
        # Process direct content
        for elem in content:
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag not in ['title']:
                result += process_element(elem, namespaces, indent + '  ')
    
    if solution is not None:
        result += f'{indent}  <solution>\n'
        for elem in solution:
            result += process_element(elem, namespaces, indent + '    ')
        result += f'{indent}  </solution>\n'
    
    result += f'{indent}</example>\n'
    return result

def process_note(note, namespaces, indent='    '):
    """Convert note"""
    note_id = note.get('id', '')
    note_class = note.get('class', '')
    
    # Map note classes to PreTeXt types
    note_map = {
        'chapter-objectives': 'note',
        'finger': 'note',
        'statistics': 'note',
        'calculator': 'note',
        'try': 'note',
    }
    
    note_type = note_map.get(note_class, 'note')
    
    result = f'{indent}<{note_type}'
    if note_id:
        result += f' xml:id="{note_id}"'
    result += '>\n'
    
    # Label (typically empty)
    label = note.find('.//{http://cnx.rice.edu/cnxml}label')
    
    # Title
    title = note.find('.//{http://cnx.rice.edu/cnxml}title')
    if title is not None and title.text:
        result += f'{indent}  <title>{title.text}</title>\n'
    
    # Process content
    for elem in note:
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag not in ['label', 'title']:
            result += process_element(elem, namespaces, indent + '  ')
    
    result += f'{indent}</{note_type}>\n'
    return result

def process_exercise(ex, namespaces, indent='    '):
    """Convert exercise or Try It"""
    ex_id = ex.get('id', '')
    ex_type = ex.get('type', '')
    
    result = f'{indent}<exercise'
    if ex_id:
        result += f' xml:id="{ex_id}"'
    result += '>\n'
    
    # Title (Try It)
    title = ex.find('.//{http://cnx.rice.edu/cnxml}title')
    if title is not None and title.text:
        result += f'{indent}  <title>{title.text}</title>\n'
    
    # Problem
    problem = ex.find('.//{http://cnx.rice.edu/cnxml}problem')
    if problem is not None:
        result += f'{indent}  <statement>\n'
        for elem in problem:
            result += process_element(elem, namespaces, indent + '    ')
        result += f'{indent}  </statement>\n'
    
    # Solution
    solution = ex.find('.//{http://cnx.rice.edu/cnxml}solution')
    if solution is not None:
        result += f'{indent}  <solution>\n'
        for elem in solution:
            result += process_element(elem, namespaces, indent + '    ')
        result += f'{indent}  </solution>\n'
    
    result += f'{indent}</exercise>\n'
    return result

def process_element(elem, namespaces, indent='    '):
    """Process a generic element"""
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    
    if tag == 'para':
        return process_para(elem, namespaces, indent)
    elif tag == 'list':
        return process_list(elem, namespaces, indent)
    elif tag == 'equation':
        return process_equation(elem, namespaces, indent)
    elif tag == 'figure':
        return process_figure(elem, namespaces, indent)
    elif tag == 'example':
        return process_example(elem, namespaces, indent)
    elif tag == 'note':
        return process_note(elem, namespaces, indent)
    elif tag == 'exercise':
        return process_exercise(elem, namespaces, indent)
    else:
        return ""

def convert_module(filepath, section_id, section_title):
    """Convert a CNXML module to PreTeXt section"""
    print(f"  Reading {filepath}...")
    
    # Parse XML
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Find content element
    content = root.find('.//{http://cnx.rice.edu/cnxml}content')
    if content is None:
        print(f"  Warning: No content found in {filepath}")
        return ""
    
    # Build section
    result = f'  <section xml:id="{section_id}">\n'
    result += f'    <title>{section_title}</title>\n\n'
    
    # Check if content has a section child (common in non-introduction modules)
    section_elem = content.find('.//{http://cnx.rice.edu/cnxml}section')
    if section_elem is not None:
        # Process elements within the section
        for elem in section_elem:
            result += process_element(elem, CNXML_NS, '    ')
    else:
        # Process all elements directly in content
        for elem in content:
            result += process_element(elem, CNXML_NS, '    ')
    
    result += '  </section>\n\n'
    
    return result

def main():
    """Main conversion"""
    modules_dir = Path('modules')
    
    # Check if running from repository root
    if not modules_dir.exists():
        print("Error: 'modules' directory not found.")
        print("Please run this script from the repository root directory.")
        return 1
    
    # Convert introduction (m79673)
    print("Converting m79673 (Introduction)...")
    intro_section = convert_module(
        modules_dir / 'm79673' / 'index.cnxml',
        'sec-chi-square-intro',
        'Introduction'
    )
    
    # Convert each section in correct order
    print("Converting m79674 (Facts About the Chi-Square Distribution)...")
    section1 = convert_module(
        modules_dir / 'm79674' / 'index.cnxml',
        'sec-facts-chi-square',
        'Facts About the Chi-Square Distribution'
    )
    
    print("Converting m79675 (Goodness-of-Fit Test)...")
    section2 = convert_module(
        modules_dir / 'm79675' / 'index.cnxml',
        'sec-goodness-of-fit-test',
        'Goodness-of-Fit Test'
    )
    
    print("Converting m79676 (Test of Independence)...")
    section3 = convert_module(
        modules_dir / 'm79676' / 'index.cnxml',
        'sec-test-independence',
        'Test of Independence'
    )
    
    print("Converting m79678 (Test for Homogeneity)...")
    section4 = convert_module(
        modules_dir / 'm79678' / 'index.cnxml',
        'sec-test-homogeneity',
        'Test for Homogeneity'
    )
    
    print("Converting m79679 (Comparison of the Chi-Square Tests)...")
    section5 = convert_module(
        modules_dir / 'm79679' / 'index.cnxml',
        'sec-comparison-chi-square-tests',
        'Comparison of the Chi-Square Tests'
    )
    
    print("Converting m79682 (Test of a Single Variance)...")
    section6 = convert_module(
        modules_dir / 'm79682' / 'index.cnxml',
        'sec-test-single-variance',
        'Test of a Single Variance'
    )
    
    print("Converting m79683 (Lab 1: Chi-Square Goodness-of-Fit)...")
    section7 = convert_module(
        modules_dir / 'm79683' / 'index.cnxml',
        'sec-chi-square-lab1',
        'Lab 1: Chi-Square Goodness-of-Fit'
    )
    
    print("Converting m79685 (Lab 2: Chi-Square Test of Independence)...")
    section8 = convert_module(
        modules_dir / 'm79685' / 'index.cnxml',
        'sec-chi-square-lab2',
        'Lab 2: Chi-Square Test of Independence'
    )
    
    # Assemble final document
    output = '<?xml version="1.0" encoding="UTF-8"?>\n'
    output += '<chapter xml:id="ch11-chi-square-distribution" xmlns:xi="http://www.w3.org/2001/XInclude">\n'
    output += '  <title>The Chi-Square Distribution</title>\n\n'
    
    # Add introduction section content
    output += intro_section
    
    # Add other sections
    output += section1
    output += section2
    output += section3
    output += section4
    output += section5
    output += section6
    output += section7
    output += section8
    
    output += '</chapter>\n'
    
    # Write output
    output_path = Path('pretext/source/ch11-chi-square-distribution.ptx')
    output_path.write_text(output)
    
    print(f"\nConversion complete! Written to {output_path}")
    print(f"Total length: {len(output)} characters")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
