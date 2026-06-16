# Objective
Enhance the `/spec` custom command (`.gemini/commands/spec.toml`) to incorporate best practices identified from the Claude-generated spec. This will improve the quality and depth of future feature specifications.

# Key Files & Context
- `.gemini/commands/spec.toml`: The prompt defining the behavior of the `/spec` command.

# Implementation Steps
Modify "Step 7" in `.gemini/commands/spec.toml` to require:
1. **Templates Section Update**: Require listing of UI state changes and visual feedback (e.g., active states).
2. **Files to Change Section Update**: Require detailed bullet points for each file, specifying exactly which functions/classes need to change and a description of the logic updates.
3. **New Section - Edge Cases and Error Handling**: Mandate defining how the feature handles invalid inputs, empty states, or unexpected behavior.
4. **Rules for Implementation Update**: Add a requirement to include specific rules for input validation.
5. **Definition of Done Update**: Mandate that the checklist includes verifications for both the happy path and the edge cases/error handling paths.

# Verification & Testing
1. Run `/spec` with a dummy feature (e.g., `/spec 99 test-feature`) and verify that the generated spec includes the new, more detailed structure.
2. Ensure the TOML syntax in `.gemini/commands/spec.toml` remains valid after the updates.