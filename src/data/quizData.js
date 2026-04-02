export const DOSHA_MAP = {
  a: "vata",
  b: "pitta",
  c: "kapha",
};

export const DOSHA_LABELS = {
  vata: "Vata",
  pitta: "Pitta",
  kapha: "Kapha",
};

export const DOSHA_SUMMARIES = {
  vata:
    "Your profile leans Vata. You likely thrive with steady routines, grounding meals, warmth, and intentional wind-down rituals that calm a highly active mind.",
  pitta:
    "Your profile leans Pitta. You likely do best with balanced intensity, cooling habits, and sustainable structure that channels ambition without overheating body or mind.",
  kapha:
    "Your profile leans Kapha. You likely benefit from energizing movement, lighter stimulation, and momentum-building routines that keep motivation and metabolism active.",
};

export const QUIZ_QUESTIONS = [
  {
    id: "natural_body_frame",
    section: "Part 1: Your Physical Characteristics",
    prompt: "How would you best describe your natural body frame?",
    options: {
      a: "Thin and unusually tall or short",
      b: "Medium body",
      c: "Stout, stocky or large / broad body",
    },
  },
  {
    id: "bone_structure",
    section: "Part 1: Your Physical Characteristics",
    prompt: "What is your general bone structure like?",
    options: {
      a: "Light, small bones and/or prominent joints",
      b: "Medium bone structure",
      c: "Heavy / dense bone structure",
    },
  },
  {
    id: "typical_body_weight",
    section: "Part 1: Your Physical Characteristics",
    prompt: "How would you characterize your typical body weight?",
    options: {
      a: "Low",
      b: "Moderate",
      c: "Can be overweight",
    },
  },
  {
    id: "skin_type",
    section: "Part 1: Your Physical Characteristics",
    prompt: "How does your skin usually look and feel?",
    options: {
      a: "Dry, rough, cool",
      b: "Soft, oily, warm",
      c: "Thick, oily, cool, pale, glistening",
    },
  },
  {
    id: "natural_hair",
    section: "Part 1: Your Physical Characteristics",
    prompt: "Which of the following best describes your natural hair?",
    options: {
      a: "Dry, brown, black, coarse, curly, brittle",
      b: "Soft, fine, often straight, oily, early grey, baldness",
      c: "Thick, oily, lustrous, wavy",
    },
  },
  {
    id: "teeth_gums",
    section: "Part 1: Your Physical Characteristics",
    prompt: "How would you describe your teeth and gums?",
    options: {
      a: "Irregular, protruded, crooked, thin gums",
      b: "Moderate, yellowish teeth, soft gums",
      c: "Regular, strong, white, healthy",
    },
  },
  {
    id: "eyes",
    section: "Part 1: Your Physical Characteristics",
    prompt: "What are your eyes like?",
    options: {
      a: "Small, brown, black iris; grey, violet, slate blue",
      b: "Medium, sharp, penetrating, hazel green, light or electric blue",
      c: "Big, blue or brown iris, thick eyelashes, calm eyes",
    },
  },
  {
    id: "lips",
    section: "Part 1: Your Physical Characteristics",
    prompt: "How would you describe the natural shape and texture of your lips?",
    options: {
      a: "Thin, small, dry",
      b: "Medium, soft, red",
      c: "Thick, large, smooth",
    },
  },
  {
    id: "chin_shape",
    section: "Part 1: Your Physical Characteristics",
    prompt: "What is the general shape of your chin?",
    options: {
      a: "Thin, angular",
      b: "Tapering",
      c: "Rounded, double",
    },
  },
  {
    id: "neck_structure",
    section: "Part 1: Your Physical Characteristics",
    prompt: "How would you describe your neck?",
    options: {
      a: "Thin, tall",
      b: "Medium",
      c: "Big, folded",
    },
  },
  {
    id: "fingers",
    section: "Part 1: Your Physical Characteristics",
    prompt: "What do your fingers naturally look like?",
    options: {
      a: "Thin, long, tapering",
      b: "Medium",
      c: "Thick, broad, short",
    },
  },
  {
    id: "physical_endurance",
    section: "Part 1: Your Physical Characteristics",
    prompt: "How would you rate your physical endurance or stamina?",
    options: {
      a: "Fair",
      b: "Good",
      c: "High",
    },
  },
  {
    id: "appetite",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "When it comes to your appetite, which of these sounds most like you?",
    options: {
      a: "Variable, scanty",
      b: "Good, excessive",
      c: "Steady, constant",
    },
  },
  {
    id: "thirst_frequency",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "How often do you typically feel thirsty?",
    options: {
      a: "Variable",
      b: "Excessive",
      c: "Less",
    },
  },
  {
    id: "sweat_odor",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "How much do you typically sweat, and how would you describe your natural body odor?",
    options: {
      a: "Low, scanty, no smell",
      b: "Profuse, hot, strong smell",
      c: "Moderate, cool, pleasant smell",
    },
  },
  {
    id: "sleep_pattern",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "What are your usual sleep patterns like?",
    options: {
      a: "Light, interrupted",
      b: "Moderate, 6-8 hours",
      c: "More than 8 hours",
    },
  },
  {
    id: "speaking_style",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "How would you describe your natural speaking style?",
    options: {
      a: "Talkative, may ramble",
      b: "Speaks purposefully",
      c: "Speaks slow and cautiously",
    },
  },
  {
    id: "digestion_elimination",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "What are your typical digestive and elimination patterns?",
    options: {
      a: "Irregular, dry, hard, tendency toward gas and constipation",
      b: "Regular, soft, sometimes loose",
      c: "Regular, solid, well-formed",
    },
  },
  {
    id: "activity_pace",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "What is your usual pace during physical activities?",
    options: {
      a: "Fast and very active",
      b: "Medium",
      c: "Slow and steady",
    },
  },
  {
    id: "libido",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "How would you describe your natural libido or sexual activity?",
    options: {
      a: "Lower, variable",
      b: "Moderate",
      c: "Good",
    },
  },
  {
    id: "weight_response",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "How does your body naturally respond to gaining or losing weight?",
    options: {
      a: "Hard to gain, easy to lose",
      b: "Easy to gain, easy to lose",
      c: "Easy to gain, hard to lose",
    },
  },
  {
    id: "climate_preference",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "What type of climate or weather do you generally prefer?",
    options: {
      a: "Prefers warm",
      b: "Prefers cool",
      c: "Enjoys changes of seasons",
    },
  },
  {
    id: "flavor_cravings",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "Which types of flavors do you find yourself craving the most?",
    options: {
      a: "Prefers sweet, sour, salty",
      b: "Prefers sweet, bitter, or astringent",
      c: "Prefers pungent, bitter or astringent",
    },
  },
  {
    id: "environmental_sensitivity",
    section: "Part 2: Your Daily Rhythms and Habits",
    prompt: "Which of the following environmental factors are you most sensitive to?",
    options: {
      a: "Cold, dryness, wind",
      b: "Heat, sunlight, fire",
      c: "Cold, damp",
    },
  },
  {
    id: "mind_state",
    section: "Part 3: Your Mind and Disposition",
    prompt: "How would you describe the natural state of your mind?",
    options: {
      a: "Restless, always active",
      b: "Aggressive, intelligent",
      c: "Calm",
    },
  },
  {
    id: "dream_themes",
    section: "Part 3: Your Mind and Disposition",
    prompt: "What kinds of themes appear most frequently in your dreams?",
    options: {
      a: "Fearful flying, jumping, running",
      b: "Fiery, passionate, anger, violence",
      c: "Watery, rivers, oceans, swimming, romantic",
    },
  },
  {
    id: "temperament",
    section: "Part 3: Your Mind and Disposition",
    prompt: "How would you describe your overall temperament day-to-day?",
    options: {
      a: "Nervous, changeable",
      b: "Motivated, aggressive",
      c: "Calm, content, conservative",
    },
  },
  {
    id: "belief_approach",
    section: "Part 3: Your Mind and Disposition",
    prompt: "How do you generally approach your personal beliefs or faith?",
    options: {
      a: "Changeable",
      b: "Determined fanatic",
      c: "Steady, slow to change",
    },
  },
  {
    id: "daily_memory",
    section: "Part 3: Your Mind and Disposition",
    prompt: "How does your memory usually function in daily life?",
    options: {
      a: "Easily notices things but easily forgets",
      b: "Sharp",
      c: "Slow to take notice but won't forget",
    },
  },
  {
    id: "hobbies",
    section: "Part 3: Your Mind and Disposition",
    prompt: "What kinds of hobbies or activities do you naturally gravitate toward?",
    options: {
      a: "Dancing, artistic activities, talking",
      b: "Competitive ventures, debate, politics, hunting",
      c: "Family and social gatherings, cooking, collecting",
    },
  },
  {
    id: "positive_emotion",
    section: "Part 3: Your Mind and Disposition",
    prompt: "Which positive emotion resonates with you the most often?",
    options: {
      a: "Adaptability",
      b: "Courage",
      c: "Love",
    },
  },
  {
    id: "negative_emotion",
    section: "Part 3: Your Mind and Disposition",
    prompt: "When you experience negative emotions, which one tends to surface most frequently?",
    options: {
      a: "Feels fear often",
      b: "Often afflicted with anger",
      c: "Attachment",
    },
  },
  {
    id: "finance_style",
    section: "Part 3: Your Mind and Disposition",
    prompt: "How do you generally tend to manage your personal finances?",
    options: {
      a: "Spends on trifles",
      b: "Spends money on luxuries",
      c: "Good money preserver",
    },
  },
  {
    id: "mood_shift_speed",
    section: "Part 3: Your Mind and Disposition",
    prompt: "How quickly do your moods tend to shift?",
    options: {
      a: "Changes quickly",
      b: "Changes slowly",
      c: "Steady, non-changing",
    },
  },
  {
    id: "memory_strength",
    section: "Part 3: Your Mind and Disposition",
    prompt: "When it comes to retaining information, what type of memory is your strongest?",
    options: {
      a: "Short-term is best",
      b: "Good general memory",
      c: "Long-term is good",
    },
  },
];
