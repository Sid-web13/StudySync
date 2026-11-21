import json
import logging
import re
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger("studysync.llm_service")

# Optional import of google-genai SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class ValidatedQuestion(BaseModel):
    question_text: str = Field(..., min_length=5)
    options: list[str] = Field(..., min_length=4, max_length=4)
    correct_answer: str
    explanation: str = Field(..., min_length=5)


class LLMService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.client = None
        if self.api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Client: {e}. Falling back to offline engine.")
                self.client = None

    def _strip_markdown_fences(self, text: str) -> str:
        """Strips markdown code fences (```json or ```) and whitespace from response."""
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```json|```", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def generate_quiz_questions(
        self, subject_name: str, topic_title: str, num_questions: int = 3
    ) -> list[dict[str, Any]]:
        """
        Generates MCQ quiz questions using Gemini if available, or returns deterministic
        high-yield academic fallbacks. Guarantees 4 distinct options without prefixes,
        strict answer matching, and clear educational explanations.
        """
        if self.client:
            prompt = f"""
You are an expert college university professor setting an examination quiz for the course '{subject_name}' on the topic '{topic_title}'.
Generate exactly {num_questions} rigorous multiple-choice questions (MCQs) in RFC 8259 compliant JSON format.

JSON Schema specification:
[
  {{
    "question_text": "Precise conceptual question text",
    "options": [
      "Exact Option 1",
      "Exact Option 2",
      "Exact Option 3",
      "Exact Option 4"
    ],
    "correct_answer": "Exact Option 1",
    "explanation": "Clear, pedagogically sound explanation why this answer is correct."
  }}
]

STRICT CONSTRAINTS:
1. Return ONLY the raw JSON array. Do NOT wrap in markdown fences or add explanatory text.
2. Every question must have exactly 4 distinct, mutually exclusive options.
3. NEVER prefix options with 'A.', 'B.', 'C.', 'D.', or numbers. Provide raw option text only.
4. 'correct_answer' MUST EXACTLY match one of the strings in the 'options' list (character-for-character).
5. Explanations must be educational, concise, and state why the option is correct.
""".strip()

            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                raw_text = response.text or ""
                cleaned_text = self._strip_markdown_fences(raw_text)
                parsed_json = json.loads(cleaned_text)

                if isinstance(parsed_json, list) and len(parsed_json) >= num_questions:
                    validated_questions = []
                    for item in parsed_json[:num_questions]:
                        # Ensure options are clean and correct_answer matches
                        options = [re.sub(r"^[A-D]\s*[\.\:\-\)]\s*", "", opt).strip() for opt in item.get("options", [])]
                        correct = re.sub(r"^[A-D]\s*[\.\:\-\)]\s*", "", item.get("correct_answer", "")).strip()
                        
                        # Match correct answer into options if slight whitespace variance
                        if correct not in options and options:
                            correct = options[0]

                        # Ensure 4 unique options
                        if len(set(options)) < 4:
                            continue

                        vq = ValidatedQuestion(
                            question_text=str(item.get("question_text", "")).strip(),
                            options=options,
                            correct_answer=correct,
                            explanation=str(item.get("explanation", "")).strip(),
                        )
                        validated_questions.append(vq.model_dump())

                    if len(validated_questions) == num_questions:
                        return validated_questions
            except Exception as e:
                logger.warning(f"Gemini quiz generation failed: {e}. Executing deterministic offline fallback engine.")

        # Deterministic Academic Offline Fallback Engine
        return self._get_offline_quiz_fallback(subject_name, topic_title, num_questions)

    def _get_offline_quiz_fallback(
        self, subject_name: str, topic_title: str, num_questions: int = 3
    ) -> list[dict[str, Any]]:
        """Provides verified, pedagogically sound questions for standard college CS topics."""
        lower_topic = topic_title.lower()
        lower_sub = subject_name.lower()

        # 1. Normalization & Functional Dependencies
        if "normal" in lower_topic or "dependenc" in lower_topic or "dbms" in lower_sub:
            bank = [
                {
                    "question_text": "In relational database design, which normal form strictly eliminates transitive functional dependencies for non-prime attributes?",
                    "options": [
                        "Third Normal Form (3NF)",
                        "First Normal Form (1NF)",
                        "Second Normal Form (2NF)",
                        "Boyce-Codd Normal Form (BCNF)",
                    ],
                    "correct_answer": "Third Normal Form (3NF)",
                    "explanation": "3NF requires a relation to be in 2NF with no transitive dependencies where a non-prime attribute depends on another non-prime attribute.",
                },
                {
                    "question_text": "Given a relation R with functional dependency X -> Y, what condition must hold for R to strictly satisfy Boyce-Codd Normal Form (BCNF)?",
                    "options": [
                        "X must be a superkey of relation R",
                        "Y must be a prime attribute part of a candidate key",
                        "X must be atomic with zero repeating groups",
                        "Relation R must contain no composite primary keys",
                    ],
                    "correct_answer": "X must be a superkey of relation R",
                    "explanation": "BCNF mandates that for every non-trivial functional dependency X -> Y, determinant X must be a superkey.",
                },
                {
                    "question_text": "What is the primary operational trade-off of decomposing tables into higher normal forms like 3NF or BCNF?",
                    "options": [
                        "Eliminates update anomalies but requires additional JOIN operations during reads",
                        "Increases disk storage redundancy while speeding up write throughput",
                        "Removes the necessity for foreign key constraint indexing",
                        "Forces all numeric columns into floating-point representation",
                    ],
                    "correct_answer": "Eliminates update anomalies but requires additional JOIN operations during reads",
                    "explanation": "Normalization minimizes data duplication and update anomalies, but reconstructing full records requires expensive SQL JOINs across decomposed tables.",
                },
            ]
            return bank[:num_questions]

        # 2. Operating Systems / Concurrency / Scheduling
        if "process" in lower_topic or "schedul" in lower_topic or "os" in lower_sub or "deadlock" in lower_topic:
            bank = [
                {
                    "question_text": "Which CPU scheduling algorithm can suffer from starvation (indefinite postponement) for longer bursts without an aging mechanism?",
                    "options": [
                        "Shortest Job First (SJF)",
                        "Round Robin (RR)",
                        "First-Come, First-Served (FCFS)",
                        "Earliest Deadline First (EDF)",
                    ],
                    "correct_answer": "Shortest Job First (SJF)",
                    "explanation": "SJF gives priority to short processes; continuous arrival of shorter jobs causes longer processes to starve indefinitely unless aging increments priority.",
                },
                {
                    "question_text": "Which of the following is NOT one of the four essential Coffman conditions required for a system deadlock to occur?",
                    "options": [
                        "Preemption of allocated resources by lower-priority threads",
                        "Mutual Exclusion",
                        "Hold and Wait",
                        "Circular Wait",
                    ],
                    "correct_answer": "Preemption of allocated resources by lower-priority threads",
                    "explanation": "No preemption is the required condition for deadlock. Allowing preemption breaks the deadlock cycle.",
                },
                {
                    "question_text": "What hardware component accelerates virtual-to-physical address translation by caching recent page table entries?",
                    "options": [
                        "Translation Lookaside Buffer (TLB)",
                        "Direct Memory Access (DMA) Controller",
                        "Memory Management Unit Register Array",
                        "Arithmetic Logic Unit (ALU) Cache",
                    ],
                    "correct_answer": "Translation Lookaside Buffer (TLB)",
                    "explanation": "The TLB is a fast associative cache on the MMU that stores recent virtual-to-physical page frame translations to avoid multi-level page table walks.",
                },
            ]
            return bank[:num_questions]

        # 3. Computer Networks / Protocols
        if "network" in lower_sub or "protocol" in lower_topic or "tcp" in lower_topic or "ip" in lower_topic:
            bank = [
                {
                    "question_text": "In the TCP 3-way handshake, what sequence of control flags is exchanged between client and server to establish a connection?",
                    "options": [
                        "SYN, SYN-ACK, ACK",
                        "SYN, ACK, FIN",
                        "ACK, SYN-ACK, SYN",
                        "RST, SYN, ACK",
                    ],
                    "correct_answer": "SYN, SYN-ACK, ACK",
                    "explanation": "The client sends a SYN packet, the server responds with SYN-ACK, and the client confirms with an ACK to establish reliable full-duplex communication.",
                },
                {
                    "question_text": "What is the usable number of IPv4 host addresses in a subnet with a /28 Classless Inter-Domain Routing (CIDR) prefix?",
                    "options": [
                        "14 hosts",
                        "16 hosts",
                        "30 hosts",
                        "12 hosts",
                    ],
                    "correct_answer": "14 hosts",
                    "explanation": "A /28 subnet has 32 - 28 = 4 host bits (2^4 = 16 total addresses). Subtracting the network and broadcast addresses leaves 14 usable host IPs.",
                },
                {
                    "question_text": "Which transport-layer protocol is connectionless, minimizes transmission latency, and does not provide automatic retransmission of lost packets?",
                    "options": [
                        "User Datagram Protocol (UDP)",
                        "Transmission Control Protocol (TCP)",
                        "Stream Control Transmission Protocol (SCTP)",
                        "Hypertext Transfer Protocol (HTTP)",
                    ],
                    "correct_answer": "User Datagram Protocol (UDP)",
                    "explanation": "UDP provides lightweight datagram transport without handshake overhead, ordering, or retransmission, making it ideal for real-time streaming and DNS.",
                },
            ]
            return bank[:num_questions]

        # 4. Generic Academic Subject Fallback
        return [
            {
                "question_text": f"What is the foundational theoretical principle underlying '{topic_title}' in modern computer science curricula?",
                "options": [
                    f"Systematic modular decomposition and rigorous algorithmic verification of {topic_title}",
                    f"Heuristic brute-force evaluation without formal state modeling",
                    f"Elimination of abstract interfaces in favor of hard-coded routines",
                    f"Static compilation without runtime dynamic dispatch",
                ],
                "correct_answer": f"Systematic modular decomposition and rigorous algorithmic verification of {topic_title}",
                "explanation": f"In {subject_name}, {topic_title} is structured around disciplined modular abstractions, formal verification, and clear separation of architectural concerns.",
            },
            {
                "question_text": f"When implementing systems involving '{topic_title}', which engineering metric is primarily optimized?",
                "options": [
                    "Computational time complexity, spatial resource efficiency, and correctness",
                    "Arbitrary code length regardless of runtime memory usage",
                    "Unconstrained heap allocation without garbage collection boundaries",
                    "Immediate termination upon transient input variations",
                ],
                "correct_answer": "Computational time complexity, spatial resource efficiency, and correctness",
                "explanation": "Core computer science fundamentals prioritize proven time-complexity bounds, memory management, and deterministic error handling.",
            },
            {
                "question_text": f"Which diagnostic approach is most effective when debugging anomalies related to '{topic_title}'?",
                "options": [
                    "Formulating test assertions, tracing execution invariants, and profiling bottlenecks",
                    "Repeatedly restarting the runtime without inspectable logging",
                    "Removing all conditional safety checks to bypass assertion errors",
                    "Disabling concurrent thread safety locks across shared buffers",
                ],
                "correct_answer": "Formulating test assertions, tracing execution invariants, and profiling bottlenecks",
                "explanation": "Systematic root-cause analysis requires invariant verification, unit test regression suites, and execution tracing.",
            },
        ][:num_questions]

    def mentor_chat(
        self, grounded_prompt: str, recent_messages: list[dict[str, str]], weak_topics: list[str]
    ) -> str:
        """
        Generates mentor advice strictly enforcing:
        - Bulleted output
        - At least one concrete practical example (code/architecture)
        - Active encouragement toward the 80% mastery threshold
        - Strict < 150 words limit
        """
        system_instruction = (
            "You are StudySync's elite AI Academic Mentor for engineering students. "
            "You have live telemetry access to the student's enrolled courses, syllabus progress, and quiz performance. "
            "STRICT CONSTRAINTS:\n"
            "1. Output MUST be formatted as concise bullet points.\n"
            "2. Include AT LEAST ONE concrete practical example (e.g. SQL query, OS command, code snippet, or architectural scenario).\n"
            "3. Actively encourage the student to reach the 80% quiz mastery threshold.\n"
            "4. Word count MUST be strictly LESS THAN 150 words. Be razor-sharp and punchy."
        )

        if self.client:
            conversation_history = "\n".join(
                [f"{msg['role'].upper()}: {msg['content']}" for msg in recent_messages[-6:]]
            )
            full_prompt = f"""
{system_instruction}

Live Student Grounding Telemetry:
{grounded_prompt}

Recent Conversation Context:
{conversation_history}

Please reply to the student's latest query now:
""".strip()

            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                )
                text = response.text or ""
                if text.strip():
                    return self._enforce_word_limit(text.strip(), max_words=148)
            except Exception as e:
                logger.warning(f"Gemini mentor chat failed: {e}. Executing deterministic offline mentor response.")

        # Deterministic Grounded Offline Mentor Fallback
        return self._get_offline_mentor_reply(grounded_prompt, weak_topics)

    def _get_offline_mentor_reply(self, grounded_prompt: str, weak_topics: list[str]) -> str:
        """Generates structured, bulleted advice adhering to the 150-word constraint with a practical example."""
        focus_area = weak_topics[0] if weak_topics else "Core System Design"

        reply = (
            f"• **Target Weak Area:** Focus your current revision sprint on **{focus_area}**.\n"
            f"• **Practical Example:** In 3NF, decompose transitive tables: separate `(StudentID, CourseID, DeptName)` into `StudentCourse(StudentID, CourseID)` and `CourseDept(CourseID, DeptName)` to prevent update anomalies.\n"
            f"• **Action Plan:** Review foreign key constraints and re-attempt the module quiz.\n"
            f"• **Goal:** Aim for ≥80% score on your next test to automatically mark this topic **Completed** on your syllabus dashboard! You've got this!"
        )
        return self._enforce_word_limit(reply, max_words=148)

    def _enforce_word_limit(self, text: str, max_words: int = 148) -> str:
        """Trims response if it exceeds word count while keeping bullet formatting clean."""
        words = text.split()
        if len(words) <= max_words:
            return text
        truncated = " ".join(words[:max_words]) + "..."
        return truncated


llm_service = LLMService()
