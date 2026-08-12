# Literature Review (Starter — Phase 1)

> Expand each entry to 8–12 lines in your own words for the black book.
> Minimum for Week 3: **5 works**. Target later: **10+**.

## 1. Playwright Test Agents (Planner / Generator / Healer) — Microsoft
**Source:** https://playwright.dev/docs/test-agents  
**Summary:** Official agentic pipeline that explores an app, writes Markdown plans, generates Playwright tests, and heals failing tests.  
**Relevance:** Closest industrial baseline to DS 1.  
**Gap we address:** Unified text-step execution + structured pass/fail docs + team failure notification in one academic/industry prototype.

## 2. Tricentis Testim
**Source:** https://www.testim.io/  
**Summary:** Commercial AI testing with smart locators / self-healing and NL-oriented authoring. Named in Dassault proposal.  
**Relevance:** Validates industry demand for less brittle UI automation.  
**Gap:** Closed product; we build an open, explainable executor with explicit report + notify modules.

## 3. Nass, Alégroth & Feldt (2024) — Improving Web Element Localization Using an LLM
**Source:** *Software Testing, Verification and Reliability*, DOI: 10.1002/stvr.1893  
**Summary:** LLMs can improve localization when traditional locators fail.  
**Relevance:** Supports AI mapping from intent/text to UI elements and recovery strategies.

## 4. Generative AI for Self-Healing Selenium Tests (ICECIT 2025)
**Source:** DOI: 10.1109/icecit67774.2025.11451150  
**Summary:** Compares open-source LLMs vs rule-based healing for broken Selenium locators.  
**Relevance:** Motivates optional self-heal module and evaluation metrics (repair success, overhead).

## 5. Self-Healing Automation with RL (PPO) + Dynamic XPath in Playwright (JAIGS 2025)
**Source:** DOI: 10.60087/jaigs.v5i1.341  
**Summary:** Reinforcement learning adapts selectors in Playwright when UI changes.  
**Relevance:** Alternate recovery approach (RL vs LLM vs heuristics) for literature comparison.

## 6. (Bonus baseline) Robula+ — Robust locator generation for web testing
**Summary:** Classic pre-AI method to generate more stable locators and reduce script breakage.  
**Relevance:** Historical baseline before agentic / LLM approaches.

## Research Gap (draft)
Existing work focuses on code generation, locator healing, or commercial NL testing.
Few academic prototypes combine:
1) plain-text step execution,
2) evidence-backed pass/fail documentation, and
3) scrum-style failure notification to owning teams
in one Quality Engineering workflow — this is our contribution.
