/**
 * Translations for the 35 dosha-assessment questions, kept in their own
 * module to keep the main locale JSONs focused on chrome strings.
 *
 * Shape:
 *   QUIZ_TRANSLATIONS[language][questionId] = {
 *     section, prompt, options: { a, b, c }
 *   }
 *
 * The English copy is the canonical source (matches the legacy
 * `QUIZ_QUESTIONS` strings exactly). Hindi is a faithful localization of
 * the same Ayurvedic content.
 */

const SECTIONS = {
  en: {
    physical: "Part 1: Your Physical Characteristics",
    daily: "Part 2: Your Daily Rhythms and Habits",
    mind: "Part 3: Your Mind and Disposition",
  },
  hi: {
    physical: "भाग 1: आपके शारीरिक लक्षण",
    daily: "भाग 2: आपकी दैनिक लय और आदतें",
    mind: "भाग 3: आपका मन और स्वभाव",
  },
};

/** Question section assignments — independent of language. */
export const QUESTION_SECTIONS = {
  natural_body_frame: "physical",
  bone_structure: "physical",
  typical_body_weight: "physical",
  skin_type: "physical",
  natural_hair: "physical",
  teeth_gums: "physical",
  eyes: "physical",
  lips: "physical",
  chin_shape: "physical",
  neck_structure: "physical",
  fingers: "physical",
  physical_endurance: "physical",
  appetite: "daily",
  thirst_frequency: "daily",
  sweat_odor: "daily",
  sleep_pattern: "daily",
  speaking_style: "daily",
  digestion_elimination: "daily",
  activity_pace: "daily",
  libido: "daily",
  weight_response: "daily",
  climate_preference: "daily",
  flavor_cravings: "daily",
  environmental_sensitivity: "daily",
  mind_state: "mind",
  dream_themes: "mind",
  temperament: "mind",
  belief_approach: "mind",
  daily_memory: "mind",
  hobbies: "mind",
  positive_emotion: "mind",
  negative_emotion: "mind",
  finance_style: "mind",
  mood_shift_speed: "mind",
  memory_strength: "mind",
};

