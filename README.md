# 📚 Kindle Annotations Transfer

A powerful tool to transfer your Kindle highlights and notes to PDF files, making your digital reading experience seamless and organized.

## 🌟 Features

- Import highlights and notes from Kindle's `My Clippings.txt` file
- Support for both PDF and MOBI-originated content
- Intelligent matching of notes to their corresponding highlights
- Visual highlighting in the PDF that matches your Kindle experience
- Smart note placement next to relevant highlights
- Handles both page-based and location-based annotations

## 🛠️ Usage

### For PDF-originated books (`kindle_pdf.py`):

```bash
python kindle_pdf.py path/to/pdf_file.pdf path/to/My_Clippings.txt
```

### For MOBI-originated books (`kindle_mobi.py`):

Set paths inside the `kindle_mobi.py` file. Then run:

```bash
python kindle_mobi.py
```

Note: The MOBI version expects files in specific locations on your Desktop. Edit the `main()` function to customize paths.

## 🔍 How It Works

### PDF Version
- Precisely matches highlights based on exact text
- Places notes adjacent to their corresponding highlights
- Maintains the exact positioning of highlights as they appear in your Kindle

### MOBI Version
- Handles books where page numbers might not exactly match
- Tries to match notes with highlights based on timestamps
- Searches entire document when page numbers aren't available
- Stacks multiple notes above their corresponding highlights

## 📋 Requirements

- Python 3.x
- PyMuPDF (fitz)
- tqdm (for PDF version)
- datetime
- re

## ⚠️ Important Notes & Limitations

- The PDF version is more precise as it works with exact text
- The MOBI version will match the first occurrence of each highlight since exact page mapping isn't always possible
- Longer highlighted text segments have a higher success rate of correct mapping
- When identical phrases appear multiple times in the text, the tool may incorrectly map to the first occurrence
- For best results:
  - Highlight longer, unique passages of text
  - Avoid highlighting common phrases or single words
  - Use the PDF version when possible for more accurate mapping


## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License.