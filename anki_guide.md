# Anki GSAT Card Setup Guide (Shadcn + TTS)

This setup uses a Shadcn-inspired Zinc Dark theme with **Auto-TTS for the headword** and **Press-to-Play TTS for sentences**.

## 1. Create Note Type
- Create a Note Type `GSAT-Shadcn-TTS` with fields: `Front` and `Back`.

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

<script>
// Logic for "Press-to-Play" sentences using Web Speech API
window.playTTS = function(text) {
  // Stop any currently speaking text
  window.speechSynthesis.cancel();
  
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  utterance.rate = 0.9; // Slightly slower for clarity
  
  // Find a high-quality English voice if available
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google')) 
                      || voices.find(v => v.lang.startsWith('en'));
  
  if (preferredVoice) utterance.voice = preferredVoice;
  
  window.speechSynthesis.speak(utterance);
};

// Required for Chrome/Anki to load voices
window.speechSynthesis.getVoices();

// Auto-play the headword on flip
window.playTTS('{{text:Front}}');
</script>
```

---

## 3. Styling (Shadcn Zinc + Buttons)
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
  --success: 142.1 70.6% 45.3%;  /* Emerald 500 */
  
  font-family: "Geist", "Inter", "Segoe UI", "PingFang TC", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  background-color: hsl(var(--background));
  color: hsl(var(--card-foreground));
  line-height: 1.5;
  max-width: 600px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* Mobile Padding Adjustment */
@media (max-width: 480px) {
  .card {
    padding: 16px 12px;
  }
  .headword {
    font-size: 32px !important;
  }
}

/* Header & Typography */
.header {
  text-align: center;
  margin-bottom: 24px;
}

.badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: hsl(var(--accent));
  background: hsla(217, 91%, 60%, 0.1);
  padding: 4px 12px;
  border-radius: 9999px;
  margin-bottom: 8px;
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

/* General Usage Note */
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

/* Entry Container */
.entry {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: 12px;
  margin-bottom: 16px;
}

/* Sentence Area */
.sentence-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.sentence {
  font-size: 17px;
  font-weight: 500;
  color: hsl(var(--primary));
  line-height: 1.5;
}

/* Play Button */
.tts-button {
  background: hsl(var(--muted));
  border: 1px solid hsl(var(--border));
  color: hsl(var(--muted-foreground));
  border-radius: 6px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.tts-button:hover {
  background: hsl(var(--accent));
  color: white;
  border-color: hsl(var(--accent));
}

.tts-button svg {
  width: 16px;
  height: 16px;
}

/* Meta Section (Translation & Explanation) */
.meta-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 12px;
  border-left: 2px solid hsl(var(--success));
  background: hsla(142, 70%, 45%, 0.03);
  margin-top: 4px;
  padding-top: 4px;
  padding-bottom: 4px;
}

.translation {
  font-size: 15px;
  font-weight: 500;
  color: hsl(var(--success));
}

.entry-explanation {
  font-size: 13px;
  font-style: italic;
  color: hsl(var(--muted-foreground));
  line-height: 1.4;
}

/* Related Forms */
.related-forms {
  text-align: center;
  margin-top: 32px;
  font-size: 13px;
  color: hsl(var(--muted-foreground));
  opacity: 0.7;
}

.related-forms .label {
  font-weight: 600;
  color: hsl(var(--primary));
  margin-right: 4px;
}

/* --- Logic: Hiding/Showing --- */

.front-card .meta-section,
.front-card .general-explanation,
.front-card .related-forms {
  display: none !important;
}

/* Cloze Blank Styling */
.front-card .collocation {
  color: transparent !important;
  font-size: 0 !important;
  background-color: hsl(var(--muted));
  text-decoration: none;
  border-radius: 4px;
  padding: 0 8px;
  display: inline-flex;
  min-width: 36px;
  height: 1.2em;
  vertical-align: middle;
  align-items: center;
  justify-content: center;
}

.front-card .collocation::after {
  content: "•••";
  color: hsl(var(--muted-foreground));
  font-size: 12px;
  letter-spacing: 1px;
}

/* Highlighting */
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
```

---

## 4. Import
1. Run `python to_anki.py`.
2. Import `anki_import.tsv` using the `GSAT-Shadcn-TTS` note type.
3. Ensure "Allow HTML" is checked.
