#!/usr/bin/env python3
"""
Convert BibTeX citations to APA-formatted markdown publications page.
"""

import bibtexparser
try:
    from bibtexparser.bparser import BibTexParser
    from bibtexparser.customization import convert_to_unicode
except ImportError:
    # Fallback for older versions
    BibTexParser = None
    convert_to_unicode = None
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Section mapping from BibTeX comments to markdown headers
SECTION_MAPPING = {
    "#JOURNAL ARTICLES": "## Journal Articles",
    "#BOOK CHAPTERS": "## Book Chapters",
    "#PREPRINTS": "## Preprints",
    "#POPULAR PRESS": "## Popular Press"
}

# Your name for bolding
MY_NAME = "Youngblood"


def get_field_value(entry: Dict, field: str, default: str = "") -> str:
    """Get field value from entry, handling bibtexparser 2.0 Field objects."""
    value = entry.get(field, default)
    if value is None:
        return default
    # Handle Field objects in bibtexparser 2.0
    if hasattr(value, 'value'):
        return str(value.value)
    return str(value)


def clean_tex(text: str) -> str:
    """Remove LaTeX formatting from text."""
    if not text:
        return ""
    text = str(text)  # Convert Field objects to string
    # Remove braces
    text = text.replace("{", "").replace("}", "")
    # Remove LaTeX commands
    text = re.sub(r"\\[a-zA-Z]+\{([^}]+)\}", r"\1", text)
    # Remove remaining backslashes
    text = text.replace("\\", "")
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_author_name(author_str: str, my_name: str = MY_NAME) -> str:
    """Format author name, bolding if it matches my_name."""
    author_str = clean_tex(author_str.strip())
    
    # Split by "and"
    if " and " in author_str:
        parts = author_str.split(" and ")
    elif "," in author_str and " and " not in author_str:
        # Handle "Last, First" format
        parts = [author_str]
    else:
        parts = [author_str]
    
    formatted_parts = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check if this author matches my name
        if my_name.lower() in part.lower():
            # Format: Last, First -> **Last, F.**
            if "," in part:
                last, first = part.split(",", 1)
                last = last.strip()
                first = first.strip()
                # Get initials
                initials = "".join([n[0].upper() + "." for n in first.split()])
                formatted = f"**{last}, {initials}**"
            else:
                # Just bold the name
                formatted = f"**{part}**"
        else:
            # Format other authors: Last, First -> Last, F.
            if "," in part:
                last, first = part.split(",", 1)
                last = last.strip()
                first = first.strip()
                # Get initials
                initials = "".join([n[0].upper() + "." for n in first.split()])
                formatted = f"{last}, {initials}"
            else:
                # Try to split by space
                name_parts = part.split()
                if len(name_parts) >= 2:
                    last = name_parts[-1]
                    first = " ".join(name_parts[:-1])
                    initials = "".join([n[0].upper() + "." for n in first.split()])
                    formatted = f"{last}, {initials}"
                else:
                    formatted = part
        
        formatted_parts.append(formatted)
    
    # Join with ", " and "&" before last author
    if len(formatted_parts) == 1:
        return formatted_parts[0]
    elif len(formatted_parts) == 2:
        return f"{formatted_parts[0]}, & {formatted_parts[1]}"
    else:
        return ", ".join(formatted_parts[:-1]) + ", & " + formatted_parts[-1]


def format_authors(entry: Dict) -> str:
    """Format author list in APA style."""
    author_field = get_field_value(entry, "author", "")
    if not author_field:
        return ""
    
    # Split authors by "and"
    authors = [a.strip() for a in author_field.split(" and ")]
    
    formatted_authors = []
    for author in authors:
        if MY_NAME.lower() in author.lower():
            # Bold my name
            if "," in author:
                last, first = author.split(",", 1)
                last = last.strip()
                first = first.strip()
                initials = "".join([n[0].upper() + "." for n in first.split()])
                formatted = f"**{last}, {initials}**"
            else:
                formatted = f"**{author}**"
        else:
            # Format other authors
            if "," in author:
                last, first = author.split(",", 1)
                last = last.strip()
                first = first.strip()
                initials = "".join([n[0].upper() + "." for n in first.split()])
                formatted = f"{last}, {initials}"
            else:
                # Try to infer last name
                parts = author.split()
                if len(parts) >= 2:
                    last = parts[-1]
                    first = " ".join(parts[:-1])
                    initials = "".join([n[0].upper() + "." for n in first.split()])
                    formatted = f"{last}, {initials}"
                else:
                    formatted = author
        
        formatted_authors.append(formatted)
    
    # Join authors
    if len(formatted_authors) == 1:
        return formatted_authors[0]
    elif len(formatted_authors) == 2:
        return f"{formatted_authors[0]}, & {formatted_authors[1]}"
    else:
        return ", ".join(formatted_authors[:-1]) + ", & " + formatted_authors[-1]


