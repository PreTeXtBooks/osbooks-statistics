#!/usr/bin/env python3
"""
Convert Chapter 6 CNXML files to PreTeXt format
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

# Namespace definitions for CNXML
CNXML_NS = {
    '': 'http://cnx.rice.edu/cnxml',
    'm': 'http://www.w3.org/1998/Math/MathML',
    'md': 'http://cnx.rice.edu/mdml'
}

def convert_mathml_to_latex(mathml_elem):
    """Convert MathML elements to LaTeX."""
    if mathml_elem is None:
        return ""
    
    tag = mathml_elem.tag.replace('{http://www.w3.org/1998/Math/MathML}', 'm:')
    
    # Handle text content
    if mathml_elem.text:
        text = mathml_elem.text.strip()
        # Greek letters and symbols
        replacements = {
            'μ': r'\mu', 'σ': r'\sigma', 'π': r'\pi',
            '−': '-', '–': '-', '≤': r'\leq', '≥': r'\geq',
            '≈': r'\approx', '∼': r'\sim', '~': r'\sim',
            '∞': r'\infty', '≠': r'\neq'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    # Process child elements
    result = ""
    for child in mathml_elem:
        child_tag = child.tag.replace('{http://www.w3.org/1998/Math/MathML}', '')
        
        if child_tag == 'mi':  # Identifier
            text = child.text or ''
            # Greek letters
            if text in ['μ', 'sigma', 'σ', 'π', 'theta', 'θ']:
                greek_map = {'μ': r'\mu', 'sigma': r'\sigma', 'σ': r'\sigma', 
                           'π': r'\pi', 'theta': r'\theta', 'θ': r'\theta'}
                result += greek_map.get(text, text)
            else:
                result += text
        
        elif child_tag == 'mn':  # Number
            result += child.text or ''
        
        elif child_tag == 'mo':  # Operator
            op = child.text or ''
            op_map = {'−': '-', '–': '-', '∼': r'\sim', '~': r'\sim',
                     '≤': r'\leq', '≥': r'\geq', '≈': r'\approx',
                     '×': r'\times', '·': r'\cdot', '≠': r'\neq'}
            result += op_map.get(op, op)
        
        elif child_tag == 'mfrac':  # Fraction
            num = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            den = convert_mathml_to_latex(child[1]) if len(child) > 1 else ''
            result += r'\frac{' + num + '}{' + den + '}'
        
        elif child_tag == 'msub':  # Subscript
            base = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            sub = convert_mathml_to_latex(child[1]) if len(child) > 1 else ''
            result += base + '_{' + sub + '}'
        
        elif child_tag == 'msup':  # Superscript
            base = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            sup = convert_mathml_to_latex(child[1]) if len(child) > 1 else ''
            result += base + '^{' + sup + '}'
        
        elif child_tag == 'mover':  # Over (like bar)
            base = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            over = child[1].text if len(child) > 1 else ''
            if over == '¯' or 'accent' in child.attrib.values():
                result += r'\bar{' + base + '}'
            else:
                result += base
        
        elif child_tag == 'msqrt':  # Square root
            inner = convert_mathml_to_latex(child[0]) if len(child) > 0 else ''
            result += r'\sqrt{' + inner + '}'
        
        elif child_tag == 'mrow':  # Group
            result += convert_mathml_to_latex(child)
        
        elif child_tag == 'mtext':  # Text
            result += child.text or ''
        
        elif child_tag == 'mtable':  # Table (alignment)
            for row in child:
                for cell in row:
                    result += convert_mathml_to_latex(cell) + ' '
        
        else:
            # Recursively process unknown tags
            result += convert_mathml_to_latex(child)
        
        # Add tail text
        if child.tail:
            result += child.tail
    
    return result

def extract_text_with_math(elem, namespaces):
    """Extract text content from element, converting math as needed."""
    if elem is None:
        return ""
    
    text_parts = []
    
    # Add initial text
    if elem.text:
        text_parts.append(elem.text)
    
    # Process children
    for child in elem:
        tag = child.tag.replace('{http://cnx.rice.edu/cnxml}', '').replace('{http://www.w3.org/1998/Math/MathML}', 'm:')
        
        if tag == 'm:math':
            # Convert MathML to LaTeX
            latex = convert_mathml_to_latex(child)
            text_parts.append('<m>' + latex + '</m>')
        elif tag == 'emphasis':
            effect = child.get('effect', '')
            content = extract_text_with_math(child, namespaces)
            if effect == 'italics':
                # Check if it's a math variable
                if len(content.strip()) == 1 or content.strip() in ['X', 'Y', 'Z', 'x', 'y', 'z', 'k', 'n', 'p', 'q']:
                    text_parts.append('<m>' + content + '</m>')
                else:
                    text_parts.append('<em>' + content + '</em>')
            elif effect == 'bold':
                text_parts.append('<alert>' + content + '</alert>')
            else:
                text_parts.append(content)
        elif tag == 'term':
            content = extract_text_with_math(child, namespaces)
            text_parts.append('<term>' + content + '</term>')
        elif tag == 'list':
            # Handle lists within paragraphs (shouldn't happen but just in case)
            text_parts.append(extract_text_with_math(child, namespaces))
        elif tag == 'sup':
            content = extract_text_with_math(child, namespaces)
            text_parts.append('<sup>' + content + '</sup>')
        elif tag == 'sub':
            content = extract_text_with_math(child, namespaces)
            text_parts.append('<sub>' + content + '</sub>')
        elif tag == 'code':
            content = extract_text_with_math(child, namespaces)
            text_parts.append('<c>' + content + '</c>')
        elif tag == 'link':
            # Handle links
            content = extract_text_with_math(child, namespaces)
            text_parts.append(content)  # Simplified - may need document attribute
        elif tag == 'newline':
            count = int(child.get('count', '1'))
            text_parts.append('\n' * count)
        else:
            # Recursively process other elements
            text_parts.append(extract_text_with_math(child, namespaces))
        
        # Add tail text
        if child.tail:
            text_parts.append(child.tail)
    
    return ''.join(text_parts)

def process_cnxml_file(filepath):
    """Read and parse a CNXML file."""
    tree = ET.parse(filepath)
    root = tree.getroot()
    return root

def write_ptx_file(output_path, content):
    """Write PreTeXt content to file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """Main conversion function."""
    
    # Read all source files
    modules_dir = Path('/home/runner/work/osbooks-statistics/osbooks-statistics/modules')
    
    files = {
        'intro': modules_dir / 'm79640' / 'index.cnxml',
        'standard': modules_dir / 'm79641' / 'index.cnxml',
        'using': modules_dir / 'm79643' / 'index.cnxml',
        'lab_lap': modules_dir / 'm79644' / 'index.cnxml',
        'lab_pinkie': modules_dir / 'm79645' / 'index.cnxml'
    }
    
    # Parse files
    trees = {}
    for key, filepath in files.items():
        trees[key] = process_cnxml_file(filepath)
        print(f"Parsed {key}: {filepath}")
    
    print("\nConversion script ready. Files parsed successfully.")
    print("Note: Full conversion requires custom handling for each section.")
    print("Due to complexity, manual conversion with assistance is recommended.")

if __name__ == '__main__':
    main()
