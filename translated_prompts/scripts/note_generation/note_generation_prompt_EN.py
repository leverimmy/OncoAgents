EDUCATION_LEVELS = [
    "Primary school or below: Limited literacy / limited understanding of medical terminology",
    "Middle school: Can understand everyday explanations, needs to avoid complex concepts",
    "High school / vocational: Can follow basic cause-and-effect explanations, willing to hear conclusions",
    "Undergraduate: Can understand risk probabilities and treatment plan comparisons",
    "Graduate / medical background: Will ask about evidence levels and guideline sources",
]

FINANCIAL_STATUSES = [
    "Difficult: Significant financial pressure from treatment costs, tends to choose low-cost options",
    "Below average: Relies on health insurance, concerned about coverage scope and limits",
    "Average: Has insurance but sensitive to out-of-pocket costs, can afford standard treatment",
    "Above average: Willing to pay for efficacy/comfort, values experience and efficiency",
    "Well-off: Cost is not a major constraint, prioritizes best options/expert resources",
]

PERSONALITIES = [
    "Impatient: Easily angered, easily agitated, lacks patience",
    "Overly anxious: Always worried and tense, difficulty relaxing",
    "Overly optimistic: Ignores risks, overly confident in treatment outcomes",
    "Distrustful: Skeptical of the medical system or doctors",
    "Verbose: Likes to discuss in detail, difficulty staying on topic",
    "Neutral: Emotionally stable, easy to communicate with",
]

COMMUNICATION_STYLES = [
    "Question-driven: Likes to ask questions, seeks answers to specific questions",
    "Information-gathering: Likes to obtain a lot of background information and details",
    "Emotion-expressive: Tends to express own feelings and emotions",
    "Silently compliant: Responds passively, rarely expresses own thoughts",
    "Calm and rational: Maintains calmness and rationality throughout communication, unaffected by emotions",
]

EDU_MAP = {
    "Primary school or below": 0,
    "Middle school": 1,
    "High school / vocational": 2,
    "Undergraduate / associate": 3,
    "Graduate and above": 4,
}

FIN_MAP = {
    "Difficult: Significant financial pressure from treatment costs, tends to choose low-cost options": 0,
    "Below average: Relies on health insurance, concerned about coverage scope and limits": 1,
    "Average: Has insurance but sensitive to out-of-pocket costs, can afford standard treatment": 2,
    "Above average: Willing to pay for efficacy/comfort, values experience and efficiency": 3,
    "Well-off: Cost is not a major constraint, prioritizes best options/expert resources": 4,
}

PER_MAP = {
    "impatient": 0,
    "anxious": 1,
    "over_optimistic": 2,
    "distrustful": 3,
    "verbose": 4,
    "neutral": 5,
}

COM_MAP = {
    "Doctor directly answers my main questions, keep it simple and clear": 0,
    "Doctor first explains the situation, causes, and available options, then I decide": 1,
    "I want to express my worries and fears first, then discuss the condition": 2,
    "I prefer the doctor to take the lead, I'll follow the doctor's arrangement": 3,
    "I want the doctor to use test results, data, and reasoning to explain pros and cons clearly": 4,
}


QUESTIONAIRE_INPUT = """Print/Export Questionnaire
Add | Common notes settings | Batch export notes
Serial number: 14 | Filled at: 2026/4/1 16:25:50 | Source IP: 117.176.120.241 (Sichuan - Chengdu) | Source channel: WeChat | Total score: 25 (average: 3.125) (?)
Q1:  xxx
Q2:  25
Q3:  Middle school
Q4:  Below average: Relies on health insurance, concerned about coverage scope and limits
Q5:  Strongly disagree (score 1)
Q6:  Agree (score 4)
Q7:  Neutral (score 3)
Q8:  Agree (score 4)
Q9:  Disagree (score 2)
Q10:  Strongly agree (score 5)
Q11:  Strongly disagree (score 1)
Q12:  Strongly agree (score 5)
Q13:  I prefer the doctor to take the lead, I'll follow the doctor's arrangement
"""

PATIENT_CASE = """PLACEHOLDER
"""

