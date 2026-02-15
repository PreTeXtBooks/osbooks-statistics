#!/usr/bin/env python3
"""
Create an actionable summary for adding missing glossary terms
"""

import xml.etree.ElementTree as ET
import re
from pathlib import Path
from collections import defaultdict

# Import the main analysis module
import sys
sys.path.insert(0, '/home/runner/work/osbooks-statistics/osbooks-statistics')

# Chapter to module mappings
CHAPTER_MODULES = {
    'ch03': ['m79611', 'm79612', 'm79614', 'm79616', 'm79617'],
    'ch04': ['m79620', 'm79621', 'm79623', 'm79624', 'm79625', 'm79626', 'm79627'],
    'ch06': ['m79641', 'm79643', 'm79644', 'm79645'],
    'ch09': ['m79660', 'm79661', 'm79662', 'm79663', 'm79664'],
    'ch10': ['m79668', 'm79669', 'm79670', 'm79672'],
    'ch11': ['m79673', 'm79674', 'm79675', 'm79676', 'm79678'],
    'ch12': ['m79686', 'm79689', 'm79691', 'm79692', 'm79694'],
    'ch13': ['m79701', 'm79703', 'm79704', 'm79705', 'm79706'],
}

PTX_FILES = {
    'ch03': 'pretext/source/ch03-probability-topics.ptx',
    'ch04': 'pretext/source/ch04-discrete-random-variables.ptx',
    'ch06': 'pretext/source/ch06-normal-distribution.ptx',
    'ch09': 'pretext/source/ch09-hypothesis-testing-one-sample.ptx',
    'ch10': 'pretext/source/ch10-hypothesis-testing-two-samples.ptx',
    'ch11': 'pretext/source/ch11-chi-square-distribution.ptx',
    'ch12': 'pretext/source/ch12-linear-regression-correlation.ptx',
    'ch13': 'pretext/source/ch13-f-distribution-anova.ptx',
}

def normalize_term(term):
    """Normalize term for comparison."""
    term = re.sub(r'\s*\([^)]*\)', '', term)
    term = term.lower().strip()
    term = re.sub(r'\s+', ' ', term)
    return term

def extract_cnxml_glossary(module_id):
    """Extract glossary terms and definitions from a CNXML module."""
    module_path = Path(f'modules/{module_id}/index.cnxml')
    
    if not module_path.exists():
        return {}
    
    try:
        tree = ET.parse(module_path)
        root = tree.getroot()
        
        ns = {'cnxml': 'http://cnx.rice.edu/cnxml'}
        glossary = {}
        
        for definition in root.findall('.//cnxml:glossary/cnxml:definition', ns):
            term_elem = definition.find('cnxml:term', ns)
            meaning_elem = definition.find('cnxml:meaning', ns)
            
            if term_elem is not None and meaning_elem is not None:
                term = term_elem.text or ''
                meaning = ''.join(meaning_elem.itertext()).strip()
                glossary[term.strip()] = meaning
        
        if not glossary:
            for definition in root.findall('.//glossary/definition'):
                term_elem = definition.find('term')
                meaning_elem = definition.find('meaning')
                
                if term_elem is not None and meaning_elem is not None:
                    term = term_elem.text or ''
                    meaning = ''.join(meaning_elem.itertext()).strip()
                    glossary[term.strip()] = meaning
        
        return glossary
    
    except Exception as e:
        return {}

def extract_ptx_glossary(ptx_file):
    """Extract glossary terms from a PreTeXt PTX file."""
    ptx_path = Path(ptx_file)
    
    if not ptx_path.exists():
        return []
    
    try:
        tree = ET.parse(ptx_path)
        root = tree.getroot()
        terms = []
        
        for gi in root.findall('.//gi'):
            title_elem = gi.find('title')
            if title_elem is not None and title_elem.text:
                terms.append(title_elem.text.strip())
        
        return terms
    
    except Exception:
        try:
            content = ptx_path.read_text()
            pattern = r'<gi[^>]*>\s*<title>([^<]+)</title>'
            matches = re.findall(pattern, content)
            return [m.strip() for m in matches]
        except Exception:
            return []

def find_missing_terms(cnxml_terms, ptx_terms):
    """Compare CNXML and PTX terms, finding missing ones."""
    ptx_normalized = {normalize_term(t): t for t in ptx_terms}
    
    missing = {}
    
    for term, definition in cnxml_terms.items():
        normalized = normalize_term(term)
        if normalized not in ptx_normalized:
            missing[term] = definition
    
    return missing

def main():
    """Generate actionable summary."""
    output = []
    output.append("=" * 80)
    output.append("ACTIONABLE SUMMARY - MISSING GLOSSARY TERMS TO ADD")
    output.append("=" * 80)
    output.append("")
    output.append("This file lists all missing glossary terms that need to be added to")
    output.append("PreTeXt files. Each chapter section shows:")
    output.append("  - The PTX file to edit")
    output.append("  - Terms to add with their definitions")
    output.append("")
    
    total_missing = 0
    
    for chapter in sorted(CHAPTER_MODULES.keys()):
        # Collect CNXML terms
        all_cnxml_terms = {}
        for module_id in CHAPTER_MODULES[chapter]:
            module_terms = extract_cnxml_glossary(module_id)
            all_cnxml_terms.update(module_terms)
        
        # Extract PTX terms
        ptx_file = PTX_FILES[chapter]
        ptx_terms = extract_ptx_glossary(ptx_file)
        
        # Find missing
        missing_terms = find_missing_terms(all_cnxml_terms, ptx_terms)
        
        if missing_terms:
            total_missing += len(missing_terms)
            output.append(f"\n{'=' * 80}")
            output.append(f"{chapter.upper()} - {len(missing_terms)} MISSING TERMS")
            output.append(f"{'=' * 80}")
            output.append(f"FILE: {ptx_file}")
            output.append("")
            output.append("TERMS TO ADD:")
            output.append("-" * 80)
            
            for i, (term, definition) in enumerate(sorted(missing_terms.items()), 1):
                # Clean definition for better readability
                definition_clean = ' '.join(definition.split())
                
                output.append(f"\n{i}. {term}")
                output.append(f"   {definition_clean}")
    
    output.append(f"\n\n{'=' * 80}")
    output.append(f"TOTAL MISSING: {total_missing} terms across all chapters")
    output.append(f"{'=' * 80}")
    
    # Save output
    output_file = Path('/tmp/glossary_action_items.txt')
    output_file.write_text('\n'.join(output))
    
    print(f"Actionable summary saved to: {output_file}")
    print('\n'.join(output))

if __name__ == '__main__':
    main()
