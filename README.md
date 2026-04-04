# GSAT English Vocabulary

This repository contains a collection of vocabulary for GSAT listed in `data/` directory, along with the cards for Anki. The cards are currently under development. I would appreciate support on additional card generations or corrections.

## Card Status

Currently I have completed the following cards:

- Level 1 - 0/1013
- Level 2 - 0/1003
- Level 3 - 1002/1002
- Level 4 - 1002/1002
- Level 5 - 0/1002
- Level 6 - 0/1008

The remaining levels are yet to be generated. You can help by generating cards for any level (probably level 5 would be the best since I'm working on level 4 already). Simply change the `level` in `config.json` and run the scripts. However, a Gemini API key is required (change the `.env.example` to `.env` and fill in the API key), which can be obtained for free on [Google AI Studio](https://aistudio.google.com/api-keys).

There's a huge amount of cards with errors in `* ... *` markings. I'm working on cleaning them up.

## Project Structure

- `data/vocabulary/`: Source word lists for each level.
- `data/raw/`: Raw Gemini API responses in TSV format (level-specific), it includes `<` `>` and `*` markers.
- `data/Anki/`: Formatted TSV files ready for Anki import.
- `config.json`: Central configuration to set the current processing level.

## How to Contribute

The remaining levels are yet to be generated. You can help by generating cards for any unfinished level:

1.  **Setup:** Clone the repo and install dependencies.
2.  **API Key:** Change `.env.example` to `.env` and fill in your Gemini API key from [Google AI Studio](https://aistudio.google.com/api-keys).
3.  **Configure:** Update `config.json` with the level you want to generate (e.g., `"level": 5`).
4.  **Process:** Run `python process.py` to fetch data from the API.
5.  **Export:** Run `python to_anki.py` to generate the Anki import file in `data/Anki/`.
6.  **Submit:** Create a Pull Request with the new files in `data/raw/` and `data/Anki/`.

## Data Source

The vocabulary data is taken from [CEEC](https://www.ceec.edu.tw/xmdoc?xsmsid=0K213553204833715309).

## Acknowledgements

The deck is entirely AI-generated and provided as-is. Please be mindful of potential AI hallucinations or errors. Use this resource to supplement your studies, but verify critical information with a primary source.