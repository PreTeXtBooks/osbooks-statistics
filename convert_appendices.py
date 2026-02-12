#!/usr/bin/env python3
"""
Convert CNXML appendix files to PreTeXt format
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

# Appendix mapping
APPENDICES = {
    'm79709': ('A', 'Review Exercises (Ch 3-13)', 'appendix-a-review-exercises'),
    'm79711': ('B', 'Practice Tests (1-4) and Final Exams', 'appendix-b-practice-tests'),
    'm79712': ('C', 'Data Sets', 'appendix-c-data-sets'),
    'm79713': ('D', 'Group and Partner Projects', 'appendix-d-group-projects'),
    'm79714': ('E', 'Solution Sheets', 'appendix-e-solution-sheets'),
    'm79715': ('F', 'Mathematical Phrases, Symbols, and Formulas', 'appendix-f-math-symbols'),
    'm79717': ('G', 'Notes for the TI-83, 83+, 84, 84+ Calculators', 'appendix-g-calculator-notes'),
    'm79718': ('H', 'Tables', 'appendix-h-tables'),
}

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
            '·': r'\cdot', '…': r'\ldots', '±': r'\pm', 'α': r'\alpha',
            'β': r'\beta', 'χ': r'\chi', 'Σ': r'\Sigma'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    result = []
    
    for child in elem:
        ctag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        ctext = (child.text or '').strip()
        
        if ctag == 'mi':  # Math identifier
            result.append(ctext if ctext else '')
        elif ctag == 'mn':  # Math number
            result.append(ctext if ctext else '')
        elif ctag == 'mo':  # Math operator
            ops = {'−': '-', '≤': r'\leq', '≥': r'\geq', '≈': r'\approx', 
                   '×': r'\times', '÷': r'\div', '∞': r'\infty'}
            result.append(ops.get(ctext, ctext) if ctext else '')
        elif ctag == 'msub':  # Subscript
            base_children = list(child)
            if len(base_children) >= 2:
                base = convert_mathml_to_latex(base_children[0], namespaces)
                sub = convert_mathml_to_latex(base_children[1], namespaces)
                result.append(f"{base}_{{{sub}}}")
        elif ctag == 'msup':  # Superscript
            base_children = list(child)
            if len(base_children) >= 2:
                base = convert_mathml_to_latex(base_children[0], namespaces)
                sup = convert_mathml_to_latex(base_children[1], namespaces)
                result.append(f"{base}^{{{sup}}}")
        elif ctag == 'mfrac':  # Fraction
            frac_children = list(child)
            if len(frac_children) >= 2:
                num = convert_mathml_to_latex(frac_children[0], namespaces)
                den = convert_mathml_to_latex(frac_children[1], namespaces)
                result.append(rf"\frac{{{num}}}{{{den}}}")
        elif ctag == 'mrow':  # Row/group
            result.append(convert_mathml_to_latex(child, namespaces))
        elif ctag == 'msqrt':  # Square root
            content = convert_mathml_to_latex(child, namespaces)
            result.append(rf"\sqrt{{{content}}}")
        elif ctag == 'mtext':  # Text in math
            result.append(rf"\text{{{ctext}}}" if ctext else '')
        else:
            # Fallback: process children
            result.append(convert_mathml_to_latex(child, namespaces))
        
        # Add tail text
        if child.tail:
            result.append(child.tail.strip())
    
    return ''.join(result)

def process_math(elem, namespaces):
    """Process math element"""
    display = elem.get('display', 'inline')
    
    # Find the MathML content
    math_elem = elem.find('.//m:math', namespaces)
    if math_elem is not None:
        latex = convert_mathml_to_latex(math_elem, namespaces)
        if display == 'block':
            return f"<me>{latex}</me>"
        else:
            return f"<m>{latex}</m>"
    return ""

def escape_xml(text):
    """Escape special XML characters"""
    if not text:
        return ""
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def process_emphasis(elem, namespaces):
    """Process emphasis elements"""
    effect = elem.get('effect', 'italics')
    text = ''.join(elem.itertext())
    
    if effect in ['bold', 'strong']:
        return f"<term>{escape_xml(text)}</term>"
    elif effect in ['italics', 'italic']:
        return f"<em>{escape_xml(text)}</em>"
    elif effect == 'underline':
        return f"<em>{escape_xml(text)}</em>"
    else:
        return f"<em>{escape_xml(text)}</em>"

def process_link(elem, namespaces):
    """Process link elements"""
    url = elem.get('url')
    document = elem.get('document')
    target_id = elem.get('target-id')
    text = ''.join(elem.itertext()).strip()
    
    if url:
        return f'<url href="{url}">{escape_xml(text)}</url>'
    elif document:
        if target_id:
            return f'<xref ref="{document}-{target_id}">{escape_xml(text)}</xref>'
        else:
            return f'<xref ref="{document}">{escape_xml(text)}</xref>'
    else:
        return escape_xml(text)

def process_image(elem, namespaces):
    """Process image elements"""
    src = elem.get('src', '')
    mime_type = elem.get('mime-type', '')
    width = elem.get('width', '')
    
    # Extract filename from path
    filename = src.split('/')[-1] if src else ''
    
    attrs = []
    if width:
        attrs.append(f'width="{width}%"')
    
    return f'<image source="../media/{filename}" {" ".join(attrs)}/>'

def process_list(elem, namespaces, indent=2):
    """Process list elements"""
    list_type = elem.get('list-type', 'bulleted')
    number_style = elem.get('number-style', 'arabic')
    
    indent_str = ' ' * indent
    
    if list_type == 'bulleted':
        lines = [f'{indent_str}<ul>']
    else:
        lines = [f'{indent_str}<ol>']
    
    for item in elem.findall('.//item', namespaces):
        lines.append(f'{indent_str}  <li>')
        item_content = process_para_content(item, namespaces, indent + 4)
        lines.append(f'{indent_str}    <p>')
        lines.append(f'{indent_str}      {item_content}')
        lines.append(f'{indent_str}    </p>')
        lines.append(f'{indent_str}  </li>')
    
    if list_type == 'bulleted':
        lines.append(f'{indent_str}</ul>')
    else:
        lines.append(f'{indent_str}</ol>')
    
    return '\n'.join(lines)

def process_para_content(elem, namespaces, indent=2):
    """Process paragraph content"""
    result = []
    
    # Get initial text
    if elem.text:
        result.append(escape_xml(elem.text.strip()))
    
    # Process child elements
    for child in elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        if tag == 'emphasis':
            result.append(process_emphasis(child, namespaces))
        elif tag == 'link':
            result.append(process_link(child, namespaces))
        elif tag == 'math':
            result.append(process_math(child, namespaces))
        elif tag == 'list':
            result.append('\n' + process_list(child, namespaces, indent))
        elif tag == 'image':
            result.append(process_image(child, namespaces))
        else:
            # Default: get text content
            result.append(escape_xml(''.join(child.itertext()).strip()))
        
        # Add tail text
        if child.tail:
            result.append(escape_xml(child.tail.strip()))
    
    return ' '.join(result)

def process_table(elem, namespaces, indent=2):
    """Process table elements"""
    indent_str = ' ' * indent
    lines = []
    
    # Get table title
    title_elem = elem.find('./title', namespaces)
    title = title_elem.text if title_elem is not None else ""
    
    # Get tgroup to determine number of columns
    tgroup = elem.find('./tgroup', namespaces)
    if tgroup is None:
        return ""
    
    cols = tgroup.get('cols', '1')
    
    lines.append(f'{indent_str}<table xml:id="table-{id(elem)}">')
    if title:
        lines.append(f'{indent_str}  <title>{escape_xml(title)}</title>')
    
    lines.append(f'{indent_str}  <tabular>')
    
    # Process thead
    thead = tgroup.find('./thead', namespaces)
    if thead is not None:
        for row in thead.findall('./row', namespaces):
            cells = []
            for entry in row.findall('./entry', namespaces):
                cell_text = ''.join(entry.itertext()).strip()
                cells.append(escape_xml(cell_text) if cell_text else '')
            lines.append(f'{indent_str}    <row header="yes">')
            for cell in cells:
                lines.append(f'{indent_str}      <cell>{cell}</cell>')
            lines.append(f'{indent_str}    </row>')
    
    # Process tbody
    tbody = tgroup.find('./tbody', namespaces)
    if tbody is not None:
        for row in tbody.findall('./row', namespaces):
            cells = []
            for entry in row.findall('./entry', namespaces):
                cell_text = ''.join(entry.itertext()).strip()
                cells.append(escape_xml(cell_text) if cell_text else '')
            lines.append(f'{indent_str}    <row>')
            for cell in cells:
                lines.append(f'{indent_str}      <cell>{cell}</cell>')
            lines.append(f'{indent_str}    </row>')
    
    lines.append(f'{indent_str}  </tabular>')
    lines.append(f'{indent_str}</table>')
    
    return '\n'.join(lines)

def convert_appendix(module_id):
    """Convert a single appendix module"""
    letter, title, xml_id = APPENDICES[module_id]
    
    print(f"Converting Appendix {letter}: {title} ({module_id})...")
    
    # Read the CNXML file
    cnxml_path = Path(f'modules/{module_id}/index.cnxml')
    if not cnxml_path.exists():
        print(f"  ERROR: File not found: {cnxml_path}")
        return None
    
    tree = ET.parse(cnxml_path)
    root = tree.getroot()
    
    # Start building PreTeXt content
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(f'<!-- Appendix {letter}: {title} -->')
    lines.append(f'<appendix xml:id="{xml_id}" xmlns:xi="http://www.w3.org/2001/XInclude">')
    lines.append(f'  <title>{title}</title>')
    lines.append('')
    
    # Get content element
    content = root.find('.//content', CNXML_NS)
    if content is None:
        print(f"  ERROR: No content element found")
        return None
    
    # Process content elements
    for child in content:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        if tag == 'para':
            para_text = process_para_content(child, CNXML_NS, 2)
            lines.append('  <p>')
            lines.append(f'    {para_text}')
            lines.append('  </p>')
            lines.append('')
        elif tag == 'section':
            section_title_elem = child.find('./title', CNXML_NS)
            section_title = section_title_elem.text if section_title_elem is not None else "Section"
            section_id = child.get('id', f'section-{id(child)}')
            
            lines.append(f'  <section xml:id="{section_id}">')
            lines.append(f'    <title>{escape_xml(section_title)}</title>')
            
            # Process section content
            for sec_child in child:
                sec_tag = sec_child.tag.split('}')[-1] if '}' in sec_child.tag else sec_child.tag
                
                if sec_tag == 'para':
                    para_text = process_para_content(sec_child, CNXML_NS, 4)
                    lines.append('    <p>')
                    lines.append(f'      {para_text}')
                    lines.append('    </p>')
                elif sec_tag == 'table':
                    lines.append(process_table(sec_child, CNXML_NS, 4))
                elif sec_tag == 'list':
                    lines.append(process_list(sec_child, CNXML_NS, 4))
            
            lines.append('  </section>')
            lines.append('')
        elif tag == 'table':
            lines.append(process_table(child, CNXML_NS, 2))
            lines.append('')
        elif tag == 'list':
            lines.append(process_list(child, CNXML_NS, 2))
            lines.append('')
        elif tag == 'note':
            note_title_elem = child.find('./title', CNXML_NS)
            note_title = note_title_elem.text if note_title_elem is not None else None
            
            lines.append('  <note>')
            if note_title:
                lines.append(f'    <title>{escape_xml(note_title)}</title>')
            
            for note_child in child:
                note_tag = note_child.tag.split('}')[-1] if '}' in note_child.tag else note_child.tag
                if note_tag == 'para':
                    para_text = process_para_content(note_child, CNXML_NS, 4)
                    lines.append('    <p>')
                    lines.append(f'      {para_text}')
                    lines.append('    </p>')
            
            lines.append('  </note>')
            lines.append('')
    
    lines.append('</appendix>')
    
    # Write the PreTeXt file
    output_path = Path(f'pretext/source/{xml_id}.ptx')
    output_path.write_text('\n'.join(lines))
    
    print(f"  Written to {output_path}")
    print(f"  Total length: {len(''.join(lines))} characters")
    return output_path

def main():
    """Convert all appendices"""
    print("Converting appendix modules to PreTeXt format...")
    print()
    
    for module_id in APPENDICES.keys():
        convert_appendix(module_id)
        print()
    
    print("Conversion complete!")

if __name__ == '__main__':
    main()