PROMPT_1 = """
You are a professional oncology medical record information extraction and structuring expert. Your task is to: **based solely on the provided medical record text**, extract key patient information and output it in the specified JSON format.

## Medical Record Text
{patient_case_text}

--------------------------------
[General Principles]
--------------------------------
1. You must only base your answers on the medical record text. **Do not fabricate, do not supplement with common knowledge inferences, do not make assumptions.**
2. All field content should preferably retain the original wording, with moderate removal of extra whitespace, line breaks, and obvious redundancy.
3. All output content should be in the same language as the source (JSON key names excepted, key names must strictly follow the specified format).
4. If a field is clearly missing or cannot be determined from the original text:
   - String fields: fill with "Unknown" or "" as specified per field below;
   - List fields: fill with `[]`;
   - Numeric fields: if cannot be determined, fill with `null`.
5. Do not output markdown, do not output explanations, do not output comments, do not output any text outside the JSON.
6. If the same information appears in different locations with conflicting values:
   - Prioritize the version from **confirmed diagnosis, examination conclusions, discharge diagnosis, or pathology results**;
   - If still conflicting, adopt the **more recent, more complete, more specific** version.
7. You should strive for completeness, but **it is better to leave a field missing than to fabricate information**.

--------------------------------
[Extraction Targets and Field Rules]
--------------------------------

You must output the following JSON structure:

{{
  "personal_info": {{
    "demographics": {{
      "name": "Full name",
      "gender": "Gender",
      "age": "Age"
    }},
    "personal_history": {{
      "smoking_status": "Smoking history",
      "alcohol_use": "Alcohol use history",
      "family_history": "Family history",
      "marriage_childbearing_history": "Marriage and childbearing history"
    }}
  }},
  "symptom": {{
    "chief_complaint": "Chief complaint",
    "additional_symptom": "Additional symptoms",
    "symptom_duration": "Symptom duration"
  }},
  "physical_examination": {{
    "basic_info": "Vital signs/scores and other basic information",
    "general_condition": "General physical examination",
    "special_examination": "Specialist examination"
  }},
  "auxiliary_examination": [
    {{
      "check_type": "Examination type",
      "item": "Examination item/body site/specimen",
      "result": "Examination result"
    }}
  ],
  "diagnosis": {{
    "disease_name": "Disease name",
    "stage": "Staging information",
    "complication": "Complications/comorbidities",
    "stage_1234": int
  }},
  "treatment": {{
    "plan": "Treatment plan",
    "course": "Treatment course/cycle"
  }}
}}

--------------------------------
[Detailed Extraction Rules for Each Field]
--------------------------------

### 1. personal_info.demographics

#### 1.1 name
- Extract the patient's name.
- Prioritize extracting from "Name", "Patient", "General Information", etc.
- If not present, fill with "Unknown".

#### 1.2 gender
- Extract gender, such as "Male" or "Female".
- If not present, fill with "Unknown".

#### 1.3 age
- Extract age, try to preserve the original format, such as "50 years old", "67 years old".
- If the original text only has a numeric age, you may add "years old".
- If not present, fill with "Unknown".

### 2. personal_info.personal_history

#### 2.1 smoking_status
- Extract smoking-related descriptions, try to preserve duration, frequency, whether they have quit, etc.
- E.g., "Smoking for 30 years, 20 cigarettes/day, quit 5 years ago", "Denies smoking history".
- If not mentioned, fill with "Unknown".

#### 2.2 alcohol_use
- Extract alcohol-related descriptions, try to preserve duration, frequency, whether they have quit, etc.
- E.g., "Alcohol consumption for over 20 years", "Denies alcohol history".
- If not mentioned, fill with "Unknown".

#### 2.3 family_history
- Extract family history, prioritizing descriptions related to tumors, genetic diseases, and infectious diseases from the original text.
- Can directly retain the original text, e.g., "Denies family history of infectious diseases, hereditary diseases, or tumors."
- If not mentioned, fill with "Unknown".

#### 2.4 marriage_childbearing_history
- Extract marriage and childbearing history, e.g., "Married, has 1 son", "Married at typical age", "Unmarried, no children", etc.
- If not mentioned, fill with "Unknown".

### 3. symptom

#### 3.1 chief_complaint
- Prioritize extracting the complete content after "Chief complaint:".
- If there is no explicit "Chief complaint", summarize the primary reason for the visit from the first sentence of the present illness history, but do not fabricate.
- If cannot be determined, fill with "Unknown".

#### 3.2 additional_symptom
- Extract important positive symptoms and important negative symptoms beyond the chief complaint.
- E.g., nausea, vomiting, diarrhea, fatigue, blood in stool, no fever, no chest pain, etc.
- Connect with semicolons, try to preserve original wording.
- If not mentioned, fill with "Unknown".

#### 3.3 symptom_duration
- Extract the duration most directly related to the chief complaint, such as "over half a year", "over 1 month", "3 days", etc.
- Preserve the original wording, do not convert.
- If cannot be determined, fill with "Unknown".

### 4. physical_examination

#### 4.1 basic_info
- Extract vital signs, height and weight, body surface area, scoring information, and other basic objective information.
- E.g., temperature, pulse, respiration, blood pressure, height, weight, Barthel score, KPS score, NRS2002 score, etc.
- Try to consolidate into a single string, preserving key values and units.
- If not mentioned, fill with "Unknown".

#### 4.2 general_condition
- Extract general examination and systemic physical examination content.
- Includes developmental nutrition, consciousness state, skin and mucous membranes, lymph nodes, head and neck, chest and abdomen, cardiopulmonary, extremities and nervous system, etc.
- Try to preserve original text.
- If not mentioned, fill with "Unknown".

#### 4.3 special_examination
- Extract specialist examination content.
- Common examples include digital rectal examination, gynecological examination, ENT specialist examination, neurological specialist examination, etc.
- If there is no clear specialist examination but there is a "specialist findings as follows" section, it should be placed in this field.
- If not mentioned, fill with "Unknown".

### 5. auxiliary_examination

- Extract all clearly identified auxiliary examinations, output as a list in the order they appear in the original text.
- Each examination item must include:
  - check_type: Examination type
  - item: Examination item/body site/specimen
  - result: Result description

#### 5.1 check_type standardization suggestions
- Laboratory tests
- CT / Contrast-enhanced CT
- MRI
- PET-CT
- Ultrasound
- X-ray
- Bone scan
- Pathology
- Immunohistochemistry
- Genetic testing
- Electrocardiogram (ECG)
- Echocardiogram / Cardiac ultrasound
- Renal dynamic imaging
- Other examination types explicitly stated in the original text

#### 5.2 item
- Extract the examination body site, item name, or specimen source.
- E.g., "chest", "abdomen", "rectal biopsy tissue", "complete blood count", "bilateral kidneys", "heart", etc.
- If no specific site/item, can fill with "".

#### 5.3 result
- Extract the corresponding examination results, try to preserve original judgment words such as "suggests", "consistent with", "possible", "no significant abnormality found", etc.
- Can moderately clean up line breaks and whitespace.
- If no result, fill with "".

#### 5.4 Important rules
- Only extract examinations that are clearly present in the original text.
- Do not treat "diagnosis" itself as an auxiliary examination.
- Do not miss key items such as pathology, immunohistochemistry, genetic testing, complete blood count, etc.
- If the same examination item has information scattered across multiple locations, it can be merged.

### 6. diagnosis

#### 6.1 disease_name
- Extract the primary disease name.
- E.g., "Middle and lower rectal adenocarcinoma", "Right lung adenocarcinoma", "Gastric cancer", "Breast invasive ductal carcinoma", etc.
- If there are multiple concurrent primary diagnoses, connect with semicolons.
- If cannot be determined, fill with "Unknown".

#### 6.2 stage
- Extract explicit staging information.
- Includes TNM staging, clinical staging, pathological staging, MRF, EMVI, and other key staging/risk stratification information directly given in the original text.
- E.g., "cT4N2M0 MRF+", "Stage IIIA", "pT2N0M0".
- Do not infer staging that is not explicitly stated.
- If not mentioned, fill with "".

#### 6.3 complication
- Extract complications, comorbidities, and important clinical issues closely related to the tumor.
- E.g., "Tumor-related anemia", "Intestinal obstruction", "Pulmonary infection", etc.
- Connect multiple entries with semicolons.
- If not mentioned, fill with "".

#### 6.4 stage_1234
- Output the Arabic numeral corresponding to the overall stage: 1, 2, 3, or 4.
- Prioritize extracting from explicit statements in the original text such as "Stage I/Stage II/Stage III/Stage IV".
- If the original text does not directly state the overall stage, but the standard overall stage can be directly determined from the explicit diagnostic conclusions, fill in the corresponding number.
- If cannot be reliably determined, fill in the most likely number.
- Must output only the numbers 1, 2, 3, or 4; do not output strings.

### 7. treatment

#### 7.1 plan
- Extract the current/initial explicitly stated treatment plan.
- If it is chemotherapy, targeted therapy, immunotherapy, radiotherapy, surgery, concurrent chemoradiotherapy, etc., try to preserve key information such as drug names, dosages, administration methods, schedules, etc.
- Examples:
  - "Oxaliplatin 200mg IV drip d1 + Capecitabine 1500mg PO BID d1-14"
  - "Underwent laparoscopic radical resection of rectal cancer"
- If not mentioned, fill with "".

#### 7.2 course
- Extract treatment cycles, frequency, total number of cycles, etc.
- Express in natural language, such as:
  - "Once every 3 weeks, 1 cycle total"
  - "Repeat every 21 days"
  - "6 cycles total"
  - "Twice daily"
- If the original text only has abbreviations like d1-14, BID, q3w, etc., convert to natural language; but do not change the medical meaning.
- If cannot be determined, fill with "".

--------------------------------
[Output Requirements]
--------------------------------
Please strictly output valid JSON and must meet the following requirements:
1. Do not output markdown code blocks
2. Do not output explanatory text
3. Do not output extra prefixes or suffixes
4. Ensure the JSON can be directly parsed
5. Key names must exactly match the specified format

Please directly output the final JSON.
"""

