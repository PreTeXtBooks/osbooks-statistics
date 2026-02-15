#!/usr/bin/env python3
"""
Comprehensive Glossary Analysis Script
Compares CNXML and PreTeXt glossary terms across all chapters
"""

import xml.etree.ElementTree as ET
import re
from pathlib import Path
from collections import defaultdict

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

# PTX file mappings
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
    """
    Normalize term for comparison:
    - Convert to lowercase
    - Remove parenthetical abbreviations like (IQR)
    - Strip whitespace
    - Remove special characters
    """
    # Remove parenthetical abbreviations
    term = re.sub(r'\s*\([^)]*\)', '', term)
    # Convert to lowercase and strip
    term = term.lower().strip()
    # Remove extra whitespace
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
        
        # Handle XML namespaces
        ns = {'cnxml': 'http://cnx.rice.edu/cnxml'}
        
        glossary = {}
        
        # Find all definition elements in glossary
        for definition in root.findall('.//cnxml:glossary/cnxml:definition', ns):
            term_elem = definition.find('cnxml:term', ns)
            meaning_elem = definition.find('cnxml:meaning', ns)
            
            if term_elem is not None and meaning_elem is not None:
                term = term_elem.text or ''
                # Get all text content from meaning element
                meaning = ''.join(meaning_elem.itertext()).strip()
                glossary[term.strip()] = meaning
        
        # Also try without namespace if not found
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
        print(f"Error parsing {module_path}: {e}")
        return {}


def extract_ptx_glossary(ptx_file):
    """Extract glossary terms from a PreTeXt PTX file."""
    ptx_path = Path(ptx_file)
    
    if not ptx_path.exists():
        return []
    
    # Try XML parsing first
    try:
        tree = ET.parse(ptx_path)
        root = tree.getroot()
        
        terms = []
        
        # Find all <gi> elements (glossary items)
        for gi in root.findall('.//gi'):
            title_elem = gi.find('title')
            if title_elem is not None and title_elem.text:
                terms.append(title_elem.text.strip())
        
        return terms
    
    except Exception as e:
        print(f"Warning: XML parsing failed for {ptx_path}: {e}")
        print(f"Attempting regex-based extraction...")
        
        # Fallback to regex-based extraction
        try:
            content = ptx_path.read_text()
            # Extract titles from <gi> elements using regex
            import re
            pattern = r'<gi[^>]*>\s*<title>([^<]+)</title>'
            matches = re.findall(pattern, content)
            return [m.strip() for m in matches]
        except Exception as e2:
            print(f"Error with regex extraction: {e2}")
            return []


def find_missing_terms(cnxml_terms, ptx_terms):
    """
    Compare CNXML and PTX terms, finding missing ones.
    Returns a dict of {original_term: definition} for missing terms.
    """
    # Normalize PTX terms for comparison
    ptx_normalized = {normalize_term(t): t for t in ptx_terms}
    
    missing = {}
    
    for term, definition in cnxml_terms.items():
        normalized = normalize_term(term)
        if normalized not in ptx_normalized:
            missing[term] = definition
    
    return missing


def analyze_chapter(chapter):
    """Analyze a single chapter for missing glossary terms."""
    print(f"\nAnalyzing {chapter}...")
    
    # Collect all CNXML glossary terms for this chapter
    all_cnxml_terms = {}
    modules = CHAPTER_MODULES[chapter]
    
    for module_id in modules:
        module_terms = extract_cnxml_glossary(module_id)
        all_cnxml_terms.update(module_terms)
    
    # Extract PTX glossary terms
    ptx_file = PTX_FILES[chapter]
    ptx_terms = extract_ptx_glossary(ptx_file)
    
    # Find missing terms
    missing_terms = find_missing_terms(all_cnxml_terms, ptx_terms)
    
    return {
        'cnxml_count': len(all_cnxml_terms),
        'ptx_count': len(ptx_terms),
        'missing_terms': missing_terms,
        'all_cnxml_terms': all_cnxml_terms,
        'ptx_terms': ptx_terms
    }


def format_output(results):
    """Format the analysis results for output."""
    output = []
    output.append("=" * 80)
    output.append("COMPREHENSIVE GLOSSARY ANALYSIS - ALL CHAPTERS")
    output.append("=" * 80)
    output.append("")
    
    total_cnxml = 0
    total_ptx = 0
    total_missing = 0
    
    for chapter in sorted(results.keys()):
        data = results[chapter]
        total_cnxml += data['cnxml_count']
        total_ptx += data['ptx_count']
        total_missing += len(data['missing_terms'])
        
        output.append(f"\n{'=' * 80}")
        output.append(f"CHAPTER: {chapter.upper()}")
        output.append(f"{'=' * 80}")
        output.append(f"CNXML Terms: {data['cnxml_count']}")
        output.append(f"PreTeXt Terms: {data['ptx_count']}")
        output.append(f"Missing Terms: {len(data['missing_terms'])}")
        output.append("")
        
        if data['missing_terms']:
            output.append(f"MISSING TERMS ({len(data['missing_terms'])} total):")
            output.append("-" * 80)
            
            for i, (term, definition) in enumerate(sorted(data['missing_terms'].items()), 1):
                output.append(f"\n{i}. TERM: {term}")
                output.append(f"   DEFINITION: {definition}")
        else:
            output.append("✓ No missing terms - all CNXML terms are in PreTeXt!")
        
        output.append("")
    
    # Summary
    output.append(f"\n{'=' * 80}")
    output.append("SUMMARY")
    output.append(f"{'=' * 80}")
    output.append(f"Total CNXML terms across all chapters: {total_cnxml}")
    output.append(f"Total PreTeXt terms across all chapters: {total_ptx}")
    output.append(f"Total missing terms: {total_missing}")
    output.append(f"Coverage: {((total_cnxml - total_missing) / total_cnxml * 100):.1f}%")
    output.append("")
    
    return "\n".join(output)


def main():
    """Main analysis function."""
    results = {}
    
    for chapter in sorted(CHAPTER_MODULES.keys()):
        results[chapter] = analyze_chapter(chapter)
    
    # Format and save output
    output = format_output(results)
    
    output_file = Path('/tmp/glossary_audit.txt')
    output_file.write_text(output)
    
    print(f"\n{'=' * 80}")
    print(f"Analysis complete! Results saved to: {output_file}")
    print(f"{'=' * 80}")
    
    # Also print to console
    print(output)


if __name__ == '__main__':
    main()