const EN = {
  natural_body_frame: {
    prompt: "How would you best describe your natural body frame?",
    options: {
      a: "Thin and unusually tall or short",
      b: "Medium body",
      c: "Stout, stocky or large / broad body",
    },
  },
  bone_structure: {
    prompt: "What is your general bone structure like?",
    options: {
      a: "Light, small bones and/or prominent joints",
      b: "Medium bone structure",
      c: "Heavy / dense bone structure",
    },
  },
  typical_body_weight: {
    prompt: "How would you characterize your typical body weight?",
    options: { a: "Low", b: "Moderate", c: "Can be overweight" },
  },
  skin_type: {
    prompt: "How does your skin usually look and feel?",
    options: {
      a: "Dry, rough, cool",
      b: "Soft, oily, warm",
      c: "Thick, oily, cool, pale, glistening",
    },
  },
  natural_hair: {
    prompt: "Which of the following best describes your natural hair?",
    options: {
      a: "Dry, brown, black, coarse, curly, brittle",
      b: "Soft, fine, often straight, oily, early grey, baldness",
      c: "Thick, oily, lustrous, wavy",
    },
  },
  teeth_gums: {
    prompt: "How would you describe your teeth and gums?",
    options: {
      a: "Irregular, protruded, crooked, thin gums",
      b: "Moderate, yellowish teeth, soft gums",
      c: "Regular, strong, white, healthy",
    },
  },
  eyes: {
    prompt: "What are your eyes like?",
    options: {
      a: "Small, brown, black iris; grey, violet, slate blue",
      b: "Medium, sharp, penetrating, hazel green, light or electric blue",
      c: "Big, blue or brown iris, thick eyelashes, calm eyes",
    },
  },
  lips: {
    prompt: "How would you describe the natural shape and texture of your lips?",
    options: { a: "Thin, small, dry", b: "Medium, soft, red", c: "Thick, large, smooth" },
  },
  chin_shape: {
    prompt: "What is the general shape of your chin?",
    options: { a: "Thin, angular", b: "Tapering", c: "Rounded, double" },
  },
  neck_structure: {
    prompt: "How would you describe your neck?",
    options: { a: "Thin, tall", b: "Medium", c: "Big, folded" },
  },
  fingers: {
    prompt: "What do your fingers naturally look like?",
    options: { a: "Thin, long, tapering", b: "Medium", c: "Thick, broad, short" },
  },
  physical_endurance: {
    prompt: "How would you rate your physical endurance or stamina?",
    options: { a: "Fair", b: "Good", c: "High" },
  },
  appetite: {
    prompt: "When it comes to your appetite, which of these sounds most like you?",
    options: { a: "Variable, scanty", b: "Good, excessive", c: "Steady, constant" },
  },
  thirst_frequency: {
    prompt: "How often do you typically feel thirsty?",
    options: { a: "Variable", b: "Excessive", c: "Less" },
  },
  sweat_odor: {
    prompt: "How much do you typically sweat, and how would you describe your natural body odor?",
    options: {
      a: "Low, scanty, no smell",
      b: "Profuse, hot, strong smell",
      c: "Moderate, cool, pleasant smell",
    },
  },
  sleep_pattern: {
    prompt: "What are your usual sleep patterns like?",
    options: {
      a: "Light, interrupted",
      b: "Moderate, 6-8 hours",
      c: "More than 8 hours",
    },
  },
  speaking_style: {
    prompt: "How would you describe your natural speaking style?",
    options: {
      a: "Talkative, may ramble",
      b: "Speaks purposefully",
      c: "Speaks slow and cautiously",
    },
  },
  digestion_elimination: {
    prompt: "What are your typical digestive and elimination patterns?",
    options: {
      a: "Irregular, dry, hard, tendency toward gas and constipation",
      b: "Regular, soft, sometimes loose",
      c: "Regular, solid, well-formed",
    },
  },
  activity_pace: {
    prompt: "What is your usual pace during physical activities?",
    options: { a: "Fast and very active", b: "Medium", c: "Slow and steady" },
  },
  libido: {
    prompt: "How would you describe your natural libido or sexual activity?",
    options: { a: "Lower, variable", b: "Moderate", c: "Good" },
  },
  weight_response: {
    prompt: "How does your body naturally respond to gaining or losing weight?",
    options: {
      a: "Hard to gain, easy to lose",
      b: "Easy to gain, easy to lose",
      c: "Easy to gain, hard to lose",
    },
  },
  climate_preference: {
    prompt: "What type of climate or weather do you generally prefer?",
    options: { a: "Prefers warm", b: "Prefers cool", c: "Enjoys changes of seasons" },
  },
  flavor_cravings: {
    prompt: "Which types of flavors do you find yourself craving the most?",
    options: {
      a: "Prefers sweet, sour, salty",
      b: "Prefers sweet, bitter, or astringent",
      c: "Prefers pungent, bitter or astringent",
    },
  },
  environmental_sensitivity: {
    prompt: "Which of the following environmental factors are you most sensitive to?",
    options: { a: "Cold, dryness, wind", b: "Heat, sunlight, fire", c: "Cold, damp" },
  },
  mind_state: {
    prompt: "How would you describe the natural state of your mind?",
    options: { a: "Restless, always active", b: "Aggressive, intelligent", c: "Calm" },
  },
  dream_themes: {
    prompt: "What kinds of themes appear most frequently in your dreams?",
    options: {
      a: "Fearful flying, jumping, running",
      b: "Fiery, passionate, anger, violence",
      c: "Watery, rivers, oceans, swimming, romantic",
    },
  },
  temperament: {
    prompt: "How would you describe your overall temperament day-to-day?",
    options: {
      a: "Nervous, changeable",
      b: "Motivated, aggressive",
      c: "Calm, content, conservative",
    },
  },
  belief_approach: {
    prompt: "How do you generally approach your personal beliefs or faith?",
    options: { a: "Changeable", b: "Determined fanatic", c: "Steady, slow to change" },
  },
  daily_memory: {
    prompt: "How does your memory usually function in daily life?",
    options: {
      a: "Easily notices things but easily forgets",
      b: "Sharp",
      c: "Slow to take notice but won't forget",
    },
  },
  hobbies: {
    prompt: "What kinds of hobbies or activities do you naturally gravitate toward?",
    options: {
      a: "Dancing, artistic activities, talking",
      b: "Competitive ventures, debate, politics, hunting",
      c: "Family and social gatherings, cooking, collecting",
    },
  },
  positive_emotion: {
    prompt: "Which positive emotion resonates with you the most often?",
    options: { a: "Adaptability", b: "Courage", c: "Love" },
  },
  negative_emotion: {
    prompt: "When you experience negative emotions, which one tends to surface most frequently?",
    options: {
      a: "Feels fear often",
      b: "Often afflicted with anger",
      c: "Attachment",
    },
  },
  finance_style: {
    prompt: "How do you generally tend to manage your personal finances?",
    options: {
      a: "Spends on trifles",
      b: "Spends money on luxuries",
      c: "Good money preserver",
    },
  },
  mood_shift_speed: {
    prompt: "How quickly do your moods tend to shift?",
    options: { a: "Changes quickly", b: "Changes slowly", c: "Steady, non-changing" },
  },
  memory_strength: {
    prompt: "When it comes to retaining information, what type of memory is your strongest?",
    options: {
      a: "Short-term is best",
      b: "Good general memory",
      c: "Long-term is good",
    },
  },
};

