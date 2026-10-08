# Phase 10 Frontend UX & Design Implementation Guide

## 1. Purpose

This document defines the UX, interaction, layout, and frontend implementation principles for Phase 10 of the AI Clinical Discharge Intelligence System.

The frontend is a professional clinical review application built with:

- Next.js
- React
- TypeScript
- HeroUI

**HeroUI is the primary UI/design system and source of truth.**

This document defines how the product should use HeroUI. It does not replace HeroUI with a custom design system.

---

# 2. Non-Negotiable Design Rules

1. Use HeroUI first.
2. Prefer native HeroUI components only or as much as possible.
3. Use HeroUI's existing variants, colors, themes, states, and interaction patterns.
4. Do not create a custom color palette.
5. Do not create custom color tokens.
6. Do not redefine HeroUI's theme.
7. Do not create a replacement design system.
8. Do not unnecessarily override HeroUI components.
9. Do not introduce another UI component framework without a demonstrated need.
10. Custom components are allowed only for application-specific behavior that HeroUI does not already provide.
11. Keep the interface visually restrained.
12. Prioritize clinical workflow efficiency over visual decoration.
13. Every interaction must have a deliberate state.
14. Every important action must provide clear feedback.
15. Do not use fake data in the real application.
16. Do not duplicate backend clinical/business logic in the frontend.

---

# 3. Product Experience

The product is an AI-powered second reviewer for discharge summaries.

The doctor should immediately understand:

- what document is being reviewed
- what the system found
- the completeness result
- what suggestions require attention
- why each suggestion exists
- what has been accepted
- what has been ignored
- what remains pending
- what the final reviewed document looks like
- how to export it

The interface should reduce cognitive load rather than increase it.

The experience should feel:

- calm
- trustworthy
- focused
- predictable
- efficient
- professional
- clinically appropriate

Avoid unnecessary animation, decoration, gradients, excessive cards, visual noise, or marketing-style copy.

---

# 4. Visual Direction

The target quality bar is a polished modern professional application with restrained visual design.

Use whitespace intentionally.

Use hierarchy rather than decoration to communicate importance.

Avoid the common AI-generated visual pattern of:

- oversized hero sections
- gradient backgrounds
- glowing elements
- excessive rounded cards
- excessive shadows
- floating decorative objects
- meaningless statistics
- dense dashboard grids
- excessive icons
- unnecessary animations

The application should look deliberately designed rather than generated from a template.

Minimalism must never remove necessary information.

A doctor should never have to guess:

- what happened
- what needs review
- what is already decided
- what is still pending
- what an action will do

---

# 5. HeroUI as the Design System

Use HeroUI as the default source for UI primitives.

Prefer HeroUI components for:

- Button
- Input
- Textarea
- Select
- Dropdown
- Modal
- Drawer
- Tabs
- Card
- Chip
- Badge
- Alert
- Tooltip
- Progress
- Spinner
- Skeleton
- Table
- Pagination
- Divider
- Switch
- Checkbox
- Radio
- Navbar/navigation primitives
- Avatar where appropriate

Use HeroUI component variants rather than recreating equivalent visual states.

Use HeroUI's built-in theme behavior for light and dark modes.

If a component needs a visual distinction, first determine whether HeroUI already provides an appropriate variant or semantic color before writing custom CSS.

---

# 6. Color and Theme Rules

**Do not define a custom color palette in this document.**

**Do not define custom color tokens.**

**Do not redefine HeroUI colors.**

HeroUI's existing/default color and theme system remains the source of truth.

Use HeroUI semantic colors and variants where appropriate.

Light and dark modes must both use HeroUI's native theme behavior.

The interface must remain readable and visually coherent in both modes.

Do not design a separate light-mode palette and dark-mode palette.

Do not hardcode colors merely to reproduce a mockup.

If custom CSS is genuinely required, it must respect HeroUI's theme system rather than replace it.

---

# 7. Typography

Typography should prioritize readability and hierarchy.

Use the typography system available through the Next.js/HeroUI/Tailwind ecosystem.

Do not introduce an unnecessary custom typography framework.

Establish clear levels for:

- application title
- page title
- section heading
- subsection heading
- body text
- supporting text
- metadata
- labels
- helper text
- error text

Clinical information must be easy to scan.

Avoid:

- excessively large headings
- very small metadata
- long uninterrupted paragraphs
- excessive uppercase text
- decorative typography

Text should remain readable in both light and dark themes.

---

# 8. Spacing and Layout

Use consistent spacing based on the existing HeroUI/Tailwind ecosystem.

