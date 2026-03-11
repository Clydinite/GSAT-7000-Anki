# Anki GSAT Card Setup Guide (Dark Mode + Cloze Style)

This setup shows the sentences on the front with **collocations hidden** (cloze style) and reveals everything automatically on the back in a dark theme.

## 1. Create Note Type
- Create a Note Type `GSAT-Dark-Cloze` with two fields: `Front` and `Back`.
- `Front` = Headword
- `Back` = Generated HTML content

---

## 2. Card Templates

### Front Template
The front will show the headword and only the sentences from the back field, but with the collocations hidden.

```html
<div class="card front-card">
  <h1 class="headword">{{Front}}</h1>
  
  <div class="sentences-only">
    {{Back}}
  </div>
</div>
```

### Back Template
The back shows everything, revealing the collocations and adding translations.

```html
<div class="card back-card">
  <h1 class="headword">{{Front}}</h1>
  <hr id="answer">
  
  <div class="full-content">
    {{Back}}
  </div>
</div>
```

---

## 3. Styling (Dark Mode CSS)
Copy this into your Anki Note Type's **Styling** section. It uses CSS to hide specific elements on the front and show them on the back.

```css
/* Base Dark Mode Styling */
.card {
  font-family: "Segoe UI", "PingFang TC", "Microsoft JhengHei", sans-serif;
  font-size: 19px;
  text-align: left;
  background-color: #121212; /* Deep Black */
  color: #e0e0e0; /* Off-white text */
  line-height: 1.6;
  max-width: 650px;
  margin: 0 auto;
  padding: 20px;
}

/* Headword */
.headword {
  font-size: 2.2em;
  color: #bb86fc; /* Material Purple */
  text-align: center;
  margin-bottom: 20px;
  border-bottom: 2px solid #3700b3;
}

/* Sentence Containers */
.entry {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  border-left: 4px solid #03dac6; /* Teal accent */
}

.sentence {
  color: #ffffff;
  font-size: 1.1em;
  margin-bottom: 8px;
}

/* Target Word & Collocation */
.target-word {
  color: #ffb74d; /* Orange */
  font-weight: bold;
}

.collocation {
  color: #03dac6; /* Teal */
  font-weight: bold;
  border-bottom: 1px dashed #03dac6;
}

/* Metadata (Translation & Notes) */
.translation {
  color: #b0b0b0;
  font-size: 0.9em;
  font-style: italic;
  margin-top: 5px;
}

.entry-explanation {
  color: #81c784; /* Light Green */
  font-size: 0.85em;
  margin-top: 5px;
  border-top: 1px solid #333;
  padding-top: 5px;
}

.general-explanation {
  background: #2c2c2c;
  padding: 12px;
  border-radius: 6px;
  color: #e0e0e0;
  margin-bottom: 20px;
  font-size: 0.9em;
}

.related-forms {
  color: #757575;
  font-size: 0.8em;
  text-align: center;
  margin-top: 20px;
}

/* --- LOGIC: Hiding/Showing elements based on Front vs Back --- */

/* On the FRONT: */
.front-card .translation,
.front-card .entry-explanation,
.front-card .general-explanation,
.front-card .related-forms {
  display: none !important; /* Hide metadata */
}

/* The "Cloze" effect: Hide collocation text on front */
.front-card .collocation {
  color: transparent !important;
  background-color: #333;
  border-radius: 3px;
  border: none;
  padding: 0 10px;
}

.front-card .collocation::after {
  content: "___";
  color: #03dac6;
  font-weight: bold;
}

/* On the BACK: */
.back-card .collocation {
  color: #03dac6 !important;
  background: transparent;
}
```

---

## 4. Run & Import
1. Execute `python to_anki.py` to refresh your `anki_import.tsv`.
2. Import into Anki choosing the `GSAT-Dark-Cloze` note type.
3. Make sure "Allow HTML" is enabled.
