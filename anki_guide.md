# Anki GSAT Card Setup Guide

## 1. Create Note Type
- Create a Note Type `GSAT` with fields: `Front` and `Back`.

---

## 2. Card Templates

You can find the HTML and CSS templates in the `templates/` folder:
- **`templates/front.html`**: Front template.
- **`templates/back.html`**: Back template.
- **`templates/card.css`**: Styling section.

Copy the contents of these files directly into the corresponding sections of your Anki Note Type.

## 3. Previewing Cards
Instead of importing into Anki to preview, you can generate a static preview file:
```bash
python templates/preview.py
```
This generates `templates/preview.html`, which you can open in any browser to verify your CSS and layout.

---

## 4. Import & Deck Organization

The vocabulary is organized by levels. You can choose to import everything into one deck or create a separate deck for each level.

### Importing to Separate Decks
1. In Anki, go to **Import**.
2. Select the level file (e.g., `data/Anki/level3_import.tsv`).
3. In the Import dialog:
   - **Type:** Select the `GSAT` Note Type you created in Step 1.
   - **Deck:** Click the deck name and type a new name like `GSAT::Level 4` to create a sub-deck.
   - **Options:** Ensure "Allow HTML in fields" is checked.
4. Repeat for each level you wish to add.

*Tip: Using the `::` syntax (e.g., `GSAT::Level 1`) allows you to keep all levels organized under a single parent "GSAT" deck.*
