"""
VER ETL Pipeline Configuration
Multi-state, multi-language support for Village Ecological Registers across India.
"""
from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EXTRACTED_DIR = DATA_DIR / "extracted"
STRUCTURED_DIR = DATA_DIR / "structured"
REVIEW_DIR = DATA_DIR / "review"
SCHEMA_DIR = PROJECT_ROOT / "schema"

# --- State-Language Mapping ---
# Maps each state to its primary data collection language(s) and Tesseract lang codes
# Install: sudo apt install tesseract-ocr tesseract-ocr-{mar,hin,guj,ori,tel,kan}
STATE_LANGUAGE_MAP = {
    "gujarat": {
        "languages": ["Gujarati", "English"],
        "tesseract_lang": "guj+eng",
        "script": "Gujarati",
    },
    "maharashtra": {
        "languages": ["Marathi", "English"],
        "tesseract_lang": "mar+eng",
        "script": "Devanagari",
    },
    "chhattisgarh": {
        "languages": ["Hindi", "English"],
        "tesseract_lang": "hin+eng",
        "script": "Devanagari",
    },
    "odisha": {
        "languages": ["Odia", "Hindi", "English"],
        "tesseract_lang": "ori+hin+eng",
        "script": "Odia",
    },
    "rajasthan": {
        "languages": ["Hindi", "English"],
        "tesseract_lang": "hin+eng",
        "script": "Devanagari",
    },
    "northeast": {
        "languages": ["English"],
        "tesseract_lang": "eng",
        "script": "Latin",
        "notes": "Covers Assam, Meghalaya, Nagaland, Manipur, Mizoram, Tripura, Arunachal Pradesh, Sikkim",
    },
    "andhra_pradesh": {
        "languages": ["Telugu", "English"],
        "tesseract_lang": "tel+eng",
        "script": "Telugu",
    },
    "telangana": {
        "languages": ["Telugu", "English"],
        "tesseract_lang": "tel+eng",
        "script": "Telugu",
    },
    "karnataka": {
        "languages": ["Kannada", "English"],
        "tesseract_lang": "kan+eng",
        "script": "Kannada",
    },
}

# Fallback if state not matched
DEFAULT_TESSERACT_LANG = "hin+eng"

# --- OCR Settings ---
TESSERACT_PSM = 6   # Assume uniform block of text (use 4 for single column, 6 for block)
TESSERACT_OEM = 3   # Default LSTM engine

# --- PDF Processing ---
PDF_DPI = 200        # Resolution for page image extraction
PDF_DPI_TABLE = 300  # Higher resolution for table pages

