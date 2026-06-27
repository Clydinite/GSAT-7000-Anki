# Anki GSAT Card Setup Guide

## 1. Create Note Type
- Create a Note Type `GSAT` with fields: `Front` and `Back`.

---

## 2. Card Templates

### Front Template
```html
<div class="card front-card">
  <div class="header">
    <span class="badge">Vocabulary</span>
    <h1 class="headword">{{Front}}</h1>
    <div style="display:none;">{{tts en_US:Front}}</div>
  </div>
</div>

<script>
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
</script>
```

### Back Template
```html
<div class="card back-card">
  <div class="header">
    <span class="badge">Vocabulary</span>
    <h1 class="headword">{{Front}}</h1>
    <div style="display:none;">{{tts en_US:Front}}</div>
  </div>
  <hr class="separator">
  
  <div class="content-area">
    {{Back}}
  </div>
</div>

<script>
(function() {
  // 1. General Explanation: Blur-to-Reveal Logic
  const general = document.querySelector('.general-explanation');
  if (general) {
    general.classList.add('blur-reveal-container');
    const overlay = document.createElement('div');
    overlay.className = 'blur-overlay';
    
    overlay.onclick = () => {
      general.classList.add('revealed');
      overlay.style.opacity = '0';
      setTimeout(() => overlay.remove(), 400);
    };
    general.appendChild(overlay);
  }

  // 2. Entries: Accordion Reveal Logic
  const metaSections = document.querySelectorAll('.meta-section');
  metaSections.forEach((section) => {
    const trigger = document.createElement('button');
    trigger.className = 'accordion-trigger';
    trigger.innerHTML = `
      <span>Reveal Translation & Notes</span>
      <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
    `;
    
    section.classList.add('accordion-content');
    trigger.onclick = (e) => {
      e.preventDefault();
      trigger.classList.toggle('active');
      section.classList.toggle('expanded');
    };
    section.parentNode.insertBefore(trigger, section);
  });
})();

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
</script>
```

---

## 3. Styling
Copy this into your Anki Note Type's **Styling** section.

```css
.card {
  --background: 240 10% 3.9%;
  --card: 240 10% 3.9%;
  --card-foreground: 0 0% 98%;
  --popover: 240 10% 3.9%;
  --primary: 0 0% 98%;
  --muted: 240 3.7% 15.9%;
  --muted-foreground: 240 5% 64.9%;
  --accent: 217.2 91.2% 59.8%;
  --border: 240 3.7% 15.9%;
  --success: 142.1 70.6% 45.3%;
  
  font-family: "Geist", "Inter", "Segoe UI", "PingFang TC", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  background-color: hsl(var(--background));
  color: hsl(var(--card-foreground));
  line-height: 1.5;
  max-width: 600px;
  margin: 0 auto;
  padding: 32px 24px;
  border-radius: 12px;
}

/* --- General Explanation: Blur Logic --- */
.general-explanation {
  position: relative;
  font-size: 14px;
  padding: 16px;
  background: hsl(240, 4%, 9%);
  border: 1px solid hsl(var(--border));
  border-radius: 8px;
  color: hsl(var(--muted-foreground));
  margin-bottom: 24px;
  line-height: 1.6;
  filter: blur(5px);
  transition: filter 0.5s ease;
  user-select: none;
}

.general-explanation.revealed {
  filter: blur(0);
  user-select: text;
}

.blur-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.1);
  cursor: pointer;
  transition: opacity 0.4s ease;
  z-index: 10;
}

/* --- Entries: Accordion UI --- */
.accordion-trigger {
  box-sizing: border-box;
  width: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  height: 40px;
  line-height: 1;
  background: transparent;
  border: 1px solid hsl(var(--border));
  border-radius: 8px;
  color: hsl(var(--muted-foreground));
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.accordion-trigger:hover {
  background: transparent;
  border: 1px solid hsl(var(--border));
}

.accordion-trigger .chevron {
  width: 16px;
  height: 16px;
  margin: 0 4px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.accordion-trigger.active .chevron {
  transform: rotate(180deg);
}

.accordion-content {
  opacity: 0;
  max-height: 0;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.accordion-content.expanded {
  opacity: 1;
  max-height: 2000px;
  padding-top: 12px;
  padding-bottom: 12px;
}

/* --- Layout Components --- */

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
  text-align: left;
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

/* --- Styling for Hierarchical Senses --- */
.senses-container {
  margin-top: 24px;
}

.sense {
  display: flex;
  margin-top: 16px;
  margin-bottom: 8px;
}

.sense-number {
  color: hsl(var(--accent));
  font-weight: 700;
  margin-right: 8px;
}

.sense-text {
  color: hsl(var(--primary));
  font-weight: 600;
  font-size: 16px;
}

.pattern-label {
  font-family: monospace;
  background: hsl(var(--muted));
  color: hsl(var(--accent));
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  margin-bottom: 8px;
  display: inline-block;
  font-weight: 600;
}

.conjugations {
  font-size: 0.9em;
  color: hsl(var(--muted-foreground));
  margin-bottom: 16px;
  padding: 8px;
  background: hsla(240, 3.7%, 15.9%, 0.3);
  border-radius: 6px;
  text-align: center;
}

.morphology {
  font-size: 0.9em;
  color: hsl(var(--muted-foreground));
  margin-bottom: 8px;
  font-style: italic;
}

.related-item {
  font-size: 0.85em;
  color: hsl(var(--accent));
  margin-left: 12px;
  margin-top: 4px;
}

/* Mobile Adjustments */
@media (max-width: 480px) {
  .card {
    padding: 12px 8px;
  }
  .headword {
    font-size: 40px;
  }
  .sentence {
    font-size: 15px;
  }
  .entry {
    padding: 12px;
    gap: 8px;
    margin-bottom: 12px;
  }
  .general-explanation {
    padding: 12px;
    font-size: 13px;
    margin-bottom: 16px;
  }
  .header {
    margin-bottom: 16px;
  }
}
```

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
