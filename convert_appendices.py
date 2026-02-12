#!/usr/bin/env python3
"""
Convert CNXML appendix files to PreTeXt format - Enhanced version
Handles nested sections, all CNXML elements, and comprehensive content conversion
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
    """Convert MathML to LaTeX - Enhanced version"""
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
            'β': r'\beta', 'χ': r'\chi', 'Σ': r'\Sigma', 'λ': r'\lambda',
            'γ': r'\gamma', 'Δ': r'\Delta', 'δ': r'\delta', 'ε': r'\varepsilon',
            'ρ': r'\rho', 'ω': r'\omega', 'Ω': r'\Omega', '√': r'\sqrt',
            '∑': r'\sum', '∫': r'\int', '∂': r'\partial', '∈': r'\in',
            '∉': r'\notin', '∀': r'\forall', '∃': r'\exists', '⊂': r'\subset',
            '⊃': r'\supset', '⊆': r'\subseteq', '⊇': r'\supseteq', '∪': r'\cup',
            '∩': r'\cap', '∅': r'\emptyset', '∝': r'\propto', '↔': r'\leftrightarrow',
            '→': r'\rightarrow', '←': r'\leftarrow', '⇒': r'\Rightarrow',
            '⇐': r'\Leftarrow', '⇔': r'\Leftrightarrow', '¬': r'\neg',
            '∧': r'\wedge', '∨': r'\vee', '°': r'^\circ'
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
            ops = {
                '−': '-', '≤': r'\leq', '≥': r'\geq', '≈': r'\approx', 
                '×': r'\times', '÷': r'\div', '∞': r'\infty', '≠': r'\neq',
                '±': r'\pm', '∓': r'\mp', '·': r'\cdot', '∘': r'\circ',
                '∑': r'\sum', '∏': r'\prod', '∫': r'\int', '√': r'\sqrt',
                '∂': r'\partial', '∇': r'\nabla', '∆': r'\Delta',
                '⊕': r'\oplus', '⊗': r'\otimes'
            }
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
        elif ctag == 'msubsup':  # Subscript and superscript
            base_children = list(child)
            if len(base_children) >= 3:
                base = convert_mathml_to_latex(base_children[0], namespaces)
                sub = convert_mathml_to_latex(base_children[1], namespaces)
                sup = convert_mathml_to_latex(base_children[2], namespaces)
                result.append(f"{base}_{{{sub}}}^{{{sup}}}")
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
        elif ctag == 'mroot':  # nth root
            root_children = list(child)
            if len(root_children) >= 2:
                base = convert_mathml_to_latex(root_children[0], namespaces)
                index = convert_mathml_to_latex(root_children[1], namespaces)
                result.append(rf"\sqrt[{index}]{{{base}}}")
        elif ctag == 'mtext':  # Text in math
            result.append(rf"\text{{{ctext}}}" if ctext else '')
        elif ctag == 'mspace':  # Space in math
            result.append(r'\;')
        elif ctag == 'mfenced':  # Fenced expression (parentheses, brackets, etc.)
            open_fence = child.get('open', '(')
            close_fence = child.get('close', ')')
            fence_map = {
                '(': r'\left(', ')': r'\right)',
                '[': r'\left[', ']': r'\right]',
                '{': r'\left\{', '}': r'\right\}',
                '|': r'\left|'
            }
            content = convert_mathml_to_latex(child, namespaces)
            result.append(f"{fence_map.get(open_fence, open_fence)}{content}{fence_map.get(close_fence, close_fence)}")
        elif ctag == 'mtable':  # Matrix/table
            result.append(r'\begin{matrix}')
            for row in child:
                row_tag = row.tag.split('}')[-1] if '}' in row.tag else row.tag
                if row_tag == 'mtr':
                    cells = []
                    for cell in row:
                        cells.append(convert_mathml_to_latex(cell, namespaces))
                    result.append(' & '.join(cells) + r'\\')
            result.append(r'\end{matrix}')
        elif ctag == 'mover':  # Over (e.g., bar, hat)
            over_children = list(child)
            if len(over_children) >= 2:
                base = convert_mathml_to_latex(over_children[0], namespaces)
                accent = convert_mathml_to_latex(over_children[1], namespaces)
                if accent == '¯' or accent == '\u00af':
                    result.append(rf"\overline{{{base}}}")
                elif accent == '^':
                    result.append(rf"\hat{{{base}}}")
                elif accent == '~':
                    result.append(rf"\tilde{{{base}}}")
                else:
                    result.append(rf"\overset{{{accent}}}{{{base}}}")
        elif ctag == 'munder':  # Under
            under_children = list(child)
            if len(under_children) >= 2:
                base = convert_mathml_to_latex(under_children[0], namespaces)
                under = convert_mathml_to_latex(under_children[1], namespaces)
                result.append(rf"\underset{{{under}}}{{{base}}}")
        elif ctag == 'munderover':  # Under and over (e.g., summation with limits)
            uo_children = list(child)
            if len(uo_children) >= 3:
                base = convert_mathml_to_latex(uo_children[0], namespaces)
                under = convert_mathml_to_latex(uo_children[1], namespaces)
                over = convert_mathml_to_latex(uo_children[2], namespaces)
                result.append(rf"{base}_{{{under}}}^{{{over}}}")
        else:
            # Fallback: process children
            result.append(convert_mathml_to_latex(child, namespaces))
        
        # Add tail text
        if child.tail:
            tail_text = child.tail.strip()
            if tail_text:
                result.append(tail_text)
    
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
    # First unescape any already-escaped entities to avoid double-escaping
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', "'")
    
    # Now escape
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
    # Process mixed content
    text = process_mixed_content(elem, namespaces, inline=True)
    
    if effect in ['bold', 'strong']:
        return f"<term>{text}</term>"
    elif effect in ['italics', 'italic']:
        return f"<em>{text}</em>"
    elif effect == 'underline':
        return f"<em>{text}</em>"
    else:
        return f"<em>{text}</em>"

def process_link(elem, namespaces):
    """Process link elements"""
    url = elem.get('url')
    document = elem.get('document')
    target_id = elem.get('target-id')
    text = process_mixed_content(elem, namespaces, inline=True)
    
    if url:
        return f'<url href="{url}">{text}</url>'
    elif document:
        if target_id:
            return f'<xref ref="{document}-{target_id}">{text}</xref>'
        else:
            return f'<xref ref="{document}">{text}</xref>'
    elif target_id:
        return f'<xref ref="{target_id}">{text}</xref>'
    else:
        return text

def process_sub(elem, namespaces):
    """Process subscript elements"""
    text = process_mixed_content(elem, namespaces, inline=True)
    return f"<m>_{{{text}}}</m>"

def process_sup(elem, namespaces):
    """Process superscript elements"""
    text = process_mixed_content(elem, namespaces, inline=True)
    return f"<m>^{{{text}}}</m>"

def process_code(elem, namespaces):
    """Process code elements"""
    text = process_mixed_content(elem, namespaces, inline=True)
    return f"<c>{text}</c>"

def process_term(elem, namespaces):
    """Process term elements"""
    text = process_mixed_content(elem, namespaces, inline=True)
    return f"<term>{text}</term>"

def process_quote(elem, namespaces):
    """Process quote elements"""
    text = process_mixed_content(elem, namespaces, inline=True)
    return f'<q>{text}</q>'

def process_foreign(elem, namespaces):
    """Process foreign language elements"""
    text = process_mixed_content(elem, namespaces, inline=True)
    return f"<foreign>{text}</foreign>"

def process_image(elem, namespaces):
    """Process image elements"""
    src = elem.get('src', '')
    mime_type = elem.get('mime-type', '')
    width = elem.get('width', '')
    
    # Extract filename from path
    filename = src.split('/')[-1] if src else ''
    
    attrs = []
    if width:
        # Convert width to percentage if it's not already
        if '%' not in width:
            attrs.append(f'width="{width}%"')
        else:
            attrs.append(f'width="{width}"')
    
    attr_str = ' '.join(attrs)
    if attr_str:
        return f'<image source="../media/{filename}" {attr_str}/>'
    else:
        return f'<image source="../media/{filename}"/>'

def process_media(elem, namespaces):
    """Process media elements (can contain images)"""
    alt = elem.get('alt', '')
    display = elem.get('display', 'block')
    
    # Find image within media
    image_elem = elem.find('./image', namespaces)
    if image_elem is not None:
        return process_image(image_elem, namespaces)
    
    # If no image, return empty
    return ""

def process_figure(elem, namespaces, indent=2):
    """Process figure elements"""
    indent_str = ' ' * indent
    lines = []
    
    figure_id = elem.get('id', f'figure-{id(elem)}')
    
    # Get caption
    caption_elem = elem.find('./caption', namespaces)
    caption_text = ""
    if caption_elem is not None:
        caption_text = process_mixed_content(caption_elem, namespaces, inline=True)
    
    # Get title
    title_elem = elem.find('./title', namespaces)
    title_text = ""
    if title_elem is not None:
        title_text = escape_xml(title_elem.text or "")
    
    lines.append(f'{indent_str}<figure xml:id="{figure_id}">')
    
    if caption_text or title_text:
        lines.append(f'{indent_str}  <caption>{caption_text or title_text}</caption>')
    
    # Process media/image
    media_elem = elem.find('./media', namespaces)
    if media_elem is not None:
        image_markup = process_media(media_elem, namespaces)
        if image_markup:
            lines.append(f'{indent_str}  {image_markup}')
    
    # Process subfigures if any
    for subfig in elem.findall('./subfigure', namespaces):
        subfig_lines = process_figure(subfig, namespaces, indent + 2)
        lines.append(subfig_lines)
    
    lines.append(f'{indent_str}</figure>')
    
    return '\n'.join(lines)

def process_list(elem, namespaces, indent=2):
    """Process list elements"""
    list_type = elem.get('list-type', 'bulleted')
    number_style = elem.get('number-style', 'arabic')
    
    indent_str = ' ' * indent
    lines = []
    
    # Get list title if present
    title_elem = elem.find('./title', namespaces)
    title = ""
    if title_elem is not None:
        title = escape_xml(title_elem.text or "")
    
    if title:
        lines.append(f'{indent_str}<p><title>{title}</title></p>')
    
    if list_type == 'bulleted':
        lines.append(f'{indent_str}<ul>')
    else:
        # Handle enumerated lists with different markers
        marker_map = {
            'upper-alpha': 'A',
            'lower-alpha': 'a',
            'upper-roman': 'I',
            'lower-roman': 'i',
            'arabic': '1'
        }
        marker = marker_map.get(number_style, '1')
        if marker != '1':
            lines.append(f'{indent_str}<ol marker="{marker}">')
        else:
            lines.append(f'{indent_str}<ol>')
    
    for item in elem.findall('./item', namespaces):
        lines.append(f'{indent_str}  <li>')
        
        # Process all content within the item
        item_content = process_element_content(item, namespaces, indent + 4, skip_tags=['title'])
        
        if item_content.strip():
            lines.append(item_content)
        
        lines.append(f'{indent_str}  </li>')
    
    if list_type == 'bulleted':
        lines.append(f'{indent_str}</ul>')
    else:
        lines.append(f'{indent_str}</ol>')
    
    return '\n'.join(lines)

def process_mixed_content(elem, namespaces, inline=False):
    """
    Process mixed content (text and child elements) 
    inline=True returns inline content suitable for <p>, <em>, etc.
    inline=False returns block content
    """
    result = []
    
    # Get initial text
    if elem.text:
        text = elem.text.strip() if inline else elem.text
        if text:
            result.append(escape_xml(text))
    
    # Process child elements
    for child in elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        if tag == 'emphasis':
            result.append(process_emphasis(child, namespaces))
        elif tag == 'link':
            result.append(process_link(child, namespaces))
        elif tag == 'math':
            result.append(process_math(child, namespaces))
        elif tag == 'sub':
            result.append(process_sub(child, namespaces))
        elif tag == 'sup':
            result.append(process_sup(child, namespaces))
        elif tag == 'code':
            result.append(process_code(child, namespaces))
        elif tag == 'term':
            result.append(process_term(child, namespaces))
        elif tag == 'quote':
            result.append(process_quote(child, namespaces))
        elif tag == 'foreign':
            result.append(process_foreign(child, namespaces))
        elif tag == 'newline':
            if inline:
                result.append('\n')
            else:
                result.append('<br/>')
        elif tag == 'space':
            result.append(' ')
        elif tag == 'list':
            # Lists are block elements
            if inline:
                result.append('\n' + process_list(child, namespaces, 0))
            else:
                result.append(process_list(child, namespaces, 0))
        elif tag == 'media':
            result.append(process_media(child, namespaces))
        elif tag == 'image':
            result.append(process_image(child, namespaces))
        else:
            # Default: get all text content
            text = ''.join(child.itertext()).strip()
            if text:
                result.append(escape_xml(text))
        
        # Add tail text
        if child.tail:
            tail = child.tail.strip() if inline else child.tail
            if tail:
                result.append(escape_xml(tail))
    
    return ' '.join(result) if inline else ''.join(result)

def process_table(elem, namespaces, indent=2):
    """Process table elements"""
    indent_str = ' ' * indent
    lines = []
    
    # Get table title
    title_elem = elem.find('./title', namespaces)
    title = ""
    if title_elem is not None:
        title = process_mixed_content(title_elem, namespaces, inline=True)
    
    # Get caption
    caption_elem = elem.find('./caption', namespaces)
    caption = ""
    if caption_elem is not None:
        caption = process_mixed_content(caption_elem, namespaces, inline=True)
    
    # Get tgroup to determine number of columns
    tgroup = elem.find('./tgroup', namespaces)
    if tgroup is None:
        return ""
    
    cols = tgroup.get('cols', '1')
    table_id = elem.get('id', f'table-{id(elem)}')
    
    lines.append(f'{indent_str}<table xml:id="{table_id}">')
    
    # Use title or caption
    if title:
        lines.append(f'{indent_str}  <title>{title}</title>')
    elif caption:
        lines.append(f'{indent_str}  <title>{caption}</title>')
    
    lines.append(f'{indent_str}  <tabular>')
    
    # Process thead
    thead = tgroup.find('./thead', namespaces)
    if thead is not None:
        for row in thead.findall('./row', namespaces):
            cells = []
            for entry in row.findall('./entry', namespaces):
                cell_text = process_mixed_content(entry, namespaces, inline=True)
                cells.append(cell_text if cell_text else '')
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
                cell_text = process_mixed_content(entry, namespaces, inline=True)
                cells.append(cell_text if cell_text else '')
            lines.append(f'{indent_str}    <row>')
            for cell in cells:
                lines.append(f'{indent_str}      <cell>{cell}</cell>')
            lines.append(f'{indent_str}    </row>')
    
    lines.append(f'{indent_str}  </tabular>')
    lines.append(f'{indent_str}</table>')
    
    return '\n'.join(lines)

def process_note(elem, namespaces, indent=2):
    """Process note elements"""
    indent_str = ' ' * indent
    lines = []
    
    note_type = elem.get('type', 'note')
    note_id = elem.get('id', f'note-{id(elem)}')
    
    # Get title
    title_elem = elem.find('./title', namespaces)
    title = ""
    if title_elem is not None:
        title = escape_xml(title_elem.text or "")
    
    # Get label
    label_elem = elem.find('./label', namespaces)
    label = ""
    if label_elem is not None:
        label = escape_xml(label_elem.text or "")
    
    lines.append(f'{indent_str}<note xml:id="{note_id}">')
    
    if title:
        lines.append(f'{indent_str}  <title>{title}</title>')
    elif label:
        lines.append(f'{indent_str}  <title>{label}</title>')
    
    # Process note content
    content_lines = process_element_content(elem, namespaces, indent + 2, skip_tags=['title', 'label'])
    if content_lines.strip():
        lines.append(content_lines)
    
    lines.append(f'{indent_str}</note>')
    
    return '\n'.join(lines)

def process_exercise(elem, namespaces, indent=2):
    """Process exercise elements"""
    indent_str = ' ' * indent
    lines = []
    
    exercise_id = elem.get('id', f'exercise-{id(elem)}')
    
    lines.append(f'{indent_str}<exercise xml:id="{exercise_id}">')
    
    # Process problem
    problem_elem = elem.find('./problem', namespaces)
    if problem_elem is not None:
        lines.append(f'{indent_str}  <statement>')
        problem_content = process_element_content(problem_elem, namespaces, indent + 4)
        if problem_content.strip():
            lines.append(problem_content)
        lines.append(f'{indent_str}  </statement>')
    
    # Process solution
    solution_elem = elem.find('./solution', namespaces)
    if solution_elem is not None:
        lines.append(f'{indent_str}  <solution>')
        solution_content = process_element_content(solution_elem, namespaces, indent + 4)
        if solution_content.strip():
            lines.append(solution_content)
        lines.append(f'{indent_str}  </solution>')
    
    lines.append(f'{indent_str}</exercise>')
    
    return '\n'.join(lines)

def process_element_content(elem, namespaces, indent=2, skip_tags=None):
    """
    Process all content within an element, creating appropriate block structures
    skip_tags: list of tag names to skip (e.g., ['title', 'label'])
    """
    if skip_tags is None:
        skip_tags = []
    
    indent_str = ' ' * indent
    lines = []
    
    # Check if element has direct text (before any children)
    has_direct_text = elem.text and elem.text.strip()
    
    # Check if element only contains inline elements (link, emphasis, math, etc.)
    children = [c for c in elem if c.tag.split('}')[-1] not in skip_tags]
    is_all_inline = all(
        child.tag.split('}')[-1] in ['link', 'emphasis', 'math', 'sub', 'sup', 'code', 'term', 'quote', 'foreign', 'newline', 'space', 'media', 'image']
        for child in children
    )
    
    # If we have only inline content or direct text, wrap in a paragraph
    if (has_direct_text or is_all_inline) and len(children) > 0:
        para_content = process_mixed_content(elem, namespaces, inline=True)
        if para_content.strip():
            lines.append(f'{indent_str}<p>')
            lines.append(f'{indent_str}  {para_content}')
            lines.append(f'{indent_str}</p>')
        return '\n'.join(lines)
    
    # If we only have direct text with no children
    if has_direct_text and len(children) == 0:
        lines.append(f'{indent_str}<p>')
        lines.append(f'{indent_str}  {escape_xml(elem.text.strip())}')
        lines.append(f'{indent_str}</p>')
        return '\n'.join(lines)
    
    # Otherwise, process block-level content
    if has_direct_text:
        lines.append(f'{indent_str}<p>')
        lines.append(f'{indent_str}  {escape_xml(elem.text.strip())}')
        lines.append(f'{indent_str}</p>')
    
    # Process child elements
    for child in elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        # Skip specified tags
        if tag in skip_tags:
            continue
        
        if tag == 'para':
            para_content = process_mixed_content(child, namespaces, inline=True)
            if para_content.strip():
                # Check for title within para
                title_elem = child.find('./title', namespaces)
                if title_elem is not None:
                    title_text = escape_xml(title_elem.text or "")
                    lines.append(f'{indent_str}<p>')
                    lines.append(f'{indent_str}  <title>{title_text}</title>')
                    # Get remaining content after title
                    remaining = []
                    if title_elem.tail:
                        remaining.append(escape_xml(title_elem.tail.strip()))
                    for elem_after in list(child)[list(child).index(title_elem) + 1:]:
                        remaining.append(process_mixed_content(elem_after, namespaces, inline=True))
                    if remaining:
                        lines.append(f'{indent_str}  {" ".join(remaining)}')
                    lines.append(f'{indent_str}</p>')
                else:
                    lines.append(f'{indent_str}<p>')
                    lines.append(f'{indent_str}  {para_content}')
                    lines.append(f'{indent_str}</p>')
        elif tag == 'section':
            section_lines = process_section(child, namespaces, indent)
            lines.append(section_lines)
        elif tag == 'list':
            lines.append(process_list(child, namespaces, indent))
        elif tag == 'table':
            lines.append(process_table(child, namespaces, indent))
        elif tag == 'figure':
            lines.append(process_figure(child, namespaces, indent))
        elif tag == 'note':
            lines.append(process_note(child, namespaces, indent))
        elif tag == 'exercise':
            lines.append(process_exercise(child, namespaces, indent))
        elif tag == 'media':
            media_markup = process_media(child, namespaces)
            if media_markup:
                lines.append(f'{indent_str}<p>')
                lines.append(f'{indent_str}  {media_markup}')
                lines.append(f'{indent_str}</p>')
        elif tag == 'equation':
            # Process display equation
            math_elem = child.find('.//m:math', namespaces)
            if math_elem is not None:
                latex = convert_mathml_to_latex(math_elem, namespaces)
                lines.append(f'{indent_str}<me>{latex}</me>')
        elif tag == 'code' and child.get('display') == 'block':
            # Block code
            code_text = ''.join(child.itertext())
            lines.append(f'{indent_str}<pre>')
            lines.append(escape_xml(code_text))
            lines.append(f'{indent_str}</pre>')
        elif tag == 'preformat':
            # Preformatted text
            pre_text = ''.join(child.itertext())
            lines.append(f'{indent_str}<pre>')
            lines.append(escape_xml(pre_text))
            lines.append(f'{indent_str}</pre>')
        
        # Handle tail text after the element
        if child.tail and child.tail.strip():
            lines.append(f'{indent_str}<p>')
            lines.append(f'{indent_str}  {escape_xml(child.tail.strip())}')
            lines.append(f'{indent_str}</p>')
    
    return '\n'.join(lines)

def process_section(elem, namespaces, indent=2, depth=0):
    """
    Recursively process section elements, including nested subsections
    depth: current depth level (0 = section, 1 = subsection, etc.)
    """
    indent_str = ' ' * indent
    lines = []
    
    # Get section attributes
    section_id = elem.get('id', f'section-{id(elem)}')
    
    # Get title
    title_elem = elem.find('./title', namespaces)
    title = ""
    if title_elem is not None:
        title = escape_xml(title_elem.text or "")
    
    # Determine if this should be a section or subsection
    if depth == 0:
        lines.append(f'{indent_str}<section xml:id="{section_id}">')
    else:
        lines.append(f'{indent_str}<subsection xml:id="{section_id}">')
    
    if title:
        lines.append(f'{indent_str}  <title>{title}</title>')
    
    # Process all content within the section
    for child in elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        
        # Skip title as we've already processed it
        if tag == 'title':
            continue
        
        if tag == 'section':
            # Recursively process nested sections as subsections
            subsection_lines = process_section(child, namespaces, indent + 2, depth + 1)
            lines.append(subsection_lines)
        elif tag == 'para':
            para_content = process_mixed_content(child, namespaces, inline=True)
            if para_content.strip():
                # Check for title within para
                para_title_elem = child.find('./title', namespaces)
                if para_title_elem is not None:
                    para_title = escape_xml(para_title_elem.text or "")
                    lines.append(f'{indent_str}  <p>')
                    lines.append(f'{indent_str}    <title>{para_title}</title>')
                    # Get content after title
                    remaining_content = []
                    if para_title_elem.tail:
                        remaining_content.append(escape_xml(para_title_elem.tail.strip()))
                    # Process remaining children after title
                    found_title = False
                    for para_child in child:
                        if para_child == para_title_elem:
                            found_title = True
                            continue
                        if found_title:
                            remaining_content.append(process_mixed_content(para_child, namespaces, inline=True))
                    if remaining_content:
                        lines.append(f'{indent_str}    {" ".join(remaining_content)}')
                    lines.append(f'{indent_str}  </p>')
                else:
                    lines.append(f'{indent_str}  <p>')
                    lines.append(f'{indent_str}    {para_content}')
                    lines.append(f'{indent_str}  </p>')
        elif tag == 'list':
            lines.append(process_list(child, namespaces, indent + 2))
        elif tag == 'table':
            lines.append(process_table(child, namespaces, indent + 2))
        elif tag == 'figure':
            lines.append(process_figure(child, namespaces, indent + 2))
        elif tag == 'note':
            lines.append(process_note(child, namespaces, indent + 2))
        elif tag == 'exercise':
            lines.append(process_exercise(child, namespaces, indent + 2))
        elif tag == 'media':
            media_markup = process_media(child, namespaces)
            if media_markup:
                lines.append(f'{indent_str}  <p>')
                lines.append(f'{indent_str}    {media_markup}')
                lines.append(f'{indent_str}  </p>')
        elif tag == 'equation':
            math_elem = child.find('.//m:math', namespaces)
            if math_elem is not None:
                latex = convert_mathml_to_latex(math_elem, namespaces)
                lines.append(f'{indent_str}  <me>{latex}</me>')
        elif tag == 'code' and child.get('display') == 'block':
            code_text = ''.join(child.itertext())
            lines.append(f'{indent_str}  <pre>')
            lines.append(f'{indent_str}    {escape_xml(code_text)}')
            lines.append(f'{indent_str}  </pre>')
        elif tag == 'preformat':
            pre_text = ''.join(child.itertext())
            lines.append(f'{indent_str}  <pre>')
            lines.append(f'{indent_str}    {escape_xml(pre_text)}')
            lines.append(f'{indent_str}  </pre>')
    
    if depth == 0:
        lines.append(f'{indent_str}</section>')
    else:
        lines.append(f'{indent_str}</subsection>')
    
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
            para_content = process_mixed_content(child, CNXML_NS, inline=True)
            if para_content.strip():
                lines.append('  <p>')
                lines.append(f'    {para_content}')
                lines.append('  </p>')
                lines.append('')
        elif tag == 'section':
            section_lines = process_section(child, CNXML_NS, 2, depth=0)
            lines.append(section_lines)
            lines.append('')
        elif tag == 'table':
            lines.append(process_table(child, CNXML_NS, 2))
            lines.append('')
        elif tag == 'list':
            lines.append(process_list(child, CNXML_NS, 2))
            lines.append('')
        elif tag == 'note':
            lines.append(process_note(child, CNXML_NS, 2))
            lines.append('')
        elif tag == 'exercise':
            lines.append(process_exercise(child, CNXML_NS, 2))
            lines.append('')
        elif tag == 'figure':
            lines.append(process_figure(child, CNXML_NS, 2))
            lines.append('')
        elif tag == 'media':
            media_markup = process_media(child, CNXML_NS)
            if media_markup:
                lines.append('  <p>')
                lines.append(f'    {media_markup}')
                lines.append('  </p>')
                lines.append('')
        elif tag == 'equation':
            math_elem = child.find('.//m:math', CNXML_NS)
            if math_elem is not None:
                latex = convert_mathml_to_latex(math_elem, CNXML_NS)
                lines.append(f'  <me>{latex}</me>')
                lines.append('')
    
    lines.append('</appendix>')
    
    # Write the PreTeXt file
    output_path = Path(f'pretext/source/{xml_id}.ptx')
    output_path.write_text('\n'.join(lines))
    
    print(f"  Written to {output_path}")
    print(f"  Total length: {len(''.join(lines))} characters")
    
    # Count various elements for verification
    section_count = len(root.findall('.//section', CNXML_NS))
    para_count = len(root.findall('.//para', CNXML_NS))
    table_count = len(root.findall('.//table', CNXML_NS))
    print(f"  Elements found: {section_count} sections, {para_count} paragraphs, {table_count} tables")
    
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