Do not create arbitrary spacing values throughout the application.

Use spacing to establish hierarchy:

- page-level separation
- section-level separation
- component-level separation
- text-level spacing

Avoid both extremes:

- cramped interfaces
- excessive empty space that separates related information

Related content should visually belong together.

Unrelated content should have clear separation.

---

# 9. Application Shell

The application should use a predictable Next.js App Router structure.

The shell should provide:

- clear primary navigation
- current location/state
- application identity
- theme control
- responsive navigation
- consistent content container
- consistent page spacing

Navigation should never require unnecessary steps.

Do not invent unusual navigation patterns.

Use standard application conventions.

On smaller screens, navigation should transform appropriately rather than simply overflow horizontally.

---

# 10. Primary Product Areas

The frontend should organize the product around the real workflow.

Recommended application areas:

1. New Review
2. Review Workspace
3. Review History
4. Review Detail
5. Export/Preview flow
6. Application-level settings/theme controls where actually required

Do not create pages that have no real backend-supported purpose.

---

# 11. New Review / Upload

The upload experience should be simple and focused.

The user should immediately understand:

- what can be uploaded
- supported formats
- what will happen next
- whether the file is valid

Supported document formats are:

- PDF
- DOCX
- TXT

Use HeroUI form/upload-compatible patterns.

The upload area should not become a large decorative drop zone.

Provide clear feedback for:

- no file selected
- unsupported format
- invalid file
- upload in progress
- processing in progress
- successful review creation
- upload failure
- backend failure
- unreadable/corrupt document

Do not show fake processing percentages unless the backend actually provides progress information.

---

# 12. Review Workspace

The review workspace is the core product experience.

It should clearly communicate:

- document identity
- diagnosis/result
- completeness score
- review status
- suggestions
- evidence
- decisions
- final document state

The workspace should support the doctor's decision-making process without overwhelming the screen.

Use progressive disclosure where useful.

Do not hide clinically important information behind unnecessary interactions.

---

# 13. Document Comparison

The product requires an understandable distinction between:

- original document
- reviewed/final document

On larger screens, use an effective split-view or comparable side-by-side presentation.

The relationship between the two views must be obvious.

On smaller screens, transform the layout into a usable sequential or tabbed presentation rather than forcing two narrow columns.

Do not pretend that the frontend has changed clinical content automatically.

The final document must only reflect explicitly accepted suggestions according to backend behavior.

---

# 14. Suggestions

Suggestions are the central review unit.

Each suggestion should clearly show:

- section
- explanation
- current state
- relevant guideline passage/evidence
- source reference where appropriate
- available doctor actions

A suggestion must never look like an automatic instruction.

Use clear semantic states:

- pending
- accepted
- ignored/rejected

The user must always know the current state.

Actions should be explicit.

Do not make destructive or clinically meaningful actions ambiguous.

---

# 15. Suggestion Interaction

When a doctor accepts or ignores a suggestion:

1. Immediately show that the action is being processed.
2. Temporarily prevent conflicting duplicate actions.
3. Send the update to the backend.
4. Update the UI using the returned authoritative state.
5. Reflect the decision in the review workspace.
6. Show appropriate feedback.
7. If the API fails, preserve the previous confirmed state and clearly communicate the failure.
8. Allow retry where appropriate.

Do not optimistically create a state that contradicts the backend.

The backend remains authoritative.

Do not require a complete page reload after every decision.

---

# 16. Evidence Presentation

Every generated suggestion is grounded in a retrieved guideline passage.

Evidence should be accessible without dominating the primary workflow.

Use progressive disclosure where appropriate.

A doctor should be able to answer:

> Why is this suggestion being shown?

without leaving the review workflow.

Source links should be visually recognizable and accessible.

Do not fabricate guideline information.

Do not display unsupported clinical claims.

---

# 17. Completeness Score

The completeness score should be visually understandable without becoming a decorative dashboard metric.

It should communicate:

- score
- relationship to the current review
- suggestion/review context

Avoid oversized circular gauges or decorative charts unless they materially improve understanding.

The score must never imply diagnostic certainty, medical correctness, or clinical safety beyond what the backend actually calculates.

---

# 18. Review Status

Status should be clear and consistent across:

- review workspace
- history
- detail pages
- export flow

Use HeroUI semantic states and components.

Do not create different visual meanings for the same status in different pages.

---

# 19. History

History should be a functional workspace rather than a decorative table.

It must support the backend's capabilities:

- search
- status filtering
- sorting
- grouping
- pagination

Use the real API query parameters.