const HI = {
  natural_body_frame: {
    prompt: "अपने प्राकृतिक शरीर के ढांचे का सबसे अच्छा वर्णन कैसे करेंगे?",
    options: {
      a: "पतला और असामान्य रूप से लंबा या छोटा",
      b: "मध्यम शरीर",
      c: "गठीला, मोटा या बड़ा / चौड़ा शरीर",
    },
  },
  bone_structure: {
    prompt: "आपकी सामान्य अस्थि-संरचना कैसी है?",
    options: {
      a: "हल्की, छोटी हड्डियाँ और/या उभरे हुए जोड़",
      b: "मध्यम अस्थि-संरचना",
      c: "भारी / घनी अस्थि-संरचना",
    },
  },
  typical_body_weight: {
    prompt: "आप अपने सामान्य शरीर के वजन को कैसे बताएंगे?",
    options: { a: "कम", b: "मध्यम", c: "अधिक हो सकता है" },
  },
  skin_type: {
    prompt: "आपकी त्वचा सामान्यतः कैसी दिखती और महसूस होती है?",
    options: {
      a: "सूखी, खुरदरी, ठंडी",
      b: "मुलायम, तैलीय, गर्म",
      c: "मोटी, तैलीय, ठंडी, पीली, चमकदार",
    },
  },
  natural_hair: {
    prompt: "आपके प्राकृतिक बालों का सबसे अच्छा वर्णन क्या है?",
    options: {
      a: "सूखे, भूरे, काले, कड़े, घुंघराले, टूटने वाले",
      b: "मुलायम, बारीक, अक्सर सीधे, तैलीय, जल्दी सफेद, गंजापन",
      c: "घने, तैलीय, चमकदार, लहरदार",
    },
  },
  teeth_gums: {
    prompt: "आप अपने दांतों और मसूड़ों का वर्णन कैसे करेंगे?",
    options: {
      a: "अनियमित, बाहर निकले, टेढ़े; पतले मसूड़े",
      b: "मध्यम, हल्के पीले दांत, मुलायम मसूड़े",
      c: "नियमित, मजबूत, सफेद, स्वस्थ",
    },
  },
  eyes: {
    prompt: "आपकी आँखें कैसी हैं?",
    options: {
      a: "छोटी, भूरी या काली पुतली; सलेटी, बैंगनी, स्लेट नीली",
      b: "मध्यम, तीखी, भेदक; हेज़ल हरी, हल्की या इलेक्ट्रिक नीली",
      c: "बड़ी, नीली या भूरी पुतली, घनी पलकें, शांत आँखें",
    },
  },
  lips: {
    prompt: "आपके होंठों का प्राकृतिक आकार और बनावट कैसी है?",
    options: { a: "पतले, छोटे, सूखे", b: "मध्यम, मुलायम, लाल", c: "मोटे, बड़े, चिकने" },
  },
  chin_shape: {
    prompt: "आपकी ठोड़ी का सामान्य आकार क्या है?",
    options: { a: "पतली, कोणीय", b: "नुकीली", c: "गोल, दोहरी" },
  },
  neck_structure: {
    prompt: "आप अपनी गर्दन का वर्णन कैसे करेंगे?",
    options: { a: "पतली, लंबी", b: "मध्यम", c: "बड़ी, मुड़ी हुई" },
  },
  fingers: {
    prompt: "आपकी उंगलियाँ स्वाभाविक रूप से कैसी दिखती हैं?",
    options: { a: "पतली, लंबी, नुकीली", b: "मध्यम", c: "मोटी, चौड़ी, छोटी" },
  },
  physical_endurance: {
    prompt: "आप अपनी शारीरिक सहनशक्ति या स्टैमिना को कैसे आंकेंगे?",
    options: { a: "ठीक-ठाक", b: "अच्छा", c: "उच्च" },
  },
  appetite: {
    prompt: "भूख की बात करें तो इनमें से क्या आप पर सबसे अधिक लागू होता है?",
    options: { a: "अनियमित, कम", b: "अच्छी, अत्यधिक", c: "स्थिर, निरंतर" },
  },
  thirst_frequency: {
    prompt: "आपको आमतौर पर कितनी बार प्यास लगती है?",
    options: { a: "अनियमित", b: "अत्यधिक", c: "कम" },
  },
  sweat_odor: {
    prompt: "आपको आमतौर पर कितना पसीना आता है, और आपकी प्राकृतिक शरीर की गंध कैसी है?",
    options: {
      a: "कम, हल्का, बिना गंध",
      b: "बहुत अधिक, गर्म, तीव्र गंध",
      c: "मध्यम, ठंडा, सुखद गंध",
    },
  },
  sleep_pattern: {
    prompt: "आपकी सामान्य नींद कैसी होती है?",
    options: {
      a: "हल्की, बीच में टूटने वाली",
      b: "मध्यम, 6-8 घंटे",
      c: "8 घंटे से अधिक",
    },
  },
  speaking_style: {
    prompt: "आप अपनी प्राकृतिक बोलने की शैली का वर्णन कैसे करेंगे?",
    options: {
      a: "बहुत बोलने वाला, इधर-उधर भटक सकता है",
      b: "उद्देश्यपूर्ण ढंग से बोलता है",
      c: "धीरे और सावधानी से बोलता है",
    },
  },
  digestion_elimination: {
    prompt: "आपका सामान्य पाचन और मल-त्याग कैसा रहता है?",
    options: {
      a: "अनियमित, सूखा, कठोर; गैस और कब्ज की प्रवृत्ति",
      b: "नियमित, मुलायम, कभी-कभी ढीला",
      c: "नियमित, ठोस, अच्छी तरह बना हुआ",
    },
  },
  activity_pace: {
    prompt: "शारीरिक गतिविधियों के दौरान आपकी सामान्य गति कैसी होती है?",
    options: { a: "तेज़ और बहुत सक्रिय", b: "मध्यम", c: "धीमी और स्थिर" },
  },
  libido: {
    prompt: "आप अपनी प्राकृतिक कामेच्छा या यौन गतिविधि का वर्णन कैसे करेंगे?",
    options: { a: "कम, अनियमित", b: "मध्यम", c: "अच्छी" },
  },
  weight_response: {
    prompt: "आपका शरीर वजन बढ़ाने या घटाने पर स्वाभाविक रूप से कैसी प्रतिक्रिया देता है?",
    options: {
      a: "बढ़ाना मुश्किल, घटाना आसान",
      b: "बढ़ाना और घटाना दोनों आसान",
      c: "बढ़ाना आसान, घटाना मुश्किल",
    },
  },
  climate_preference: {
    prompt: "आप आमतौर पर किस तरह की जलवायु या मौसम पसंद करते हैं?",
    options: { a: "गर्म पसंद", b: "ठंडा पसंद", c: "मौसम बदलना अच्छा लगता है" },
  },
  flavor_cravings: {
    prompt: "आपको किस तरह के स्वादों की सबसे अधिक इच्छा होती है?",
    options: {
      a: "मीठा, खट्टा, नमकीन पसंद",
      b: "मीठा, कड़वा या कसैला पसंद",
      c: "तीखा, कड़वा या कसैला पसंद",
    },
  },
  environmental_sensitivity: {
    prompt: "इनमें से किन वातावरणीय कारकों के प्रति आप सबसे अधिक संवेदनशील हैं?",
    options: { a: "ठंड, सूखापन, हवा", b: "गर्मी, धूप, अग्नि", c: "ठंड, नमी" },
  },
  mind_state: {
    prompt: "आप अपने मन की प्राकृतिक स्थिति का वर्णन कैसे करेंगे?",
    options: { a: "बेचैन, हमेशा सक्रिय", b: "आक्रामक, बुद्धिमान", c: "शांत" },
  },
  dream_themes: {
    prompt: "आपके सपनों में सबसे अधिक किस तरह के विषय आते हैं?",
    options: {
      a: "डर भरे — उड़ना, कूदना, दौड़ना",
      b: "अग्निमय, उत्साही, क्रोध, हिंसा",
      c: "जल से जुड़े — नदी, समुद्र, तैरना, रोमांटिक",
    },
  },
  temperament: {
    prompt: "आप दैनिक रूप से अपने स्वभाव का वर्णन कैसे करेंगे?",
    options: {
      a: "घबराया हुआ, बदलने वाला",
      b: "प्रेरित, आक्रामक",
      c: "शांत, संतुष्ट, परंपरावादी",
    },
  },
  belief_approach: {
    prompt: "आप अपनी व्यक्तिगत मान्यताओं या आस्था के प्रति कैसा दृष्टिकोण रखते हैं?",
    options: { a: "बदलने वाला", b: "दृढ़ कट्टर", c: "स्थिर, धीरे बदलने वाला" },
  },
  daily_memory: {
    prompt: "रोज़मर्रा में आपकी स्मृति आमतौर पर कैसे काम करती है?",
    options: {
      a: "चीज़ें आसानी से देखता है पर भूल भी जाता है",
      b: "तीव्र",
      c: "देर से ध्यान देता है पर भूलता नहीं",
    },
  },
  hobbies: {
    prompt: "आप किस तरह के शौक या गतिविधियों की ओर स्वाभाविक रूप से झुकते हैं?",
    options: {
      a: "नृत्य, कलात्मक गतिविधियाँ, बातचीत",
      b: "प्रतिस्पर्धी कार्य, बहस, राजनीति, शिकार",
      c: "पारिवारिक और सामाजिक मेल, खाना पकाना, संग्रह करना",
    },
  },
  positive_emotion: {
    prompt: "कौन सी सकारात्मक भावना आपके साथ सबसे अधिक मेल खाती है?",
    options: { a: "अनुकूलनशीलता", b: "साहस", c: "प्रेम" },
  },
  negative_emotion: {
    prompt: "नकारात्मक भावनाओं में से कौन सी सबसे अधिक उभरती है?",
    options: {
      a: "अक्सर भय महसूस करता है",
      b: "अक्सर क्रोध से ग्रस्त",
      c: "आसक्ति",
    },
  },
  finance_style: {
    prompt: "आप आमतौर पर अपने व्यक्तिगत वित्त को कैसे संभालते हैं?",
    options: {
      a: "छोटी-मोटी चीज़ों पर खर्च",
      b: "विलासिता पर खर्च",
      c: "अच्छा बचत करने वाला",
    },
  },
  mood_shift_speed: {
    prompt: "आपके मूड कितनी जल्दी बदलते हैं?",
    options: { a: "जल्दी बदलता है", b: "धीरे बदलता है", c: "स्थिर, नहीं बदलता" },
  },
  memory_strength: {
    prompt: "जानकारी याद रखने में आपकी सबसे मजबूत स्मृति कौन सी है?",
    options: {
      a: "अल्पकालिक सबसे अच्छी",
      b: "अच्छी सामान्य स्मृति",
      c: "दीर्घकालिक अच्छी",
    },
  },
};