def format_journal_article(entry: Dict) -> str:
    """Format a journal article entry in APA style."""
    authors = format_authors(entry)
    year = get_field_value(entry, "year", "")
    title = clean_tex(get_field_value(entry, "title", ""))
    journal = clean_tex(get_field_value(entry, "journal", ""))
    volume = get_field_value(entry, "volume", "")
    number = get_field_value(entry, "number", "")
    pages = get_field_value(entry, "pages", "")
    doi = get_field_value(entry, "doi", "")
    url = get_field_value(entry, "url", "")
    
    # Build citation
    citation = f"* {authors}"
    if year:
        citation += f" ({year})"
    citation += ". "
    
    if title:
        citation += f"{title}. "
    
    if journal:
        citation += f"*{journal}*"
        if volume:
            citation += f", *{volume}*"
            if number:
                citation += f"({number})"
        if pages:
            citation += f", {pages}"
        citation += ". "
    
    # Add links
    links = []
    if url:
        links.append(f"[Link]({url})")
    if doi and not url:
        links.append(f"[Link](https://doi.org/{doi})")
    
    if links:
        citation += " ".join(links)
    
    return citation


def format_book_chapter(entry: Dict) -> str:
    """Format a book chapter entry in APA style."""
    authors = format_authors(entry)
    year = get_field_value(entry, "year", "")
    title = clean_tex(get_field_value(entry, "title", ""))
    booktitle = clean_tex(get_field_value(entry, "booktitle", "") or get_field_value(entry, "journal", ""))
    publisher = clean_tex(get_field_value(entry, "publisher", ""))
    url = get_field_value(entry, "url", "")
    doi = get_field_value(entry, "doi", "")
    
    # Build citation
    citation = f"* {authors}"
    if year:
        citation += f" ({year})"
    citation += ". "
    
    if title:
        citation += f"{title}. "
    
    if booktitle:
        citation += f"*{booktitle}*"
        if publisher:
            citation += f". {publisher}"
        citation += ". "
    
    # Add links
    links = []
    if url:
        links.append(f"[Link]({url})")
    if doi and not url:
        links.append(f"[Link](https://doi.org/{doi})")
    
    if links:
        citation += " ".join(links)
    
    return citation


def parse_bibtex_with_sections(bibtex_file: Path) -> List[Tuple[str, List[Dict]]]:
    """Parse BibTeX file and group entries by sections."""
    with open(bibtex_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    sections = []
    current_section = None
    current_buffer = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            # Save previous section
            if current_section and current_buffer:
                # Parse the buffer
                bib_string = '\n'.join(current_buffer)
                try:
                    # Try bibtexparser 2.0 API first
                    if hasattr(bibtexparser, 'parse_string'):
                        bib_database = bibtexparser.parse_string(bib_string)
                        sections.append((current_section, bib_database.entries))
                    elif BibTexParser and convert_to_unicode:
                        parser = BibTexParser(customization=convert_to_unicode)
                        bib_database = bibtexparser.loads(bib_string, parser=parser)
                        sections.append((current_section, bib_database.entries))
                    else:
                        bib_database = bibtexparser.loads(bib_string)
                        sections.append((current_section, bib_database.entries))
                except Exception as e:
                    print(f"Warning: Error parsing section {current_section}: {e}")
            
            # Start new section
            current_section = stripped
            current_buffer = []
        else:
            if current_section:
                current_buffer.append(line)
    
    # Handle last section
    if current_section and current_buffer:
        bib_string = '\n'.join(current_buffer)
        try:
            # Try bibtexparser 2.0 API first
            if hasattr(bibtexparser, 'parse_string'):
                bib_database = bibtexparser.parse_string(bib_string)
                sections.append((current_section, bib_database.entries))
            elif BibTexParser and convert_to_unicode:
                parser = BibTexParser(customization=convert_to_unicode)
                bib_database = bibtexparser.loads(bib_string, parser=parser)
                sections.append((current_section, bib_database.entries))
            else:
                bib_database = bibtexparser.loads(bib_string)
                sections.append((current_section, bib_database.entries))
        except Exception as e:
            print(f"Warning: Error parsing section {current_section}: {e}")
    
    return sections


def generate_markdown(sections: List[Tuple[str, List[Dict]]]) -> str:
    """Generate markdown from parsed sections."""
    output = ["# Publications", ""]
    
    for section_header, entries in sections:
        # Get markdown header
        md_header = SECTION_MAPPING.get(section_header, f"## {section_header.lstrip('#').strip()}")
        output.append(md_header)
        output.append("")
        
        # Sort entries by year (descending)
        entries.sort(key=lambda x: int(get_field_value(x, "year", "0") or "0"), reverse=True)
        
        # Format each entry
        for entry in entries:
            entry_type = get_field_value(entry, "ENTRYTYPE", "").lower()
            
            if entry_type == "incollection" or "chapter" in entry_type:
                citation = format_book_chapter(entry)
            else:
                citation = format_journal_article(entry)
            
            output.append(citation)
            output.append("")
    
    return "\n".join(output)


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    
    bibtex_file = project_root / "cv" / "citations.bib"
    output_file = project_root / "docs" / "publications.md"
    
    if not bibtex_file.exists():
        print(f"Error: BibTeX file not found: {bibtex_file}")
        return
    
    # Parse BibTeX with sections
    sections = parse_bibtex_with_sections(bibtex_file)
    
    # Generate markdown
    markdown = generate_markdown(sections)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"Successfully generated {output_file}")
    print(f"Total entries: {sum(len(entries) for _, entries in sections)}")


if __name__ == "__main__":
    main()