PROMPT_2 = """


"""

PROMPT_3 = """
You are an "Oncology Bad News Communication Analysis Assistant."

You will receive 5 simulated dialogue JSONs for the same patient under the same communication task. Each JSON may contain:
- patient_data: Patient profile including education level, financial situation, personality, communication style, etc.
- examination_data: Examinations, diagnosis, staging, treatment plan, etc.
- conversation_history: Multi-turn doctor-patient dialogue
- scores / patient_scores: Scores such as CCS, EWS, APS, etc., that change across turns

[Task Objective]
Based on these simulated dialogues, distill a set of communication key points for a "bad news disclosure in oncology settings" for a real clinical doctor, focusing on:
1. Key questions the patient is highly likely to ask or follow up on
2. Most useful communication key points for the doctor
3. Ready-to-use phrases the doctor can use on the spot

Core requirements:
- This is not a restatement of the medical record
- This is not a mechanical summary of the persona
- Rather, it combines "static profile + dynamic performance across multi-turn interactions" to distill communication insights that are truly useful and actionable for the doctor

--------------------------------
[Analysis Principles]
1. Must reference both types of information:
   - Static profile: education, finances, personality, communication style, etc.
   - Dynamic performance: the patient's follow-up questions, emotional changes, understanding changes, compliance changes during the dialogue
2. Do not summarize each of the 5 dialogues individually; synthesize across dialogues, prioritizing "the most consistently appearing patterns."
3. If CCS / EWS / APS scores are available, use them as trend evidence:
   - What type of doctor response is more likely to improve understanding?
   - What type of response is more likely to stabilize emotions?
   - What type of response is more likely to advance cooperation?
   But do not mechanically list scores in the output.
4. Output must be clinically oriented: short, precise, specific, actionable.
5. All conclusions should be based on the provided dialogues as much as possible; if evidence is insufficient, do not over-speculate.
6. The output focus should be "what the doctor should say next to be more effective," not "cover all information."

--------------------------------
[What You Need to Output]

I. High-Probability Question List (5 items)
Each item must include two parts:
- category: Category/direction, keep it short, 4-8 words
- utterance: The specific phrase the patient might say, as close to a real speaking style as possible

Suggested category directions to prioritize:
- Severity
- Survival/prognosis
- Treatment details
- Risks/side effects
- Cost/burden
- Next steps
- Tolerance/feasibility
But do not mechanically apply these; use the most consistently appearing and most critical questions from the dialogues.

Example style (for reference only, do not copy):
[Severity] "What exactly is my disease? Is it very serious?"
[Survival] "Will this disease kill me? How long do I have? Tell me the truth."
[Treatment details] "How exactly does chemotherapy work? How often do I come? How long will this take?"
[Risks] "Are the side effects bad? Can my body handle it?"
[Cost] "How much does one cycle cost roughly? Can I afford it after insurance? Can it be cheaper?"

II. Communication Key Points (3 items)
Please output the following three fixed fields:

1. communication_strategy
- "How to make this patient receptive to what's being said"
- Synthesize based on the profile and dynamic performance in the conversations
- Emphasize how the doctor should organize information, control pace, and respond to questions

2. emotional_stabilization
- "How to more easily stabilize the patient's emotions"
- Emphasize specific actions, not abstract principles
- E.g., acknowledge emotions first, answer the most practical question first, deliver information in segments, pause after explaining, etc.
- But base this on the patterns observed in this set of dialogues

3. red_flag
- "The most important pitfall to avoid"
- Refers to statements or approaches most likely to make the patient panic, get frustrated, lose trust, become unreceptive, or repeatedly ask the same questions
- Must be specific, do not write vague principles

III. Ready-to-Use Phrases (5 sentences)
- Provide 5 sentences the doctor can use directly
- Language must be short, natural, like something a doctor would actually say
- Prioritize covering:
  - Acknowledging emotions
  - Responding to practical concerns (costs / side effects / tolerance / feasibility)
  - Wrapping up with next steps
- These sentences must be consistent with the "Communication Key Points" above, not contradictory

--------------------------------
[Output Format Requirements]
Please strictly output as JSON. The top-level object may only contain the following 3 keys:
- "likely_questions"
- "keypoints"
- "ready_to_use_lines"

Format as follows:

{{
  "likely_questions": [
    {{
      "category": "...",
      "utterance": "..."
    }},
    {{
      "category": "...",
      "utterance": "..."
    }},
    {{
      "category": "...",
      "utterance": "..."
    }},
    {{
      "category": "...",
      "utterance": "..."
    }},
    {{
      "category": "...",
      "utterance": "..."
    }}
  ],
  "keypoints": {{
    "communication_strategy": "...",
    "emotional_stabilization": "...",
    "red_flag": "..."
  }},
  "ready_to_use_lines": [
    "...",
    "...",
    "...",
    "...",
    "..."
  ]
}}

--------------------------------
[Hard Requirements]
1. Must output valid JSON, do not output markdown, do not add code blocks, do not add explanatory text.
2. "likely_questions" must have exactly 5 items.
3. "ready_to_use_lines" must have exactly 5 items.
4. "keypoints" must contain exactly 3 keys:
   - "communication_strategy"
   - "emotional_stabilization"
   - "red_flag"
5. Question sentences must sound like what a patient would actually say, not like a doctor's summary.
6. Keypoints must be specific and actionable; avoid empty phrases like "improve communication" or "show empathy."
7. Do not restate too many diagnostic and treatment details unless they directly affect the communication strategy.
8. If there are differences across multiple dialogues, prioritize summarizing "the most consistently appearing patterns."

Below are multiple simulated dialogue JSONs:
{cases_json}
""".strip()