Do not fetch an unlimited history dataset merely to perform all filtering in the browser.

History entries should provide enough information to identify a review quickly.

At minimum, use available backend information such as:

- filename
- diagnosis
- status
- completeness score
- creation time

Do not invent unavailable fields.

---

# 20. Empty States

Every collection or page that can legitimately have no content needs an intentional empty state.

An empty state should explain:

- what is empty
- why it may be empty
- what the user can do next

Avoid meaningless illustrations or excessive copy.

Examples:

- no previous reviews
- no search results
- no suggestions
- no matching guideline
- no audit events

---

# 21. Loading States

Use HeroUI loading/skeleton/spinner patterns where appropriate.

Loading states should preserve layout stability.

Avoid replacing the entire application with a generic full-screen spinner when only one area is loading.

For long AI processing operations, clearly communicate that the review is being processed without inventing backend progress.

---

# 22. Error States

Errors must be specific and actionable.

Differentiate between:

- invalid input
- unsupported file
- unreadable document
- network failure
- backend error
- review not found
- guideline unavailable/no match
- preview failure
- export failure

Do not display raw stack traces to users.

Do not hide errors behind generic "Something went wrong" messages when a useful explanation is available.

Provide retry or recovery paths where appropriate.

---

# 23. No Guideline Match

A no-match result is a valid system state, not a generic failure.

The interface must clearly communicate that the system does not have a sufficiently matching guideline and therefore should not invent suggestions.

Do not make the UI imply that the AI simply "failed."

Do not generate frontend fallback clinical advice.

---

# 24. Preview and Export

The export experience must support:

- PDF
- DOCX
- TXT

The user should be able to preview the current output before committing to download.

Use a clear format selector.

Preview should not be confused with export.

Export should explicitly represent the final action.

During export:

- disable conflicting duplicate actions
- show progress/loading
- handle failure
- trigger the correct file download
- show success feedback

Do not mark a review exported merely because a preview was requested.

The backend is authoritative for export state.

---

# 25. Responsive Design

Design intentionally for:

### Desktop

Use the available width efficiently.

The review workspace may use multiple coordinated regions when useful.

### Laptop

Maintain the same information hierarchy while reducing unnecessary horizontal density.

### Tablet

Allow panels to stack or transform while keeping review actions accessible.

### Mobile

Prioritize:

1. review identity/status
2. score
3. suggestions
4. evidence
5. decisions
6. final document
7. export

Do not simply shrink desktop components.

Use appropriate HeroUI responsive patterns and application-specific layout logic.

Avoid horizontal scrolling unless it is genuinely required.

---

# 26. Accessibility

Accessibility is part of product quality.

Ensure:

- semantic HTML
- keyboard navigation
- visible focus states
- logical tab order
- accessible labels
- appropriate button names
- sufficient text readability
- modal focus management
- accessible error messages
- no information conveyed by color alone
- appropriate ARIA only when needed
- usable mobile touch targets

Do not sacrifice accessibility for visual minimalism.

---

# 27. Interaction Psychology

Use predictable interaction patterns.

Important principles:

### Recognition over recall

Show the information required for decisions instead of forcing users to remember it.

### Immediate feedback

Actions should produce clear feedback.

### Error prevention

Disable or constrain invalid actions before submission where possible.

### Progressive disclosure

Show important information first and deeper evidence/details when requested.

### Consistency

The same action should behave the same way everywhere.

### Reversibility

Where technically supported, make review decisions understandable and recoverable.

### Clear consequence

Actions that affect the final reviewed document must clearly communicate their effect.

---

# 28. Clinical Workflow Principle

The AI is an advisory second reviewer.

The frontend must reinforce that principle.

Never make the interface imply:

- automatic clinical approval
- automatic editing
- automatic acceptance
- medical diagnosis
- guaranteed correctness

The doctor remains the decision maker.

The UI should make explicit doctor decisions easy and visible.

---

# 29. Content and Copy

Use plain, concise, clinical-but-approachable language.

Avoid:

- marketing slogans
- exaggerated AI claims
- unexplained technical terminology
- unnecessary abbreviations
- overly verbose descriptions
- generic AI phrases

Buttons should use direct action language.

Examples of appropriate patterns:

- Review document
- Accept
- Ignore
- View evidence
- Preview
- Export
- Retry
- Open review

Avoid vague actions such as:

- Enhance
- Optimize
- Magic
- Supercharge
- Generate insight

unless the actual product behavior specifically requires them.

---

# 30. Icons

Use icons only when they improve recognition or reduce visual complexity.

