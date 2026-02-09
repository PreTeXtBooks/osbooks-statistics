#!/usr/bin/env python3
"""
Complete conversion of Chapter 9 CNXML files to PreTeXt format
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
    # Check if para contains a table
    table = para.find('.//{http://cnx.rice.edu/cnxml}table')
    if table is not None:
        # Para contains a table, handle separately
        result = ''
        # Extract text before the table (including inline markup)
        text_parts = []
        if para.text:
            text_parts.append(para.text)
        
        # Process any elements before the table
        for child in para:
            if child == table:
                break
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag == 'emphasis':
                effect = child.get('effect', '')
                content = extract_text(child, namespaces)
                if effect == 'italics':
                    if len(content.strip()) <= 2:
                        text_parts.append(f'<m>{content}</m>')
                    else:
                        text_parts.append(f'<em>{content}</em>')
                elif effect == 'bold':
                    text_parts.append(f'<alert>{content}</alert>')
                else:
                    text_parts.append(content)
            else:
                text_parts.append(extract_text(child, namespaces))
            
            if child.tail:
                text_parts.append(child.tail)
        
        text_before = ''.join(text_parts).strip()
        if text_before:
            result += f'{indent}<p>{text_before}</p>\n'
        
        # Process the table
        result += process_table(table, namespaces, indent)
        
        # Process text after the table (tail of table element)
        if table.tail and table.tail.strip():
            result += f'{indent}<p>{xml_escape(table.tail.strip())}</p>\n'
        return result
    
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

def process_table(table_elem, namespaces, indent='    '):
    """Convert table element"""
    table_id = table_elem.get('id', '')
    summary = table_elem.get('summary', '')
    
    result = f'{indent}<table'
    if table_id:
        result += f' xml:id="{table_id}"'
    result += '>\n'
    
    # Caption if present
    caption = table_elem.find('.//{http://cnx.rice.edu/cnxml}caption')
    if caption is not None:
        cap_text = extract_text(caption, namespaces).strip()
        if cap_text:
            result += f'{indent}  <caption>{cap_text}</caption>\n'
    
    # Process tgroup
    tgroup = table_elem.find('.//{http://cnx.rice.edu/cnxml}tgroup')
    if tgroup is not None:
        # Get column count
        cols = tgroup.get('cols', '2')
        
        result += f'{indent}  <tabular>\n'
        
        # Process thead
        thead = tgroup.find('.//{http://cnx.rice.edu/cnxml}thead')
        if thead is not None:
            for row in thead.findall('.//{http://cnx.rice.edu/cnxml}row'):
                entries = row.findall('.//{http://cnx.rice.edu/cnxml}entry')
                row_parts = []
                for entry in entries:
                    entry_text = extract_text(entry, namespaces).strip()
                    row_parts.append(f'<cell>{entry_text}</cell>')
                result += f'{indent}    <row>' + ''.join(row_parts) + '</row>\n'
        
        # Process tbody
        tbody = tgroup.find('.//{http://cnx.rice.edu/cnxml}tbody')
        if tbody is not None:
            for row in tbody.findall('.//{http://cnx.rice.edu/cnxml}row'):
                entries = row.findall('.//{http://cnx.rice.edu/cnxml}entry')
                row_parts = []
                for entry in entries:
                    entry_text = extract_text(entry, namespaces).strip()
                    row_parts.append(f'<cell>{entry_text}</cell>')
                result += f'{indent}    <row>' + ''.join(row_parts) + '</row>\n'
        
        result += f'{indent}  </tabular>\n'
    
    result += f'{indent}</table>\n'
    return result

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

def process_note(note, namespaces, indent='    '):
    """Convert note element"""
    note_id = note.get('id', '')
    note_class = note.get('class', '')
    
    # Determine note type
    if note_class == 'statistics try':
        # This is a "Try It" exercise, will be handled differently
        return ''
    
    result = f'{indent}<note'
    if note_id:
        result += f' xml:id="{note_id}"'
    result += '>\n'
    
    # Title
    title = note.find('.//{http://cnx.rice.edu/cnxml}title')
    if title is not None and title.text:
        result += f'{indent}  <title>{title.text.strip()}</title>\n'
    
    # Process content
    for child in note:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'para':
            result += process_para(child, namespaces, indent + '  ')
        elif tag == 'list':
            result += process_list(child, namespaces, indent + '  ')
        elif tag == 'title' or tag == 'label':
            # Already handled
            pass
    
    result += f'{indent}</note>\n'
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

def process_exercise(ex, namespaces, indent='    '):
    """Convert exercise (Try It)"""
    ex_id = ex.get('id', '')
    
    result = f'{indent}<exercise'
    if ex_id:
        result += f' xml:id="{ex_id}"'
    result += '>\n'
    
    # Title
    title = ex.find('.//{http://cnx.rice.edu/cnxml}title')
    if title is not None and title.text:
        result += f'{indent}  <title>{title.text.strip()}</title>\n'
    
    # Problem
    problem = ex.find('.//{http://cnx.rice.edu/cnxml}problem')
    if problem is not None:
        result += f'{indent}  <statement>\n'
        for para in problem.findall('.//{http://cnx.rice.edu/cnxml}para'):
            result += process_para(para, namespaces, indent + '    ')
        for lst in problem.findall('.//{http://cnx.rice.edu/cnxml}list'):
            result += process_list(lst, namespaces, indent + '    ')
        for eq in problem.findall('.//{http://cnx.rice.edu/cnxml}equation'):
            result += process_equation(eq, namespaces, indent + '    ')
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
    elif tag == 'table':
        return process_table(elem, namespaces, indent)
    elif tag == 'figure':
        return process_figure(elem, namespaces, indent)
    elif tag == 'example':
        return process_example(elem, namespaces, indent)
    elif tag == 'note':
        note_class = elem.get('class', '')
        if note_class == 'statistics try':
            # Process as exercises
            exercises = elem.findall('.//{http://cnx.rice.edu/cnxml}exercise')
            result = ''
            for exercise in exercises:
                result += process_exercise(exercise, namespaces, indent)
            return result
        else:
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

def convert_introduction():
    """Convert the introduction module (m79660)"""
    modules_dir = Path('modules')
    tree = ET.parse(modules_dir / 'm79660' / 'index.cnxml')
    root = tree.getroot()
    
    content = root.find('.//{http://cnx.rice.edu/cnxml}content')
    if content is None:
        return '<introduction/>'
    
    result = '  <introduction>\n'
    
    # Process all children of content
    for child in content:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        if tag == 'figure':
            result += process_figure(child, CNXML_NS, '    ')
        elif tag == 'note':
            note_class = child.get('class', '')
            if note_class == 'chapter-objectives':
                note_id = child.get('id', '')
                result += f'    <objectives'
                if note_id:
                    result += f' xml:id="{note_id}"'
                result += '>\n'
                
                title = child.find('.//{http://cnx.rice.edu/cnxml}title')
                if title is not None and title.text:
                    result += f'      <title>{title.text.strip()}</title>\n'
                
                # Find the intro para and list
                for subchild in child:
                    subtag = subchild.tag.split('}')[-1] if '}' in subchild.tag else subchild.tag
                    if subtag == 'para':
                        result += process_para(subchild, CNXML_NS, '      ')
                    elif subtag == 'list':
                        result += process_list(subchild, CNXML_NS, '      ')
                
                result += '    </objectives>\n'
            else:
                result += process_note(child, CNXML_NS, '    ')
        elif tag == 'para':
            result += process_para(child, CNXML_NS, '    ')
        elif tag == 'list':
            result += process_list(child, CNXML_NS, '    ')
    
    result += '  </introduction>\n'
    
    return result

def main():
    """Main conversion"""
    modules_dir = Path('modules')
    
    # Convert introduction (m79660)
    print("Converting m79660 (Introduction)...")
    intro = convert_introduction()
    
    # Convert each section
    print("Converting m79661 (Null and Alternative Hypotheses)...")
    section1 = convert_module(
        modules_dir / 'm79661' / 'index.cnxml',
        'sec-null-alternative-hypotheses',
        'Null and Alternative Hypotheses'
    )
    
    print("Converting m79662 (Outcomes and Type Errors)...")
    section2 = convert_module(
        modules_dir / 'm79662' / 'index.cnxml',
        'sec-outcomes-type-errors',
        'Outcomes and the Type I and Type II Errors'
    )
    
    print("Converting m79663 (Distribution for Hypothesis Testing)...")
    section3 = convert_module(
        modules_dir / 'm79663' / 'index.cnxml',
        'sec-distribution-test-statistics',
        'Distribution Needed for Hypothesis Testing'
    )
    
    print("Converting m79664 (Rare Events)...")
    section4 = convert_module(
        modules_dir / 'm79664' / 'index.cnxml',
        'sec-rare-events',
        'Rare Events, the Sample, Decision and Conclusion'
    )
    
    print("Converting m79665 (Additional Information)...")
    section5 = convert_module(
        modules_dir / 'm79665' / 'index.cnxml',
        'sec-additional-information-one-sample',
        'Additional Information and Full Hypothesis Test Examples'
    )
    
    print("Converting m79666 (Review)...")
    section6 = convert_module(
        modules_dir / 'm79666' / 'index.cnxml',
        'sec-hypothesis-testing-review',
        'Hypothesis Testing with One Sample: Review'
    )
    
    print("Converting m79667 (Practice)...")
    section7 = convert_module(
        modules_dir / 'm79667' / 'index.cnxml',
        'sec-hypothesis-testing-practice',
        'Hypothesis Testing with One Sample: Practice'
    )
    
    # Assemble final document
    output = '<?xml version="1.0" encoding="UTF-8"?>\n'
    output += '<chapter xml:id="ch09-hypothesis-testing-one-sample" xmlns:xi="http://www.w3.org/2001/XInclude">\n'
    output += '  <title>Hypothesis Testing with One Sample</title>\n\n'
    output += intro
    output += section1
    output += section2
    output += section3
    output += section4
    output += section5
    output += section6
    output += section7
    output += '</chapter>\n'
    
    # Write output
    output_path = Path('pretext/source/ch09-hypothesis-testing-one-sample.ptx')
    output_path.write_text(output)
    
    print(f"\nConversion complete! Written to {output_path}")
    print(f"Total length: {len(output)} characters")

if __name__ == '__main__':
    main()
