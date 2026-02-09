#!/usr/bin/env python3
"""
Complete conversion of Chapter 6 CNXML files to PreTeXt format
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
    
    # Handle text-only content
    text = (elem.text or '').strip()
    if text and len(list(elem)) == 0:
        # Apply symbol replacements
        replacements = {
            'μ': r'\mu', 'σ': r'\sigma', 'π': r'\pi', 'θ': r'\theta',
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
            greek = {'μ': r'\mu', 'σ': r'\sigma', 'π': r'\pi', 'θ': r'\theta', 'Σ': r'\Sigma'}
            result.append(greek.get(ctext, ctext))
        elif ctag == 'mn':  # Number
            result.append(ctext)
        elif ctag == 'mo':  # Operator
            ops = {'−': '-', '–': '-', '∼': r'\sim', '~': r'\sim',
                   '≤': r'\leq', '≥': r'\geq', '≈': r'\approx',
                   '×': r'\times', '·': r'\cdot', '≠': r'\neq',
                   '±': r'\pm'}
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
    
    # Title
    title = ex.find('.//{http://cnx.rice.edu/cnxml}title')
    if title is not None and title.text:
        result += f'{indent}  <title>{title.text.strip()}</title>\n'
    
    result += f'{indent}  <statement>\n'
    
    # Process problem/statement paragraphs
    problem = ex.find('.//{http://cnx.rice.edu/cnxml}problem')
    if problem is not None:
        for para in problem.findall('.//{http://cnx.rice.edu/cnxml}para'):
            result += process_para(para, namespaces, indent + '    ')
        for lst in problem.findall('.//{http://cnx.rice.edu/cnxml}list'):
            result += process_list(lst, namespaces, indent + '    ')
        for eq in problem.findall('.//{http://cnx.rice.edu/cnxml}equation'):
            result += process_equation(eq, namespaces, indent + '    ')
        for fig in problem.findall('.//{http://cnx.rice.edu/cnxml}figure'):
            result += process_figure(fig, namespaces, indent + '    ')
    else:
        # Process direct children of example (excluding solution)
        for child in ex:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag == 'para':
                result += process_para(child, namespaces, indent + '    ')
            elif tag == 'list':
                result += process_list(child, namespaces, indent + '    ')
            elif tag == 'equation':
                result += process_equation(child, namespaces, indent + '    ')
            elif tag == 'figure':
                result += process_figure(child, namespaces, indent + '    ')
            elif tag in ['solution', 'title']:
                # Skip these, handled separately
                pass
    
    result += f'{indent}  </statement>\n'
    
    # Solution
    solution = ex.find('.//{http://cnx.rice.edu/cnxml}solution')
    if solution is not None:
        result += f'{indent}  <solution>\n'
        for para in solution.findall('.//{http://cnx.rice.edu/cnxml}para'):
            result += process_para(para, namespaces, indent + '    ')
        for lst in solution.findall('.//{http://cnx.rice.edu/cnxml}list'):
            result += process_list(lst, namespaces, indent + '    ')
        for eq in solution.findall('.//{http://cnx.rice.edu/cnxml}equation'):
            result += process_equation(eq, namespaces, indent + '    ')
        for fig in solution.findall('.//{http://cnx.rice.edu/cnxml}figure'):
            result += process_figure(fig, namespaces, indent + '    ')
        result += f'{indent}  </solution>\n'
    
    result += f'{indent}</example>\n'
    return result

def process_note(note, namespaces, indent='    '):
    """Convert note elements"""
    note_class = note.get('class', '')
    note_id = note.get('id', '')
    
    # Determine PreTeXt element type
    if 'try' in note_class:
        tag = 'exercise'
        title = 'Try It'
    elif 'collab' in note_class:
        tag = 'activity'
        title = 'Collaborative Activity'
    elif 'lab' in note_class:
        tag = 'project'
        title = 'Lab'
    elif 'calculator' in note_class:
        tag = 'aside'
        title = 'Calculator'
    else:
        tag = 'note'
        title = ''
    
    result = f'{indent}<{tag}'
    if note_id:
        result += f' xml:id="{note_id}"'
    result += '>\n'
    
    # Title
    title_elem = note.find('.//{http://cnx.rice.edu/cnxml}title')
    if title_elem is not None and title_elem.text:
        result += f'{indent}  <title>{title_elem.text.strip()}</title>\n'
    elif title:
        result += f'{indent}  <title>{title}</title>\n'
    
    # Content
    if tag == 'exercise':
        result += f'{indent}  <statement>\n'
        for para in note.findall('.//{http://cnx.rice.edu/cnxml}para'):
            result += process_para(para, namespaces, indent + '    ')
        for lst in note.findall('.//{http://cnx.rice.edu/cnxml}list'):
            result += process_list(lst, namespaces, indent + '    ')
        result += f'{indent}  </statement>\n'
    else:
        for para in note.findall('.//{http://cnx.rice.edu/cnxml}para'):
            result += process_para(para, namespaces, indent + '  ')
        for lst in note.findall('.//{http://cnx.rice.edu/cnxml}list'):
            result += process_list(lst, namespaces, indent + '  ')
    
    result += f'{indent}</{tag}>\n'
    return result

def process_exercise(ex, namespaces, indent='    '):
    """Convert exercise (homework problem)"""
    ex_id = ex.get('id', '')
    ex_type = ex.get('element-type', '')
    
    result = f'{indent}<exercise'
    if ex_id:
        result += f' xml:id="{ex_id}"'
    result += '>\n'
    
    # Title  
    title = ex.find('.//{http://cnx.rice.edu/cnxml}title')
    if title is not None and title.text:
        result += f'{indent}  <title>{title.text.strip()}</title>\n'
    
    result += f'{indent}  <statement>\n'
    
    # Process problem
    problem = ex.find('.//{http://cnx.rice.edu/cnxml}problem')
    if problem is not None:
        for child in problem:
            tag = child.tag.split('}')[-1]
            if tag == 'para':
                result += process_para(child, namespaces, indent + '    ')
            elif tag == 'list':
                result += process_list(child, namespaces, indent + '    ')
            elif tag == 'equation':
                result += process_equation(child, namespaces, indent + '    ')
            elif tag == 'figure':
                result += process_figure(child, namespaces, indent + '    ')
    
    result += f'{indent}  </statement>\n'
    
    # Solution
    solution = ex.find('.//{http://cnx.rice.edu/cnxml}solution')
    if solution is not None:
        result += f'{indent}  <solution>\n'
        for child in solution:
            tag = child.tag.split('}')[-1]
            if tag == 'para':
                result += process_para(child, namespaces, indent + '    ')
            elif tag == 'list':
                result += process_list(child, namespaces, indent + '    ')
            elif tag == 'equation':
                result += process_equation(child, namespaces, indent + '    ')
            elif tag == 'figure':
                result += process_figure(child, namespaces, indent + '    ')
        result += f'{indent}  </solution>\n'
    
    result += f'{indent}</exercise>\n'
    return result

def process_element(elem, namespaces, indent='    '):
    """Process any element and return PreTeXt"""
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
    elif tag == 'title':
        # Skip titles, they're handled separately
        return ''
    else:
        return ''

def convert_module(filepath, section_id, section_title):
    """Convert a single CNXML module"""
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Find content element
    content = root.find('.//{http://cnx.rice.edu/cnxml}content')
    if content is None:
        return ""
    
    result = f'\n  <section xml:id="{section_id}">\n'
    result += f'    <title>{section_title}</title>\n\n'
    
    # Process all direct children of content
    for child in content:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        if tag == 'section':
            # Nested section becomes subsection
            section_id_nested = child.get('id', '')
            section_class = child.get('class', '')
            
            # Determine if this should be a special section
            title_elem = child.find('{http://cnx.rice.edu/cnxml}title')
            section_title_nested = title_elem.text.strip() if title_elem is not None and title_elem.text else ''
            
            # Don't skip ANY sections - convert them all
            result += f'\n    <subsection'
            if section_id_nested:
                result += f' xml:id="{section_id_nested}"'
            result += '>\n'
            if section_title_nested:
                result += f'      <title>{section_title_nested}</title>\n'
            
            # Process all children of section
            for subchild in child:
                result += process_element(subchild, CNXML_NS, '      ')
            
            result += '    </subsection>\n'
        else:
            # Direct child of content that's not a section
            result += process_element(child, CNXML_NS, '    ')
    
    result += '\n  </section>\n'
    
    return result

def main():
    """Main conversion"""
    modules_dir = Path('modules')
    
    # Read current file
    current = Path('pretext/source/ch06-normal-distribution.ptx').read_text()
    
    # Extract introduction (already done)
    intro_match = re.search(r'(<introduction>.*?</introduction>)', current, re.DOTALL)
    intro = intro_match.group(1) if intro_match else '<introduction/>'
    
    # Convert each section
    print("Converting m79641 (Standard Normal Distribution)...")
    section1 = convert_module(
        modules_dir / 'm79641' / 'index.cnxml',
        'sec-standard-normal-distribution',
        'The Standard Normal Distribution'
    )
    
    print("Converting m79643 (Using Normal Distribution)...")
    section2 = convert_module(
        modules_dir / 'm79643' / 'index.cnxml',
        'sec-using-normal-distribution',
        'Using the Normal Distribution'
    )
    
    print("Converting m79644 (Lab: Lap Times)...")
    section3 = convert_module(
        modules_dir / 'm79644' / 'index.cnxml',
        'sec-normal-distribution-lab-lap-times',
        'Lab: Lap Times'
    )
    
    print("Converting m79645 (Lab: Pinkie Length)...")
    section4 = convert_module(
        modules_dir / 'm79645' / 'index.cnxml',
        'sec-normal-distribution-lab-pinkie',
        'Lab: Pinkie Length'
    )
    
    # Assemble final document
    output = '<?xml version="1.0" encoding="UTF-8"?>\n'
    output += '<chapter xml:id="ch06-normal-distribution" xmlns:xi="http://www.w3.org/2001/XInclude">\n'
    output += '  <title>The Normal Distribution</title>\n\n'
    output += '  ' + intro + '\n'
    output += section1
    output += section2
    output += section3
    output += section4
    output += '</chapter>\n'
    
    # Write output
    output_path = Path('pretext/source/ch06-normal-distribution.ptx')
    output_path.write_text(output)
    
    print(f"\nConversion complete! Written to {output_path}")
    print(f"Total length: {len(output)} characters")

if __name__ == '__main__':
    main()