Do not decorate every heading or card with an icon.

Icons must not replace necessary text for important actions.

Use consistent iconography.

Prefer the icon system already compatible with the chosen HeroUI/Next.js implementation rather than introducing several icon libraries.

---

# 31. Animation and Motion

Motion should be subtle and functional.

Use animation for:

- state transitions
- loading feedback
- panel transitions
- confirmation feedback

Avoid:

- decorative animation
- excessive bouncing
- dramatic page transitions
- continuous motion
- animations that delay important workflows

Respect reduced-motion preferences.

---

# 32. Component Consistency

A component should have one consistent meaning.

For example:

- primary actions should look consistent
- destructive actions should look consistent
- statuses should use consistent semantic treatment
- evidence presentation should behave consistently
- dialogs should behave consistently
- loading states should use consistent HeroUI patterns

Do not create visually different versions of the same component for individual pages without a strong UX reason.

---

# 33. Custom Components

Custom components are appropriate for product-specific behavior such as:

- review workspace
- suggestion review item
- document comparison view
- evidence viewer
- review status summary
- application-specific history row
- export preview container

Custom components should compose HeroUI primitives wherever possible.

Do not recreate generic UI primitives that HeroUI already provides.

---

# 34. State Architecture

Keep state close to where it is needed.

Separate:

- server/API state
- UI state
- form state
- transient interaction state

The backend remains authoritative for persisted review state.

Do not maintain duplicate representations of the same persisted suggestion decision without a clear synchronization strategy.

Avoid unnecessary global state.

---

# 35. API Integration UX

The frontend API layer should provide typed methods for the real backend contracts.

It should centralize:

- base URL configuration
- request handling
- response parsing
- error normalization
- upload handling
- API timeout/retry behavior where appropriate

Components should not contain duplicated raw `fetch()` logic for the same endpoint.

Do not hardcode production backend URLs.

Use environment-based configuration appropriate for Next.js.

Never expose backend secrets to the browser.

---

# 36. Security UX

Never expose:

- API secrets
- database credentials
- LLM credentials
- Langfuse secrets

to client-side code.

Do not log document contents.

Do not display raw backend exception details.

Treat uploaded documents as sensitive.

Only expose information required by the actual product workflow.

---

# 37. Performance

Avoid unnecessary client-side rendering.

Use Next.js server/client boundaries intentionally.

Do not make the entire application a client component without a reason.

Avoid unnecessary API requests.

Avoid repeated history fetches caused by uncontrolled state changes.

Avoid rendering extremely large document content inefficiently.

Use pagination for history.

Prefer stable layouts to prevent layout shift during loading.

---

# 38. Do Not Fake Functionality

The production frontend must not contain:

- fake review results
- hardcoded patient/document data
- fake progress percentages
- fake AI responses
- fake history records
- fake export success
- fake suggestion decisions

If the backend does not support a requested behavior, identify the limitation rather than silently pretending it works.

---

# 39. Design Review Checklist

Before considering a screen complete, verify:

### Visual

- Is hierarchy immediately clear?
- Is the screen visually calm?
- Is there unnecessary decoration?
- Does it look like a professional product?
- Is HeroUI being used correctly?
- Has unnecessary custom styling been avoided?

### UX

- Is the primary action obvious?
- Can the user understand the current state?
- Are errors recoverable?
- Are important decisions explicit?
- Is unnecessary cognitive load removed?

### Accessibility

- Can it be used with keyboard navigation?
- Are labels and focus states correct?
- Is information understandable without relying only on color?

### Responsive

- Does it work on desktop?
- Does it work on tablet?
- Does it work on mobile?
- Does the information hierarchy survive smaller screens?

### Theme

- Does it work correctly in HeroUI light mode?
- Does it work correctly in HeroUI dark mode?
- Has no competing custom theme been introduced?

### Integration

- Is the data real?
- Does the API contract match the backend?
- Are loading/error states handled?
- Is persisted state authoritative?
- Does the interaction work end-to-end?

---

# 40. Final Quality Standard

The final frontend should feel like a real professional clinical software product.

It must not feel like:

- a template
- a prototype
- a demo
- a hackathon interface
- a generic AI dashboard
- an AI-generated component collection

The design should achieve quality through:

**clarity + hierarchy + restraint + consistency + usability + reliable interaction**

not through excessive visual effects.

HeroUI remains the UI foundation and source of truth.

Do not replace HeroUI's design language with a custom theme.

Do not create a custom color system.

Do not sacrifice usability for visual novelty.

The product should make the doctor's review workflow feel simple, focused, and predictable.