export const QUIZ_TRANSLATIONS = { en: EN, hi: HI };

/**
 * Build the localized question array consumed by `useQuizViewModel`.
 * Falls back to English for any unsupported language and per-question
 * for any missing entry.
 *
 * @param {string} language e.g. "en" or "hi"
 * @returns {Array<{ id: string, section: string, prompt: string, options: { a: string, b: string, c: string } }>}
 */
export function getLocalizedQuestions(language) {
  const baseLang = (language || "en").slice(0, 2);
  const dict = QUIZ_TRANSLATIONS[baseLang] || QUIZ_TRANSLATIONS.en;
  const sections = SECTIONS[baseLang] || SECTIONS.en;

  return Object.keys(QUESTION_SECTIONS).map((id) => {
    const enFallback = QUIZ_TRANSLATIONS.en[id];
    const entry = dict[id] || enFallback;
    const sectionKey = QUESTION_SECTIONS[id];
    return {
      id,
      section: sections[sectionKey] || SECTIONS.en[sectionKey],
      prompt: entry.prompt || enFallback.prompt,
      options: {
        a: entry.options?.a ?? enFallback.options.a,
        b: entry.options?.b ?? enFallback.options.b,
        c: entry.options?.c ?? enFallback.options.c,
      },
    };
  });
}
