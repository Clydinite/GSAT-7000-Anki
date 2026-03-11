# Anki GSAT Card Setup Guide (Shadcn Zinc Dark)

This setup uses a modern, minimalist "Shadcn UI" aesthetic. It features a Zinc color palette, subtle borders, and a clean card-based layout.

## 1. Create Note Type
- Create a Note Type `GSAT-Shadcn-Dark` with two fields: `Front` and `Back`.
- `Front` = Headword
- `Back` = Generated HTML content

---

## 2. Card Templates

### Front Template
```html
<div class="card front-card">
  <div class="header">
    <span class="badge">Vocabulary</span>
    <h1 class="headword">{{Front}}</h1>
  </div>
  
  <div class="content-area">
    {{Back}}
  </div>
</div>
```

### Back Template
```html
<div class="card back-card">
  <div class="header">
    <span class="badge">Vocabulary</span>
    <h1 class="headword">{{Front}}</h1>
  </div>
  <hr class="separator">
  
  <div class="content-area">
    {{Back}}
  </div>
</div>
```

---

## 3. Styling (Shadcn Zinc CSS)
Copy this into your Anki Note Type's **Styling** section.

```css
/* --- Shadcn Zinc Dark Theme --- */

.card {
  --background: 240 10% 3.9%;    /* Zinc 950 */
  --card: 240 10% 3.9%;
  --card-foreground: 0 0% 98%;
  --popover: 240 10% 3.9%;
  --primary: 0 0% 98%;           /* Zinc 50 */
  --muted: 240 3.7% 15.9%;       /* Zinc 800ish */
  --muted-foreground: 240 5% 64.9%; /* Zinc 400 */
  --accent: 217.2 91.2% 59.8%;   /* Modern Blue */
  --border: 240 3.7% 15.9%;
  
  font-family: "Geist", "Inter", "Segoe UI", "PingFang TC", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  background-color: hsl(var(--background));
  color: hsl(var(--card-foreground));
  line-height: 1.5;
  max-width: 600px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* Header & Typography */
.header {
  text-align: center;
  margin-bottom: 24px;
}

.badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: hsl(var(--accent));
  background: hsla(217, 91%, 60%, 0.1);
  padding: 4px 12px;
  border-radius: 9999px;
  margin-bottom: 12px;
}

.headword {
  font-size: 42px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0;
  color: hsl(var(--primary));
}

.separator {
  border: 0;
  border-top: 1px solid hsl(var(--border));
  margin: 24px 0;
}

/* Usage Note (General Explanation) */
.general-explanation {
  font-size: 14px;
  padding: 16px;
  background: hsl(240, 4%, 9%); /* Zinc 900ish */
  border: 1px solid hsl(var(--border));
  border-radius: 8px;
  color: hsl(var(--muted-foreground));
  margin-bottom: 24px;
  line-height: 1.6;
}

/* Entry Cards */
.entry {
  position: relative;
  padding: 20px;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: 12px;
  margin-bottom: 16px;
  transition: border-color 0.2s;
}

.sentence {
  font-size: 17px;
  font-weight: 400;
  color: hsl(var(--primary));
  line-height: 1.6;
}

/* Highlights */
.target-word {
  color: hsl(var(--accent));
  font-weight: 600;
}

.collocation {
  font-weight: 600;
  color: hsl(var(--primary));
  text-decoration: underline decoration-thickness 2px;
  text-underline-offset: 4px;
  text-decoration-color: hsl(var(--accent));
}

/* Metadata */
.translation {
  margin-top: 12px;
  font-size: 15px;
  font-weight: 500;
  color: #10b981; /* Emerald 500 */
}

.entry-explanation {
  margin-top: 8px;
  font-size: 13px;
  color: hsl(var(--muted-foreground));
  border-top: 1px solid hsla(0, 0%, 100%, 0.05);
  padding-top: 8px;
}

.related-forms {
  text-align: center;
  margin-top: 32px;
  font-size: 13px;
  color: hsl(var(--muted-foreground));
}

.related-forms .label {
  font-weight: 600;
  color: hsl(var(--primary));
  margin-right: 4px;
}

/* --- Logic: Hiding/Showing based on Front vs Back --- */

/* Front Card Specifics */
.front-card .translation,
.front-card .entry-explanation,
.front-card .general-explanation,
.front-card .related-forms {
  display: none !important;
}

/* The Cloze Blank */
.front-card .collocation {
  color: transparent !important;
  background-color: hsl(var(--muted));
  text-decoration: none;
  border-radius: 4px;
  padding: 0 4px;
  display: inline-flex;
  min-width: 60px;
  height: 1.2em;
  vertical-align: middle;
}

.front-card .collocation::after {
  content: "•••";
  color: hsl(var(--muted-foreground));
  font-size: 10px;
  letter-spacing: 2px;
  width: 100%;
  text-align: center;
}

/* Back Card Adjustments */
.back-card .entry {
  border-color: hsla(217, 91%, 60%, 0.2);
}
```

---

## 4. Import Instructions
1. Run `python to_anki.py` to generate the latest `anki_import.tsv`.
2. Import into Anki using the `GSAT-Shadcn-Dark` note type.
3. Ensure "Allow HTML" is checked.
