# Targeted F2 accessibility qualification

This is a bounded engineering audit, not WCAG 2.2 AA certification, expert utility
validation or a claim of actual screen-reader testing.

The browser harness executes real keyboard navigation: landing skip link, native
import/help disclosures, four-step links, focus at exact destinations, reading
selection, report-to-data return and focus inside a refusal. New dataset headings
receive focus; intent/theme/language changes do not reset dataset focus/state.
Processing is a polite live status with one actual current stage and no invented
percentage. Errors are labeled alerts with an action, raw reason and recovery
link. Radios have fieldset legends; optional declarations have labels/hints.
Shared chart components and F1 semantic captions/tables/SVG remain in use.

Test-only `axe-core` 4.14.1 (MPL-2.0) is pinned in the development lock. It is
injected only by the browser test runner, never bundled in the production client
or script-free exported reports. Product/provider licences and versions remain
unchanged. Audits run the WCAG 2 A/AA and WCAG 2.1 A/AA tags over representative
landing/import-help, live four-step, retained-refusal, saved tablet and French
dark mobile states. JSON artifacts retain both violations and incomplete checks;
the tests require zero reported violations rather than disabling failing rules.

The initial live audit found four serious contrast violations on the new step
numbers (3.38:1). Removing their translucent text corrected the demonstrated
defect. The subsequent audited states have no reported violations. Incomplete
color-contrast and label/name checks remain manual-review candidates: a pass is
not inferred from an incomplete result. Actual screenshots were opened for visual
inspection of the relevant desktop/mobile, figure, source, warning and print
states. See the exact-head PR artifacts and [validation](F2_VALIDATION.md).

No interactive NVDA/JAWS/VoiceOver session was available/executed. ARIA/DOM,
keyboard interaction, axe and AI visual inspection are the evidence actually
obtained. Native disclosure accessibility, SVG chart descriptions and horizontal
technical-table scrolling still need representative assistive-technology users.
No real users were recruited or simulated as scientific expert reviewers.
