#It will only match first occurence of highlight/note since no way to find exact page.
#Better to add notes/highlights in longer text that can be uniquely identified
import os
import re
import fitz
from datetime import datetime

def get_desktop_path():
    return os.path.join(os.path.expanduser("~"), "Desktop")

def parse_clippings(clippings_file):
    """
    Parses the clippings file to extract highlights and notes with their timestamps,
    page/location information, etc.
    """
    with open(clippings_file, 'r', encoding='utf-8') as f:
        data = f.read()

    blocks = data.split('==========')
    entries = []

    page_re = re.compile(r'page\s+(\d+)', re.IGNORECASE)
    loc_re  = re.compile(r'location\s+([\d-]+)', re.IGNORECASE)
    time_re = re.compile(r'Added on (.*)$', re.IGNORECASE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split('\n')
        if len(lines) < 2:
            continue

        header = lines[1].strip()
        content = lines[-1].strip()  # The text of highlight or note

        # Determine if it's a highlight or a note
        if "Your Highlight" in header:
            entry_type = "highlight"
        elif "Your Note" in header:
            entry_type = "note"
        else:
            continue

        # Parse page, location, timestamp
        page_match = page_re.search(header)
        loc_match = loc_re.search(header)
        time_match = time_re.search(header)

        page_num = int(page_match.group(1)) if page_match else None
        loc_str  = loc_match.group(1) if loc_match else None

        time_obj = None
        if time_match:
            time_str = time_match.group(1).strip()
            try:
                # Kindle format example: "Sunday, January 5, 2025 1:50:08 PM"
                time_obj = datetime.strptime(time_str, "%A, %B %d, %Y %I:%M:%S %p")
            except:
                pass

        entries.append({
            "type": entry_type,
            "text": content,
            "page": page_num,
            "location": loc_str,
            "timestamp": time_obj
        })

    return entries

def match_notes_to_highlights(entries):
    """
    Attach each note to the highlight on the same page (or location)
    that is closest in time (whether earlier or later).
    """
    highlights = []
    notes = []

    for e in entries:
        if e["type"] == "highlight":
            highlights.append(e)
        else:
            notes.append(e)

    # Sort highlights by (page, timestamp)
    highlights.sort(key=lambda h: (
        h["page"] if h["page"] else 999999,
        h["timestamp"] if h["timestamp"] else datetime.min
    ))

    # Build final matched list with a "notes" list for each highlight
    matched_highlights = []
    for h in highlights:
        matched_highlights.append({
            "highlight": h["text"],
            "page": h["page"],
            "location": h["location"],
            "timestamp": h["timestamp"],
            "notes": []  # Store multiple notes if needed
        })

    # Sort notes similarly
    notes.sort(key=lambda n: (
        n["page"] if n["page"] else 999999,
        n["timestamp"] if n["timestamp"] else datetime.min
    ))

    for note in notes:
        note_page = note["page"]
        note_time = note["timestamp"] or datetime.min
        note_loc  = note["location"]

        # Filter highlights on the same page or location
        possible_hls = [
            mh for mh in matched_highlights
            if (mh["page"] == note_page)
        ]
        if not possible_hls and note_loc:
            # fallback match by location if page was not found
            possible_hls = [
                mh for mh in matched_highlights
                if (mh["location"] == note_loc)
            ]

        if not possible_hls:
            # No matching highlight found by page or location
            continue

        # Pick highlight with the minimal absolute time difference
        best_hl = None
        best_diff = float('inf')
        for hl in possible_hls:
            hl_time = hl["timestamp"] or datetime.min
            diff = abs((hl_time - note_time).total_seconds())
            if diff < best_diff:
                best_diff = diff
                best_hl = hl

        # Attach note to the best highlight
        if best_hl is not None:
            best_hl["notes"].append({
                "text": note["text"],
                "timestamp": note_time
            })

    return matched_highlights

def normalize_text(text):
    return ' '.join(text.lower().split())

def annotate_pdf(pdf_in, pdf_out, matched_highlights):
    """
    For each highlight, search on the specified page (if valid),
    highlight the snippet once, and add all associated notes.
    """
    doc = fitz.open(pdf_in)
    total_highlights = 0
    total_notes = 0

    for hl in matched_highlights:
        snippet = hl["highlight"]
        if not snippet:
            continue

        page_num = hl["page"]
        # If valid page, search that. Otherwise search entire doc.
        if page_num and 1 <= page_num <= len(doc):
            pages_to_search = [page_num - 1]
        else:
            pages_to_search = range(len(doc))

        snippet_found = False
        for pnum in pages_to_search:
            page = doc[pnum]
            rects = page.search_for(snippet)
            if rects:
                # Highlight only the first occurrence
                highlight_annot = page.add_highlight_annot(rects[0])
                highlight_annot.update()
                total_highlights += 1

                # Place each note above the highlight, stacked so they don't overlap
                note_offset = 0
                for note_dict in hl["notes"]:
                    note_text = note_dict["text"]
                    note_pos = (rects[0].x0, rects[0].y0 - 15 - note_offset)
                    page.add_text_annot(note_pos, note_text)
                    total_notes += 1
                    note_offset += 15

                snippet_found = True
                break  # Found it once, move on to next highlight

            if snippet_found:
                break

    doc.save(pdf_out)
    print(f"Annotated PDF saved as: {pdf_out}")
    print(f"Total highlights added: {total_highlights}")
    print(f"Total notes added: {total_notes}")

def main():
    desktop = get_desktop_path()
    clippings_file = os.path.join(desktop, "Clippings.txt")
    pdf_input = os.path.join(desktop, "book.pdf")
    pdf_output = os.path.join(desktop, "Annotated_book_with_Notes.pdf")

    if not os.path.isfile(clippings_file):
        print(f"Clippings file not found: {clippings_file}")
        return
    if not os.path.isfile(pdf_input):
        print(f"PDF file not found: {pdf_input}")
        return

    # 1. Parse all highlights & notes
    entries = parse_clippings(clippings_file)

    # 2. Match each note to the highlight with the *closest time* (not just preceding)
    matched_highlights = match_notes_to_highlights(entries)

    # 3. Annotate PDF
    annotate_pdf(pdf_input, pdf_output, matched_highlights)

if __name__ == "__main__":
    main()