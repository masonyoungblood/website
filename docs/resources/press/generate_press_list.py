#!/usr/bin/env python3
"""
Generate press list markdown from CSV files.
Combines multiple CSV files, sorts by date (most recent first), and generates markdown.
"""

import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

def parse_date(date_str: str) -> datetime:
    """Parse date string in format 'DD MMM YYYY' to datetime object."""
    try:
        return datetime.strptime(date_str.strip(), '%d %b %Y')
    except ValueError:
        # If parsing fails, return a very old date so it sorts to the bottom
        return datetime(1900, 1, 1)

def read_csv_file(csv_path: Path) -> List[Dict[str, str]]:
    """Read a CSV file and return list of dictionaries."""
    entries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries

def generate_markdown(entries: List[Dict[str, str]]) -> str:
    """Generate markdown from entries matching the current style."""
    output = []
    
    for entry in entries:
        link = entry.get('link', '#')
        image_link = entry.get('image_link', '')
        title = entry.get('title', '')
        source = entry.get('source', '')
        date = entry.get('date', '')
        description = entry.get('description', '')
        
        # Escape HTML special characters in text fields
        title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        source = source.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        date = date.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        description = description.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        card_html = f'''<div class="grid">
	<a href="{link}" class="card" style="display: flex; align-items: flex-start; gap: 1rem; text-decoration: none; color: inherit;">
		<img src="{image_link}" style="width: 100px; flex-shrink: 0;">
		<div>
			<b>{title}</b>
			<br>
			<i>{source} | {date}</i>
			<br>
			{description}
		</div>
	</a>
</div>
'''
        output.append(card_html)
    
    return '\n'.join(output)

def main():
    """Main function to combine CSV files and generate markdown."""
    script_dir = Path(__file__).parent
    
    # Default CSV files
    csv_files = [
        script_dir / 'manual_articles.csv',
        script_dir / 'scraped_articles.csv'
    ]
    
    # Allow command-line arguments for CSV files
    if len(sys.argv) > 1:
        csv_files = [Path(f) for f in sys.argv[1:]]
    
    # Read and combine all entries
    all_entries = []
    for csv_file in csv_files:
        if not csv_file.exists():
            print(f"Warning: CSV file not found: {csv_file}", file=sys.stderr)
            continue
        entries = read_csv_file(csv_file)
        all_entries.extend(entries)
    
    if not all_entries:
        print("Error: No entries found in CSV files", file=sys.stderr)
        sys.exit(1)
    
    # Sort by date (most recent first)
    all_entries.sort(key=lambda x: parse_date(x.get('date', '01 Jan 1900')), reverse=True)
    
    # Generate markdown
    markdown = generate_markdown(all_entries)
    
    # Write to full_press_list.md
    output_file = script_dir / 'full_press_list.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"Successfully generated {len(all_entries)} entries in {output_file}")

if __name__ == "__main__":
    main()

