---
name: create-tutorial 
description: Use this skill to generate a comprehensive, textbook-style technical tutorial for a newly implemented or modified software component.
argument-hint: "[topic of tutorial]"
metadata: 
  author: "Martin Saerbeck"
  version: "0.1"
effort: high
---

# Create a Technical Tutorial

Create a technical tutorial for $ARGUMENTS 

A technical tutorial serves as:
- A long-term knowledge artifact for developers
- A validation layer ensuring implementation aligns with intent and requirements
- A structured reference for both human engineers and LLM agents

The tutorial must be **self-contained**, requiring no external context to understand the system.

---

## Inputs & Assumptions

Before generating the tutorial:
- Use all available context (code, APIs, comments, architecture, requirements)
- If critical information is missing, explicitly state assumptions
- Infer design intent where necessary, but clearly label inferred vs explicit behavior

---

## Output Requirements

Write a **textbook-style technical tutorial** with the following structure:

### 1. Introduction
- Problem the software solves
- Motivation and use cases
- Design philosophy and guiding principles
- Constraints and tradeoffs

### Prerequisites
- What should the reader already know
- What must be installed
- Necessary and available configuration 

### 2. System Architecture
- High-level architecture overview
- Role of this component within the system
- Interaction with other components
- Data flow and control flow

### 3. Core Concepts
- Key abstractions and mental models
- Terminology definitions
- Important invariants
- Relevant fix points 

### 4. API and Functional Overview
For each major API / function:
- Purpose
- Inputs / outputs
- Preconditions / postconditions
- Side effects
- Error handling behavior

### 5. Worked Examples
- Realistic multiple usage scenarios covering distinct domains
- Step-by-step walkthroughs
- Include edge cases and failure modes

### 6. Implementation Insights
- Key algorithms and data structures
- Complexity analysis (time/space where relevant)
- Design tradeoffs vs alternative approaches
- Deviations from standard practices (if any)

### 7. Comparative Analysis
- How this approach compares to common patterns or libraries
- Strengths and weaknesses
- When NOT to use this component

### 8. Integration Guidance
- How other components/layers should interface with this
- Extension points and customization
- Common integration pitfalls

### 9. Outlook
- Future improvements or scalability considerations
- Potential evolution of the component

### 10. Testing Strategy
- Unit tests
- Integration tests
- Edge cases covered

---

## Style Guidelines

- Write for **senior developers and LLM agents**
- Be precise, not verbose
- Prefer clarity and being explicit to minimise ambiguity
- Prefer explicit descriptions over implicit assumptions
- Avoid ambiguous references like "this" or "that"
- Use consistent terminology
- Use markdown formatting:
  - headings
  - bullet points
  - code blocks for examples
- Avoid vague language like “simple” or “easy”
- Include ASCII or mermaid diagrams where helpful

---

## Saving the Tutorial

- Save as a markdown file in: `doc/tutorials/`
- File name rules:
  - Use concise, kebab-case naming
  - Reflect the main component or feature
  - Example: `event-stream-processor.md`
- If a filename is explicitly provided, use it
- Ensure the directory exists (create if necessary)
- Overwrite existing file with the same name

---

