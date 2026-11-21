# StudySync -- Prompt Iteration Log

**Team Name:** Learnova\
**Team ID:** PE-B25-24\
**Problem Statement:** SIH 26207 -- Smart Education\
**Project:** StudySync -- Personalised Student Academic Mentorship
Platform

## Purpose

This log documents the prompt-refinement sequences explicitly described
in the supplied StudySync prompts:

1.  Quiz Generator: P09 → P10 → P11 → P12
2.  AI Academic Mentor: P15 → P16 → P17 → P18

The tables use the five requested columns: **Version**, **Initial Prompt
/ Change**, **Problem Identified**, **Improvement Made**, and
**Result**.

> **Evidence note:** The results below describe the intended or
> specified technical outcome of each prompt. Attach actual model-output
> screenshots, code evidence and application tests to substantiate
> observed results. Do not present an expected result as a measured
> result unless it was verified during development.

------------------------------------------------------------------------

## Experiment 1: AI Quiz Generator

**Objective:** Improve the structure, consistency and reliability of
AI-generated practice questions.

  ------------------------------------------------------------------------------------------------------
  Version        Initial Prompt / Change         Problem           Improvement Made   Result
                                                 Identified                           
  -------------- ------------------------------- ----------------- ------------------ ------------------
  V1 --          Asked the model to generate a   The requested     Established a      Provides a basic
  Zero-Shot      three-question practice quiz on baseline output   baseline prompt    quiz-generation
  Baseline       "Functional Dependencies &      was plain text.   and identified the baseline, but
                 Normalization" in DBMS using a  Such output is    need for a         plain text is not
                 simple instruction.             difficult to      machine-readable   suitable for
                                                 extract reliably  response format.   direct automated
                                                 into application                     processing without
                                                 fields such as                       additional
                                                 question text,                       handling.
                                                 options and                          
                                                 correct answer.                      

  V2 -- Role &   Added the role of an expert     The model may     Added role         Produces more
  Schema Request university professor, specified wrap JSON in      prompting and an   task-specific and
                 the subject and topic,          Markdown code     explicit JSON      structured output,
                 requested three MCQs, and asked fences or add     output request.    but formatting may
                 for a JSON list containing      conversational                       still require
                 question text, options and      text, which can                      validation and
                 correct answer.                 prevent direct                       cleanup.
                                                 JSON parsing.                        

  V3 -- Strict   Required a strict JSON array    A loosely         Added explicit     Defines a more
  Schema &       with the keys `question_text`,  specified JSON    schema             predictable,
  Negative       `question_type`, `options`,     request may still requirements and   machine-readable
  Constraints    `correct_answer` and            produce           negative           output contract
                 `explanation`. Required four    inconsistent      constraints to     for quiz
                 option strings and an           keys, option      reduce ambiguity   generation.
                 exact-match answer; prohibited  counts or extra   in the expected    
                 Markdown fences, comments and   text, causing     output.            
                 conversational text.            parsing or                           
                                                 validation                           
                                                 problems.                            

  V4 --          Implemented the refined quiz    API               Added output       Makes the
  Resilient LLM  prompt in                       unavailability,   cleanup, parsing   quiz-generation
  Service &      `app/services/llm_service.py`   missing API       and a              service more
  Fallback       using Google Gemini             configuration or  deterministic      resilient and
                 (`gemini-2.5-flash`) and the    accidental        fallback path for  supports continued
                 Google GenAI SDK. Added         formatting issues offline testing or prototype testing
                 regex-based Markdown-fence      could interrupt   when an API key is when the external
                 cleanup, JSON parsing and       quiz generation.  not configured.    AI service is
                 deterministic fallback                                               unavailable.
                 questions.                                                           
  ------------------------------------------------------------------------------------------------------

### Quiz Generator -- Iteration Outcome

The quiz-generation sequence progresses from a basic zero-shot
instruction to a structured generation pipeline. Role prompting
clarifies the model's task, strict schema constraints define the
expected output, and the service-layer fallback and parsing logic
address integration reliability.

------------------------------------------------------------------------

## Experiment 2: AI Academic Mentor

