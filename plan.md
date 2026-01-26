# Implementation Plan: Ralph Loop Enhancements

Enhancing the `Gemini_Tasks` extension by incorporating high-efficiency patterns from the "Ralph Wiggum" philosophy.

## 🎯 Objectives
*   **Precision**: Move from fuzzy string matching to strict XML-tagged completion promises.
*   **Efficiency**: Implement context clearing to prevent performance degradation over long runs.
*   **Resilience**: Ensure the agent always knows its original objective, even if memory is reset.
*   **Transparency**: Create a granular audit trail of autonomous iterations.

## 🛠️ Detailed Tasks

### 1. Robust Completion Signaling
- [x] **XML Promise Tags**: Update `after_agent.py` to search for `<promise>...</promise>` tags using case-insensitive regex.
- [x] **State Validation**: If tags are present but the content doesn't match `COMPLETION_PROMISE`, treat as a "false promise" and block.
- [x] **Documentation**: Update `README.md` and tool descriptions to instruct the AI to use the XML format.

### 2. Memory & Context Management
- [x] **Context Clearing**: Update the hook response to include `hookSpecificOutput: { clearContext: true }` when a loop iteration continues.
- [x] **Prompt Re-injection**: When clearing context, the `reason` provided in the hook MUST contain the `original_prompt` to ensure the agent doesn't lose its goal.
- [ ] **Token Monitoring**: (Optional) Log iteration token counts to verify the benefit of clearing context.

### 3. State Persistence Enhancements
- [x] **Bootstrap Objective**: Update the state schema to include `original_prompt`.
- [x] **Granular Logging**: Implement `.gemini/ralph-iterations.log`.
- [x] **Error Context**: Pipe verification failures into the AI's reason field.
- [x] **Custom Commands**:
    - [x] Implement `/ralph-start "Objective"` to bootstrap a session and record the goal.
    - [x] Implement `/ralph-cancel` to stop the current loop and clear state.

### 4. Codebase & Hook Refactoring
- [x] **Logic Separation**: Abstracted decision logic into `deny_with_context` and specialized helpers.
- [x] **Environment Variable Sync**: Ensure `GEMINI_MAX_ITERATIONS` and `GEMINI_COMPLETION_PROMISE` are properly defaulted and sanitized, with per-session overrides.

## 🏁 Success Criteria
1.  **Token Savings**: The agent's context window remains small across 10+ iterations.
2.  **No Hallucination**: The agent does not "forget" its original instructions after a context reset.
3.  **Strict Exit**: The agent cannot exit by simply mentioning the promise word in a sentence; it MUST use tags.
4.  **Verified Completion**: Exit only occurs when: `Tags Present` AND `Keyword Matches` AND `Tasks Completed` AND `Verify Script Passes`.

## 📅 Phases
- [x] **Phase A**: XML Tags & State Update (Foundation).
    - **Affected Files**: `hooks/after_agent.py`, `README.md`
- [x] **Phase B**: Context Reset Logic (Optimization).
    - **Affected Files**: `hooks/after_agent.py`
- [x] **Phase C**: Logging & UI Polish (Quality of Life).
    - **Affected Files**: `hooks/after_agent.py`, `README.md`, `GEMINI.md`, `commands/ralph/start.toml`, `commands/ralph/cancel.toml`