# --- Section-to-Page Mapping Template ---
# Multilingual section header keywords for detection
# English headers are present in the printed VER template across all states
# Local language variants added per state/language
SECTION_HEADERS = {
    "section_2": {
        "english": ["Section - 2", "General Information"],
        "hindi": ["विभाग - 2", "सामान्य जानकारी", "गाँव की सामान्य जानकारी"],
        "marathi": ["विभाग -२", "सर्वसाधारण माहिती", "गावाची सर्वसाधारण माहिती"],
        "gujarati": ["વિભાગ - ૨", "સામાન્ય માહિતી", "ગામની સામાન્ય માહિતી"],
        "odia": ["ବିଭାଗ - ୨", "ସାଧାରଣ ତଥ୍ୟ"],
        "telugu": ["విభాగం - 2", "సాధారణ సమాచారం"],
        "kannada": ["ವಿಭಾಗ - ೨", "ಸಾಮಾನ್ಯ ಮಾಹಿತಿ"],
    },
    "section_3": {
        "english": ["Section - 3", "Village History"],
        "hindi": ["विभाग - 3", "गाँव का इतिहास"],
        "marathi": ["विभाग -३", "गावाचा इतिहास"],
        "gujarati": ["વિભાગ - ૩", "ગામનો ઇતિહાસ"],
        "odia": ["ବିଭାଗ - ୩", "ଗ୍ରାମ ଇତିହାସ"],
        "telugu": ["విభాగం - 3", "గ్రామ చరిత్ర"],
        "kannada": ["ವಿಭಾಗ - ೩", "ಹಳ್ಳಿ ಇತಿಹಾಸ"],
    },
    "section_4": {
        "english": ["Section - 4", "Agro-ecological"],
        "hindi": ["विभाग - 4", "कृषि-पारिस्थितिक"],
        "marathi": ["विभाग -४", "शेतीविषयक"],
        "gujarati": ["વિભાગ - ૪", "કૃષિ-ઇકોલોજીકલ"],
        "odia": ["ବିଭାଗ - ୪", "କୃଷି-ପରିବେଶ"],
        "telugu": ["విభాగం - 4", "వ్యవసాయ-పర్యావరణ"],
        "kannada": ["ವಿಭಾಗ - ೪", "ಕೃಷಿ-ಪರಿಸರ"],
    },
    "section_5": {
        "english": ["Section - 5", "Livestock"],
        "hindi": ["विभाग - 5", "पशुधन"],
        "marathi": ["विभाग -५", "पशुधन"],
        "gujarati": ["વિભાગ - ૫", "પશુધન"],
        "odia": ["ବିଭାଗ - ୫", "ପଶୁ"],
        "telugu": ["విభాగం - 5", "పశువులు"],
        "kannada": ["ವಿಭಾಗ - ೫", "ಜಾನುವಾರು"],
    },
    "section_6": {
        "english": ["Section - 6", "Waterscape"],
        "hindi": ["विभाग - 6", "जलक्षेत्र", "पानी"],
        "marathi": ["विभाग -६", "पाणलोट"],
        "gujarati": ["વિભાગ - ૬", "જળ વ્યવસ્થા"],
        "odia": ["ବିଭାଗ - ୬", "ଜଳ"],
        "telugu": ["విభాగం - 6", "నీటి వనరులు"],
        "kannada": ["ವಿಭಾಗ - ೬", "ಜಲ"],
    },
    "section_7": {
        "english": ["Section - 7", "Forest"],
        "hindi": ["विभाग - 7", "वन भूमि"],
        "marathi": ["विभाग -७", "वन जमीन"],
        "gujarati": ["વિભાગ - ૭", "વન જમીન"],
        "odia": ["ବିଭାଗ - ୭", "ଜଙ୍ଗଲ"],
        "telugu": ["విభాగం - 7", "అడవి భూమి"],
        "kannada": ["ವಿಭಾಗ - ೭", "ಅರಣ್ಯ"],
    },
    "section_8": {
        "english": ["Section - 8", "Grassland", "Grazing"],
        "hindi": ["विभाग - 8", "चरागाह", "घास का मैदान"],
        "marathi": ["विभाग -८", "गवताळ", "चराई"],
        "gujarati": ["વિભાગ - ૮", "ઘાસની જમીન"],
        "odia": ["ବିଭାଗ - ୮", "ଘାସ ଜମି"],
        "telugu": ["విభాగం - 8", "పచ్చిక బయలు"],
        "kannada": ["ವಿಭಾಗ - ೮", "ಹುಲ್ಲುಗಾವಲು"],
    },
    "section_9": {
        "english": ["Section - 9", "Revenue Waste"],
        "hindi": ["विभाग - 9", "राजस्व बंजर"],
        "marathi": ["विभाग -९", "महसूल"],
        "gujarati": ["વિભાગ - ૯", "મહેસૂલ"],
        "odia": ["ବିଭାଗ - ୯", "ରାଜସ୍ୱ ଜମି"],
        "telugu": ["విభాగం - 9", "రెవెన్యూ భూమి"],
        "kannada": ["ವಿಭಾಗ - ೯", "ಕಂದಾಯ"],
    },
    "section_10": {
        "english": ["Section - 10", "Grooves", "Banni", "Sacred"],
        "hindi": ["विभाग - 10", "पवित्र उपवन"],
        "marathi": ["विभाग -१०", "देवराई"],
        "gujarati": ["વિભાગ - ૧૦", "પવિત્ર વન"],
        "odia": ["ବିଭାଗ - ୧୦", "ପବିତ୍ର ବନ"],
        "telugu": ["విభాగం - 10", "పవిత్ర వనం"],
        "kannada": ["ವಿಭಾಗ - ೧೦", "ದೇವರ ಕಾಡು"],
    },
    "section_11": {
        "english": ["Section - 11", "Ecologically important"],
        "hindi": ["विभाग - 11", "पारिस्थितिक"],
        "marathi": ["विभाग -११", "पर्यावरणाच्या"],
        "gujarati": ["વિભાગ - ૧૧", "ઇકોલોજીકલ"],
        "odia": ["ବିଭାଗ - ୧୧"],
        "telugu": ["విభాగం - 11"],
        "kannada": ["ವಿಭಾಗ - ೧೧"],
    },
    "section_12": {
        "english": ["Section - 12", "Old and Giant trees"],
        "hindi": ["विभाग - 12", "पुराने और विशाल पेड़"],
        "marathi": ["विभाग -१२", "जुन्या", "महाकाय झाडांची"],
        "gujarati": ["વિભાગ - ૧૨", "જૂના અને વિશાળ વૃક્ષો"],
        "odia": ["ବିଭାଗ - ୧୨", "ପୁରାତନ ଗଛ"],
        "telugu": ["విభాగం - 12", "పురాతన చెట్లు"],
        "kannada": ["ವಿಭಾಗ - ೧೨", "ಹಳೆಯ ಮರಗಳು"],
    },
    "section_13": {
        "english": ["Section - 13", "bee hive"],
        "hindi": ["विभाग - 13", "मधुमक्खी"],
        "marathi": ["विभाग -१३", "मध पोळ"],
        "gujarati": ["વિભાગ - ૧૩", "મધમાખી"],
        "odia": ["ବିଭାଗ - ୧୩", "ମହୁମାଛି"],
        "telugu": ["విభాగం - 13", "తేనెటీగ"],
        "kannada": ["ವಿಭಾಗ - ೧೩", "ಜೇನುಗೂಡು"],
    },
    "section_14": {
        "english": ["Section - 14", "Fire"],
        "hindi": ["विभाग - 14", "आग"],
        "marathi": ["विभाग -१४", "आगीच्या"],
        "gujarati": ["વિભાગ - ૧૪", "આગ"],
        "odia": ["ବିଭାଗ - ୧୪", "ନିଆଁ"],
        "telugu": ["విభాగం - 14", "అగ్ని"],
        "kannada": ["ವಿಭಾಗ - ೧೪", "ಬೆಂಕಿ"],
    },
    "section_15": {
        "english": ["Section - 15", "Conservation ethos"],
        "hindi": ["विभाग - 15", "संरक्षण"],
        "marathi": ["विभाग -१५", "संवर्धन"],
        "gujarati": ["વિભાગ - ૧૫", "સંરક્ષણ"],
        "odia": ["ବିଭାଗ - ୧୫", "ସଂରକ୍ଷଣ"],
        "telugu": ["విభాగం - 15", "సంరక్షణ"],
        "kannada": ["ವಿಭಾಗ - ೧೫", "ಸಂರಕ್ಷಣೆ"],
    },
    "section_16": {
        "english": ["Section - 16", "Medicinal"],
        "hindi": ["विभाग - 16", "औषधीय"],
        "marathi": ["विभाग -१६", "औषधी"],
        "gujarati": ["વિભાગ - ૧૬", "ઔષધીય"],
        "odia": ["ବିଭାଗ - ୧୬", "ଔଷଧୀୟ"],
        "telugu": ["విభాగం - 16", "ఔషధ"],
        "kannada": ["ವಿಭಾಗ - ೧೬", "ಔಷಧ"],
    },
    "section_17": {
        "english": ["Section - 17", "Invasive"],
        "hindi": ["विभाग - 17", "आक्रामक"],
        "marathi": ["विभाग -१७", "आक्रमक"],
        "gujarati": ["વિભાગ - ૧૭", "આક્રમક"],
        "odia": ["ବିଭାଗ - ୧୭", "ଆକ୍ରମଣକାରୀ"],
        "telugu": ["విభాగం - 17", "దాడి చేసే"],
        "kannada": ["ವಿಭಾಗ - ೧೭", "ಆಕ್ರಮಣಕಾರಿ"],
    },
    "section_18": {
        "english": ["Section - 18", "Feral"],
        "hindi": ["विभाग - 18", "जंगली जानवर"],
        "marathi": ["विभाग -१८", "जंगली प्राणी"],
        "gujarati": ["વિભાગ - ૧૮", "જંગલી પ્રાણી"],
        "odia": ["ବିଭାଗ - ୧୮", "ବଣ୍ୟ ପ୍ରାଣୀ"],
        "telugu": ["విభాగం - 18", "వన్య జంతువులు"],
        "kannada": ["ವಿಭಾಗ - ೧೮", "ಕಾಡು ಪ್ರಾಣಿ"],
    },
    "section_19": {
        "english": ["Section - 19", "culturally protected"],
        "hindi": ["विभाग - 19", "सांस्कृतिक रूप से संरक्षित"],
        "marathi": ["विभाग -१९", "सांस्कृतिक"],
        "gujarati": ["વિભાગ - ૧૯", "સાંસ્કૃતિક"],
        "odia": ["ବିଭାଗ - ୧୯", "ସାଂସ୍କୃତିକ"],
        "telugu": ["విభాగం - 19", "సాంస్కృతిక"],
        "kannada": ["ವಿಭಾಗ - ೧೯", "ಸಾಂಸ್ಕೃತಿಕ"],
    },
    "section_20": {
        "english": ["Section - 20", "flora and Fauna"],
        "hindi": ["विभाग - 20", "वनस्पति और जीव"],
        "marathi": ["विभाग -२०", "वनस्पती आणि जीवजंतू"],
        "gujarati": ["વિભાગ - ૨૦", "વનસ્પતિ અને પ્રાણી"],
        "odia": ["ବିଭାଗ - ୨୦", "ଉଦ୍ଭିଦ ଓ ଜୀବଜନ୍ତୁ"],
        "telugu": ["విభాగం - 20", "వృక్షజాతి మరియు జంతుజాతి"],
        "kannada": ["ವಿಭಾಗ - ೨೦", "ಸಸ್ಯ ಮತ್ತು ಪ್ರಾಣಿ"],
    },
}

