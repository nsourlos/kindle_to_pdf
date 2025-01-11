import fitz
import re
import sys
from datetime import datetime
from tqdm import tqdm

def parse_clippings(content):
    entries = content.split('==========')
    highlights_and_notes = []
    
    for entry in entries:
        if not entry.strip():
            continue
            
        lines = entry.strip().split('\n')
        if len(lines) < 2:
            continue
            
        metadata = lines[1].strip()
        
        # Extract page number and timestamp
        page_match = re.search(r'page (\d+)', metadata, re.IGNORECASE)
        time_match = re.search(r'Added on (.+)', metadata, re.IGNORECASE)
        if not page_match or not time_match:
            continue
        
        # Parse timestamp
        timestamp = datetime.strptime(time_match.group(1).strip(), '%A, %B %d, %Y %I:%M:%S %p')
        
        entry_type = 'Highlight' if 'Highlight' in metadata else 'Note'
        content = '\n'.join(line for line in lines[2:] if line.strip())
        content = re.sub(r'\s+', ' ', content).replace('\u00a0', ' ').strip()
        
        highlights_and_notes.append({
            'type': entry_type,
            'content': content,
            'page': int(page_match.group(1)),
            'timestamp': timestamp
        })
    
    return highlights_and_notes

filename = sys.argv[1]
clippings = sys.argv[2]

with open(clippings, "r", encoding='utf-8-sig') as f:
    content = f.read()

entries = parse_clippings(content)
print(f"{len(entries)} highlights/notes found in clippings")

doc = fitz.open(filename)
processed = []

# Separate highlights and notes
highlights = [e for e in entries if e['type'] == 'Highlight']
notes = [e for e in entries if e['type'] == 'Note']

# For each note, find the closest highlight by timestamp
for note in notes:
    closest_highlight = None
    min_time_diff = float('inf')
    
    for highlight in highlights:
        time_diff = abs((highlight['timestamp'] - note['timestamp']).total_seconds())
        if time_diff < min_time_diff:
            min_time_diff = time_diff
            closest_highlight = highlight
    
    if closest_highlight:
        note['closest_highlight'] = closest_highlight

# Process pages and add annotations
for page_num, page in enumerate(tqdm(doc, total=len(doc), desc="Processing pages")):
    page_text = ' '.join(page.get_text().split())
    
    # Add highlights
    for highlight in highlights:
        if highlight in processed or highlight['page'] != page_num + 1:
            continue
            
        if highlight['content'] in page_text:
            quads = page.search_for(highlight['content'], quads=True)
            if quads:
                annot = page.add_highlight_annot(quads)
                annot.set_colors({"stroke": (1, 1, 0)})
                annot.update()
                processed.append(highlight)

    # Add notes next to their closest highlights
    for note in notes:
        if note in processed or note['page'] != page_num + 1:
            continue
        
        closest_highlight = note.get('closest_highlight')
        if closest_highlight and closest_highlight in processed:
            highlight_quads = page.search_for(closest_highlight['content'], quads=True)
            if highlight_quads:
                rect = highlight_quads[0].rect
                point = fitz.Point(rect.x1 + 10, rect.y0)  # Place note to the right of the highlight
                annot = page.add_text_annot(point, note['content'])
                annot.update()
                processed.append(note)

output_path = filename.rsplit(".", 1)[0] + "_annotated.pdf"
doc.save(output_path)
print(f"Saved annotated PDF to {output_path}")

remaining = [e for e in entries if e not in processed]
if remaining:
    print("\nCouldn't process these entries:")
    for entry in remaining:
        print(f"- {entry['content'][:100]}...")