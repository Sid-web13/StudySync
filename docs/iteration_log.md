# StudySync AI Prompt Engineering & LLM Architecture Iteration Log

**Project:** StudySync (SIH Problem Statement 26207: Smart Education)  
**Team:** Learnova (`PE-B25-24`)  
**AI Engine Target:** Google Gemini (`gemini-2.5-flash`) via `google-genai` SDK with Zero-Crash Offline Fallback  

---

## Evolution of Prompt Engineering & Output Sanitization

### Version 1.0: Naive Free-Form Generation
- **Prompt Formulation:**
  ```text
  You are an academic mentor. Make a quiz of 3 questions for {subject} on {topic}.
  Give 4 options for each question and tell which is correct.
  ```
- **Observed Failures:**
  1. **Unstructured Output:** The model returned markdown prose, numbering schemas ("1. A) B) C) D)"), and explanatory paragraphs before and after the quiz questions.
  2. **Parsing Impossibility:** Automated server-side grading could not parse options reliably using standard regex splits.
  3. **Option Prefix Bleeding:** Questions contained prefixes like `"A. 3NF"` which broke answer comparison if the student submitted `"3NF"`.
  4. **Chat Hallucination:** The mentor provided generic advice with no awareness of whether the student had actually studied the topic or had low quiz scores.

---

### Version 2.0: JSON Prompting with Direct Deserialization
- **Prompt Formulation:**
  ```text
  Generate a JSON array of 3 questions for {subject} on {topic}:
  [{"question_text": "...", "options": ["A", "B", "C", "D"], "correct_answer": "...", "explanation": "..."}]
  ```
- **Observed Failures:**
  1. **Markdown Fence Encapsulation:** Gemini returned JSON enclosed inside triple backticks:
     ````text
     ```json
     [ ... ]
     ```
     ````
  2. **JSONDecodeError:** Calling `json.loads(response.text)` triggered `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` because of the leading ```json token.
  3. **Chat Verbosity:** Mentor chat responses routinely exceeded 350+ words with discursive generic greetings, overwhelming college students seeking rapid revision pointers.

---

### Version 3.0: Regex Fence Stripping & Pydantic Schema Validation
- **Prompt Formulation:**
  ```text
  You are an expert college professor setting an exam for '{subject_name}' on '{topic_title}'.
  Return ONLY a raw JSON array matching:
  [
    {
      "question_text": "...",
      "options": ["...", "...", "...", "..."],
      "correct_answer": "...",
      "explanation": "..."
    }
  ]
  Do not include markdown code blocks.
  ```
- **Implementation Improvements:**
  - Added regex code fence sanitization:
    ```python
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE)
    cleaned = re.sub(r"```json|```", "", cleaned, flags=re.IGNORECASE).strip()
    ```
  - Added Pydantic `ValidatedQuestion` schema to ensure every question has exactly 4 options.
- **Observed Residual Edge Cases:**
  1. **Option Formatting Variance:** Despite negative constraints, Gemini occasionally returned options as `["A. First Normal Form", "B. Second Normal Form", ...]`, which caused answer comparison mismatches.
  2. **API Flakiness / Missing Key:** If deployed without a `GEMINI_API_KEY` or in an environment with proxy/network limitations, the entire quiz generation endpoint threw an unhandled exception.

---

### Version 4.0 (Production): Production-Ready Grounded Engine with Deterministic Fallbacks
- **Architecture Overview:**
  ```mermaid
  flowchart TD
      A[Student Requests Quiz / Chat] --> B{Gemini API Key & Network Available?}
      B -- Yes --> C[Invoke Gemini 2.5 Flash with Grounded Telemetry]
      C --> D[Regex Strip Markdown Code Fences]
      D --> E[Clean Option Prefixes A/B/C/D]
      E --> F{Pydantic Schema Validation}
      F -- Pass --> G[Persist in SQLite & Return Response]
      F -- Fail --> H[Deterministic Academic Fallback Engine]
      B -- No / Exception --> H
      H --> G
  ```
- **Key Enhancements Implemented in Production:**
  1. **Option Prefix Stripping:**
     ```python
     options = [re.sub(r"^[A-D]\s*[\.\:\-\)]\s*", "", opt).strip() for opt in item.get("options", [])]
     correct = re.sub(r"^[A-D]\s*[\.\:\-\)]\s*", "", item.get("correct_answer", "")).strip()
     ```
  2. **Anti-Cheat Response Projection:**
     Database stores `correct_answer` and `explanation`, but `QuizOut` schema strictly projects questions using `QuizQuestionOut` (omitting answers and explanations until after submission).
  3. **Strict Mentor Chat Constraints:**
     - Grounded with live SQLite telemetry (enrolled courses, weak topics, mean quiz score).
     - Mandates **bulleted output**.
     - Mandates **at least one concrete practical example** (e.g., schema decomposition or OS command).
     - Mandates active encouragement toward the **80% mastery threshold**.
     - Enforces `< 150 words` brevity limit via algorithmic word truncation:
       ```python
       def _enforce_word_limit(self, text: str, max_words: int = 148) -> str:
           words = text.split()
           if len(words) <= max_words:
               return text
           return " ".join(words[:max_words]) + "..."
       ```
  4. **Zero-Crash Deterministic Fallback Engine:**
     Curated question banks for DBMS, OS, Computer Networks, and generic academic topics that guarantee identical pedagogical quality and zero downtime even without an active internet connection or API key.
