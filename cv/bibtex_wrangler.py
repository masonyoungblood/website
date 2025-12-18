import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
import yaml
import re
import argparse
import sys
from pathlib import Path

def bibtex_to_rendercv_yaml(bibtex_source, my_name="Mason Youngblood"):
    """
    Splits BibTeX into sections based on comments starting with '#',
    counts entries per section, and outputs grouped YAML.
    """
    
    # 1. READ RAW CONTENT
    raw_text = ""
    try:
        with open(bibtex_source, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except (OSError, FileNotFoundError):
        raw_text = bibtex_source

    # 2. SPLIT INTO SECTIONS
    # We look for lines starting with # to create chunks
    lines = raw_text.splitlines()
    sections = []
    
    current_title = None
    current_buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            # If we have a previous section with a title, save it
            if current_title is not None:
                sections.append({
                    'title': current_title, 
                    'bib_string': '\n'.join(current_buffer)
                })
            
            # Start new section
            current_title = stripped.lstrip('#').strip()
            current_buffer = []
        else:
            # Only add to buffer if we have a section title
            # (skip any content before the first # comment)
            if current_title is not None:
                current_buffer.append(line)
            
    # Append the final section
    if current_title is not None and current_buffer:
        sections.append({
            'title': current_title, 
            'bib_string': '\n'.join(current_buffer)
        })

    # 3. PARSE EACH SECTION AND FORMAT
    publications = []

    for section in sections:
        if not section['bib_string'].strip():
            continue
        
        # Create a fresh parser for each section to avoid state issues
        section_parser = BibTexParser()
        section_parser.customization = convert_to_unicode
        bib_database = bibtexparser.loads(section['bib_string'], parser=section_parser)
        entries = bib_database.entries
        
        # Deduplicate entries by BibTeX ID
        seen_ids = set()
        unique_entries = []
        for entry in entries:
            entry_id = entry.get('ID', '') or entry.get('id', '')
            if entry_id and entry_id not in seen_ids:
                seen_ids.add(entry_id)
                unique_entries.append(entry)
            elif not entry_id:
                # Fallback: use title for deduplication if no ID
                title = clean_tex(entry.get('title', ''))
                if title and title not in seen_ids:
                    seen_ids.add(title)
                    unique_entries.append(entry)
        
        entries = unique_entries
        
        # Sort entries: Year (desc), then Title
        entries.sort(key=lambda x: (x.get('year', '0000'), x.get('title', '')), reverse=True)
        
        count = len(entries)

        # Add section header with count
        if section['title']:
            publications.append({
                'title': section['title'],
                'authors': [f"(*n* = {count})"],
            })

        # Add publication entries
        for entry in entries:
            title = clean_tex(entry.get('title', ''))
            
            journal = entry.get('journal') or entry.get('booktitle') or entry.get('publisher') or ''
            journal = clean_tex(journal)

            date = entry.get('year', '')
            
            doi = entry.get('doi', '')
            if doi and not doi.startswith('http'):
                doi = f"https://doi.org/{doi}"

            raw_authors = entry.get('author', '').split(' and ')
            formatted_authors = [format_author_name(auth, my_name) for auth in raw_authors]

            pub_entry = {
                'title': title,
                'authors': formatted_authors,
            }
            
            # Only add non-empty fields
            if journal:
                pub_entry['journal'] = journal
            if date:
                pub_entry['date'] = date
            if doi:
                pub_entry['doi'] = doi
            
            publications.append(pub_entry)

    return publications

def format_author_name(raw_name, my_name_target):
    raw_name = clean_tex(raw_name.strip())
    
    if ',' in raw_name:
        parts = raw_name.split(',', 1)
        last = parts[0].strip()
        first = parts[1].strip()
    else:
        parts = raw_name.split()
        if len(parts) > 1:
            last = parts[-1]
            first = ' '.join(parts[:-1])
        else:
            return raw_name

    initials_list = []
    first = first.replace('.', ' ')
    
    for name_part in first.split():
        if '-' in name_part:
            sub_parts = [p[0].upper() + '.' for p in name_part.split('-') if p]
            initials_list.append('-'.join(sub_parts))
        elif name_part:
            initials_list.append(name_part[0].upper() + '.')
            
    initials_str = ''.join(initials_list)
    return f"{initials_str} {last}"

def clean_tex(text):
    if not text: return ''
    text = text.replace('{', '').replace('}', '')
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def update_cv_yaml(bibtex_file, cv_yaml_file, my_name="Mason Youngblood"):
    """
    Read BibTeX file, generate publications list, and replace publications section in CV YAML.
    """
    # Generate publications from BibTeX
    publications = bibtex_to_rendercv_yaml(bibtex_file, my_name)
    
    # Read existing CV YAML
    with open(cv_yaml_file, 'r', encoding='utf-8') as f:
        cv_data = yaml.safe_load(f)
    
    # Replace publications section
    if 'cv' in cv_data and 'sections' in cv_data['cv']:
        cv_data['cv']['sections']['publications'] = publications
    else:
        print("Warning: Could not find cv.sections.publications in YAML structure", file=sys.stderr)
        return False
    
    # Write back to file
    with open(cv_yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(cv_data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    
    return True

# --- COMMAND LINE INTERFACE ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Convert BibTeX to rendercv YAML format and update CV YAML file'
    )
    parser.add_argument(
        '--bibtex',
        type=str,
        default='citations.bib',
        help='Path to BibTeX file (default: citations.bib)'
    )
    parser.add_argument(
        '--yaml',
        type=str,
        default='Mason_Youngblood_CV.yaml',
        help='Path to CV YAML file (default: Mason_Youngblood_CV.yaml)'
    )
    parser.add_argument(
        '--name',
        type=str,
        default='Mason Youngblood',
        help='Your name for author formatting (default: Mason Youngblood)'
    )
    parser.add_argument(
        '--output-only',
        action='store_true',
        help='Only output YAML to stdout, do not update file'
    )
    
    args = parser.parse_args()
    
    # Determine script directory for default paths
    script_dir = Path(__file__).parent
    bibtex_path = script_dir / args.bibtex
    yaml_path = script_dir / args.yaml
    
    if args.output_only:
        publications = bibtex_to_rendercv_yaml(str(bibtex_path), args.name)
        output_dict = {'publications': publications}
        print(yaml.dump(output_dict, sort_keys=False, default_flow_style=False, allow_unicode=True))
    else:
        if not bibtex_path.exists():
            print(f"Error: BibTeX file not found: {bibtex_path}", file=sys.stderr)
            sys.exit(1)
        if not yaml_path.exists():
            print(f"Error: CV YAML file not found: {yaml_path}", file=sys.stderr)
            sys.exit(1)
        
        if update_cv_yaml(str(bibtex_path), str(yaml_path), args.name):
            print(f"Successfully updated publications section in {yaml_path}")
        else:
            sys.exit(1)