**Objective:** Transform a generic question-answering prompt into a
personalized, context-aware academic mentoring prompt.

  -------------------------------------------------------------------------------------------
  Version        Initial Prompt /   Problem          Improvement Made      Result
                 Change             Identified                             
  -------------- ------------------ ---------------- --------------------- ------------------
  V1 --          Asked the model:   A generic        Established a         Provides a general
  Zero-Shot      "What should I     response may     baseline prompt and   academic response,
  Baseline       revise for my      provide          identified the need   but does not
                 upcoming exam in   textbook-style   for student-specific  establish
                 DBMS?"             revision advice  context.              individualized
                                    without                                revision
                                    considering the                        priorities.
                                    student's                              
                                    course, enrolled                       
                                    subjects or                            
                                    individual                             
                                    academic                               
                                    progress.                              

  V2 -- Persona  Introduced the     Static profile   Added role-based      Makes the prompt
  & Student      "StudySync Mentor" information does instructions and      more relevant to
  Scoping        persona and        not show which   student-specific      the student's
                 supplied the       topics the       academic profile      academic profile,
                 student's name,    student has      information.          but does not yet
                 B.Tech Computer    completed or                           incorporate
                 Science course and where the                              assessment
                 enrolled subjects: student has                            history.
                 DBMS, Operating    performed poorly                       
                 Systems and        in assessments.                        
                 Computer Networks.                                        

  V3 -- Dynamic  Extended the       A static student Added dynamic         Enables the mentor
  Assessment     prompt using       profile cannot   database queries to   prompt to include
  Telemetry      database-derived   reflect current  retrieve academic and current syllabus
                 information:       syllabus         assessment context    progress and
                 enrolled subjects  progress or      before constructing   identified weak
                 and course codes,  identify         the mentor prompt.    topics when that
                 completed topics   knowledge gaps                         data is available.
                 versus total       from quiz                              
                 topics, and weak   performance.                           
                 topics with recent                                        
                 quiz scores below                                         
                 70%.                                                      

  V4 -- Concise  Added rules to     Even with        Added explicit        Defines a concise,
  Actionable     ground             student and      response-structure,   structured and
  Standard       explanations in    assessment       conciseness and       context-grounded
                 the student's      context,         actionability         response standard
                 enrolled syllabus, responses may be constraints.          for the StudySync
                 provide targeted   too lengthy or                         Mentor.
                 encouragement and  insufficiently                         
                 revision tips for  actionable for                         
                 weak topics, use   quick academic                         
                 concise bullet     guidance.                              
                 points and                                                
                 practical                                                 
                 examples, and stay                                        
                 strictly below 150                                        
                 words.                                                    
  -------------------------------------------------------------------------------------------

### AI Academic Mentor -- Iteration Outcome

The mentor prompt progresses through four stages: generic question
answering, persona and student profiling, dynamic academic-context
injection, and concise actionable guidance. The final prompt is designed
to use the student's syllabus and assessment information to make its
guidance more relevant.

------------------------------------------------------------------------

## Evidence to Attach

Attach actual evidence alongside or immediately after the relevant
experiment tables.

  -----------------------------------------------------------------------
  Evidence ID             Evidence Required       Related Prompt(s)
  ----------------------- ----------------------- -----------------------
  E01                     Initial zero-shot quiz  P09
                          prompt and its raw      
                          output                  

  E02                     Role-based quiz prompt  P10
                          and generated output    

  E03                     Strict JSON prompt and  P11
                          generated output        

  E04                     Gemini service          P12
                          implementation, JSON    
                          cleanup and fallback    
                          logic                   

  E05                     Baseline mentor prompt  P15
                          and generic response    

  E06                     Personalized mentor     P16
                          prompt and its response 

  E07                     Code or screenshot      P17
                          showing dynamic         
                          academic-context        
                          construction            

  E08                     Final mentor prompt and P18
                          its grounded response   

  E09                     Actual StudySync        Development evidence
                          application Version 1   
                          screenshot              

  E10                     Actual StudySync        Development evidence
                          application Version 2   
                          screenshot              

  E11                     Actual StudySync        Development evidence
                          application Version 3   
                          screenshot              
  -----------------------------------------------------------------------

## Important Distinction: Prompt Versions and Application Versions

The four versions in the two experiment tables refer to **prompt
iterations**, not necessarily four releases of the StudySync
application.

The supplied project description mentions three application versions. If
screenshots of those versions are available, include them separately as
application-development evidence (E09--E11). Do not label them V1--V4 in
the prompt iteration tables unless the application itself was actually
released in four versions.

## Overall Conclusion

The prompt iteration process demonstrates how prompt instructions were
refined to address two key AI features in StudySync. The Quiz Generator
sequence focuses on structured, machine-readable output and resilient
integration. The AI Academic Mentor sequence focuses on personalization,
dynamic academic context and actionable responses.

Together, these experiments document the progression from baseline
prompts to more explicitly constrained prompts and supporting
application logic.