# --- OCR Confidence Thresholds ---
HIGH_CONFIDENCE = 0.80    # Auto-accept
MEDIUM_CONFIDENCE = 0.50  # Accept but flag for review
LOW_CONFIDENCE = 0.50     # Flag for mandatory human review

# --- Village ID Convention ---
# Format: {village_name}_{block}_{state} all lowercase, spaces replaced with underscores
# Example: manjari_khatav_maharashtra


def get_tesseract_lang(state: str) -> str:
    """Get Tesseract language string for a given state."""
    state_key = state.lower().replace(" ", "_")
    if state_key in STATE_LANGUAGE_MAP:
        return STATE_LANGUAGE_MAP[state_key]["tesseract_lang"]
    # Check if state is a sub-region of northeast
    northeast_states = ["assam", "meghalaya", "nagaland", "manipur", "mizoram",
                        "tripura", "arunachal_pradesh", "sikkim"]
    if state_key in northeast_states:
        return STATE_LANGUAGE_MAP["northeast"]["tesseract_lang"]
    return DEFAULT_TESSERACT_LANG


def get_section_keywords(section_id: str) -> list:
    """Get all language variants of section header keywords for detection."""
    section = SECTION_HEADERS.get(section_id, {})
    keywords = []
    for lang_keywords in section.values():
        keywords.extend(lang_keywords)
    return keywords