REITERATE_PROMPT = """Imagine you are a patient describing your discomfort to a doctor. The doctor wants you to describe your symptoms in your own words to help them understand.

Based on the information provided below, restate your symptoms in a way that **matches your own cognitive level and expression habits**, to help the doctor understand "where it hurts, how it hurts, and how long it's been going on."

## Symptom Information (facts, do not change the meaning)

- Chief complaint (primary discomfort): {chief_complaint}
- Other accompanying symptoms: {additional_symptom}
- Symptom duration: {symptom_duration}

## Your Education Level

Your education level is: {education_level}

Please **strictly adjust your expression based on your education level**:

- Lower education level:
  - Use everyday language
  - Sentences can be incomplete
  - Do not use medical terminology
  - Can show some confusion or uncertainty

- Medium education level:
  - Can describe symptom changes and general feelings
  - Use simple, colloquial explanations
  - Avoid complex concepts

- Higher education level:
  - Expression is relatively clear and organized
  - May use a small number of common medical terms
  - But still maintain the tone of "a patient describing their own experience"

## Output Requirements

- Describe in **first person as the patient** (e.g., "Lately I've been...")
- Do not summarize, analyze, or draw conclusions
- Do not explain causes like a doctor would
- Just "restating symptoms"
- Output 1-3 sentences, natural and conversational

Now, please restate your symptoms as a patient:
"""
