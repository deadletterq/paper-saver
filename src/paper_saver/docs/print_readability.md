# Print readability on A4 — research and recommendations

Reference document for the Paper Saver print stylesheet (`src/paper_saver/assets/print_styles.css`). Distills the empirical reading-research literature and the classical typographic tradition into concrete numeric targets, weighted against this project's three hard constraints:

1. **Black ink only** — no greys, tints, colour accents.
2. **Save paper** — compact margins, dense leading acceptable.
3. **Save ink** — no decorative rules, no link underlines, semibold over bold where it suffices.

Where the research permits a range, the recommendation tilts toward paper/ink economy. Where it doesn't, readability wins.

---

## 0. Why print typography matters at all

Reading on paper produces measurably better comprehension than reading on screens, and the gap is *widening* — not narrowing — as people are exposed to more digital reading.

- **Delgado et al. (2018)**, meta-analysis of 54 studies and 171,055 participants in *Educational Research Review*: paper-based reading is comprehended better than screen reading; the effect is strongest under time pressure and for **informational / expository text** — the exact content Paper Saver targets. The effect has grown over time since 2000.
- **Salmerón et al. (2023)** confirms the screen disadvantage persists for handheld devices.
- Proposed mechanism — the *shallowing hypothesis*: digital media trains shallow scanning; paper invites linear/deep processing.

This is the empirical justification for the entire project. It also means the stylesheet should be judged by **sustained-reading comprehension**, not by visual polish, glanceability, or print-preview aesthetics.

Sources: [Delgado et al. 2018 (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S1747938X18300101) · [PDF mirror](https://www.uv.es/lasalgon/papers/Delgado%202018%20dont%20throw%20away%20your%20printed%20books.pdf) · [Salmerón et al. 2023 PDF](https://www.uv.es/lasalgon/papers/Salmeron%202023%20manuscript_tablets.pdf).

---

## 1. Quick-reference table

Current CSS values are shown alongside the research-supported range so the reader can see where we land and where there's headroom.

| Parameter            | Current CSS                                 | Research-supported range          | Notes                                                                         |
| -------------------- | ------------------------------------------- | --------------------------------- | ----------------------------------------------------------------------------- |
| Body type size       | 11.5 pt (Iowan/Palatino)                    | 10–12 pt for serif body           | At ~50 cm reading distance this is within the critical print size sweet spot. |
| Line-height          | 1.38                                        | 1.20–1.45 for serif at 60–75 CPL  | Tight is fine for high-x-height serifs like Iowan.                            |
| Measure (CPL)        | ~80–90 at current margins (A4, 11.5 pt)     | 60–75; hard cap 75                | **Currently too wide.** See §4 — widen side margins or up the type size.      |
| Page margins         | 1.5 cm top / 1.7 cm sides + bottom          | 1.5–2.5 cm symmetric              | Defensible as paper-saving; bottom slightly larger preserves Tschichold cue.  |
| Alignment            | `text-align: left` (ragged-right)           | Justified *iff* hyphens work      | WeasyPrint hyphenates well — justification is on the table.                   |
| Hyphenation          | `auto`, limit-chars 8/4/4                   | 6/3/3, max 2 consecutive          | Slightly loosen current setting; cap consecutive hyphenated lines.            |
| Widows / orphans     | 3 / 3                                       | 3 / 3                             | Already correct.                                                              |
| Heading top weight   | h1 700, h2/h3/h4 600                        | 600 (semibold) preferred over 700 | Drop h1 to 600 — printer ink-spread + crowding research both support this.    |
| Heading scale        | h1 16 / h2 13.5 / h3 12.5 / h4 12 / body 11.5 | 1.15–1.333× per step (perfect-fourth or tighter) | Current scale is roughly correct; small tightening is possible.            |
| Link decoration      | hairline underline (0.3 pt)                 | None for B&W single-sided print   | Already minimal — consider removing entirely; URLs aren't navigable on paper. |
| Blockquote           | 0.6 em left indent + 0.4 pt rule, italic    | 1–2 em indent, **upright** body face | Italic for long quotes hurts speed — see §10.                              |
| Table body size      | 9.5 pt                                      | 8.5–9.5 pt                        | Already correct.                                                              |
| Footnote / superscript | n/a                                       | 60–70 % cap height, after punctuation | Add if Readability ever extracts real footnotes.                            |

---

## 2. Line length (measure) — the single most important parameter

**Target: 60–70 characters per line. Hard cap: ~75. Floor: ~45.**

The strongest, longest-running finding in reading research. Three converging traditions agree:

- **Tinker & Paterson (1929–1963)** — eye-movement studies on 10 pt type with 2 pt leading. Optimal speed and comprehension at 3–4 inch lines (~45–60 CPL). Established the "safety zone": size, leading, and measure interact and can't be tuned in isolation. [Tinker 1963 PDF](https://gwern.net/doc/design/typography/1963-tinker-legibilityofprint.pdf) · [Methods review](https://designregression.com/article/examining-the-research-methods-used-by-legibility-legends-tinker-and-paterson)
- **Bringhurst, *Elements of Typographic Style*** — "45 to 75 characters is widely regarded as a satisfactory length of line for a single-column page set in a serifed text face... A 66-character line is widely regarded as ideal." Rule of thumb: target measure ≈ 30× type size in points. [webtypography.net 2.1.2](http://webtypography.net/2.1.2)
- **Dyson (2004)** review article — 55–70 CPL is the empirically-supported sweet spot. Long lines (100+) can be read faster but readers strongly dislike them; comprehension drops. [PDF mirror](https://stu.westga.edu/~ssynan1/literacy/Dyson.pdf)
- **Atilgan, Xiong & Legge (PNAS 2020)** — there is also a *floor*: ~13 characters is the minimum to reach 80 % of maximum reading speed for normally-sighted readers. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7720185/)

**What happens at the extremes:**
- **Above 75 CPL** — return-sweep failures ("doubling"): the eye loses the next line on the reverse saccade, causing regressions, re-reading, and fatigue.
- **Below 45 CPL** — too many return sweeps per paragraph, the saccade rhythm is disrupted, and hyphenation pressure rises (which itself slows reading).

**Implication for Paper Saver.** A4 minus 1.7 cm side margins = 17.6 cm measure. At Iowan 11.5 pt the average character width is ~2.0 mm, giving **~85–90 CPL** — about 15 CPL over the empirical sweet spot. Options:

1. **Widen the side margins to ~2.5 cm** — measure drops to ~16 cm / ~75 CPL. Costs ~1.6 cm² of printable area per page; preserves all type sizes.
2. **Up the body to 12 pt** — average char width grows, CPL drops to ~80. Worse for paper (fewer lines per page) but easier on older eyes.
3. **Two-column layout** — yields 40–50 CPL per column, which is the multi-column sweet spot, and squeezes more text per page. Significant complexity in WeasyPrint and breaks figure/code/table flow. Not recommended unless the project decides paper density is paramount.

Recommendation: **option 1**, plus a measured A/B comparison on real prints. The paper saved by tight side margins is illusory — it isn't more text-per-page, it's wider lines per page, and wider lines slow reading.

---

## 3. Body type size

**Target: 11–11.5 pt for Iowan/Palatino. 10 pt floor; 12 pt for older readers.**

- **Tinker** — 10 pt optimal at 19-pica measure with 2 pt leading; 6 pt and 14 pt slowed readers; 9–12 pt all acceptable.
- **Legge & Bigelow (2011)**, vision-science — maximum reading speed is reached at the *critical print size* of ~0.2° visual angle, which at 40 cm equals an x-height of ~1.4 mm (~4 pt). Reading is "fluent" across a 10× range (0.2°–2°, i.e., x-height 1.4–14 mm). Real-world hardback books cluster at x-height ~1.68 mm — roughly **9.5–11 pt** body type depending on the face's x-height ratio. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/)
- **Older readers** — critical print size shifts upward with age-related vision loss. Practical rule: add 1 pt for documents likely to be read by 60+. [Frontiers review](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.931646/full)
- **Butterick** (widely cited in legal-doc typography): 10–12 pt for print; 11 pt usually optimal. [Point size](https://practicaltypography.com/point-size.html)

Iowan Old Style has a generous x-height for a Palatino-family serif, which is why it reads well at 11.5 pt where Garamond would feel small. **Current setting is well-founded.**

---

## 4. Leading / line-height

**Target: 1.30–1.40× for serif body at 60–75 CPL.** Leading scales with measure: longer lines need more lead.

- **Tinker & Paterson** — 2 pt of leading on 10 pt type (12/10 = 1.2 line-height) was optimal at their 19-pica measure. Set-solid (no extra leading) hurt reading speed at all but the shortest measures.
- **Bringhurst** — leading depends on typeface, language and x-height; **serif faces with generous x-heights can take *tighter* leading than sans-serifs**. [Summary](https://www.inkwell.ie/typography/bringhurst.html)
- **Convergence** — for serif print at modest CPL with moderate x-height, **1.3–1.4 is standard** and supported by both Bringhurst and Hochuli. As CPL approaches 75+, increase to 1.5–1.6. [Pimp my Type](https://pimpmytype.com/line-length-line-height/)

Current 1.38 line-height is squarely in the supported range and aligns with the "tight is fine for high-x-height serifs" guidance. **No change needed** — until/unless §2 widens the measure beyond 75 CPL, in which case leading should rise toward 1.45.

---

## 5. Serif vs sans-serif on paper

**No measurable difference for sustained reading at 600 dpi. Choose on aesthetic and tradition grounds.** The "serifs guide the eye" claim is folklore unsupported by 70 years of research.

- **Lund (1999), U. Reading** — dissertation reviewed 72 studies; *no valid conclusion in favour of either*. [Summary](https://alexpoole.info/blog/which-are-more-legible-serif-or-sans-serif-typefaces/)
- **Arditi & Cho (2005)** — varied serif size (0 %, 5 %, 10 % of cap height): no difference in reading speed on paper or in RSVP. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4612630/)
- **Richardson (2022)** book-length review across paper and screen: no consistent difference. [Open-access PDF](https://library.oapen.org/bitstream/id/165f35ac-584f-4a2e-ba84-6832faed7e69/978-3-030-90984-0.pdf)

Iowan Old Style is a fine choice. Switching to a sans for the body would not measurably help reading speed — and would lose the centuries-old prose convention that primes the reader's "long-form" attention mode. Keep it.

---

## 6. Margins on A4

**No empirical "right answer." Typographic tradition gives the strongest guidance.**

- **Tschichold's canon** (codifying van de Graaf / Rosarivo): margin ratios **1 : 1 : 2 : 3** (inner : top : outer : bottom) on a 2:3 page place the text block in golden-section proportion. The bottom margin is largest to "ground" the page. A4 is 1 : √2 ≈ 1 : 1.414 — not 2:3 — so the canon doesn't translate one-to-one, but the *ratio asymmetry* still applies. [Canons of page construction](https://en.wikipedia.org/wiki/Canons_of_page_construction) · [Tschichold rules](https://www.foglioprint.com/blog/jan-tschicholds-timeless-rules-what-modern-self-publishers-can-learn-from-the-father-of-book-design)
- **Inner/gutter margin is irrelevant** here — Paper Saver prints single-sided; there's no binding edge.
- **Printer safe area** — consumer lasers can clip below ~5 mm; below ~10 mm clipping is a real risk.

The driving constraint isn't tradition or printer hardware; it's the line-length finding from §2. **Margins are how you control measure.** For Iowan at 11.5 pt on A4 (210 mm wide), the side margin needed to land at the 60–75 CPL sweet spot is **2.0–2.5 cm**. The current 1.7 cm is paper-economical but pushes measure past the recommended ceiling.

Recommendation:
- **Side margins: 2.2 cm** (lands ~75 CPL — top of the sweet spot, max ink per page).
- **Top: 1.5 cm**, **bottom: 2.0 cm** — preserves a hint of the Tschichold "grounded" bottom without burning paper.
- A4 ream height utilisation at these margins: ~25 cm of text per page vs the current 26.6 cm — about a 6 % paper hit in exchange for a much-improved measure. Worth it.

---

## 7. Justification vs ragged-right; hyphenation

**Justify *iff* hyphenation is reliable. WeasyPrint hyphenation is reliable. Therefore: justify.**

- **Gregory & Poulton (1970)** — justified vs ragged made *no* difference for skilled readers; for poorer readers in narrow columns, justified was significantly worse. Effect disappeared at ~12 words/line (~60 CPL). [Discussion](https://www.designthings.org/things/righthandedge) · [ResearchGate](https://www.researchgate.net/publication/230180398_Right_is_Wrong_an_examination_of_the_effect_of_right_justification_on_reading)
- **Trollip & Sales (1986)** — fill-justified computer-generated text read more slowly than ragged. The key issue: 1986-era word processors lacked hyphenation, so justification produced large word-spaces and rivers. [SAGE](https://journals.sagepub.com/doi/abs/10.1177/001872088602800204)
- **Modern replications** — with proper hyphenation, justified is comparable to or marginally faster than ragged at normal measures. [Heyman roundup](https://heyman.info/2023/fill-justified-text-on-the-web)

The current `text-align: left` (ragged) is the *safer* default; a small experiment is worth running. If the inter-word spacing in justified output is reasonable (no rivers, no large gaps), switch. Combined with hyphenation per §8, the page will look like a printed book.

Recommended block to test:

```css
p {
    text-align: justify;
    text-justify: inter-word;
}
```

---

## 8. Hyphenation parameters

**Adopt Knuth/Liang TeX defaults — they have governed professional typesetting for 40+ years and remain unbeaten.**

- **TeX (American English) defaults**: min word length **5**, min prefix **2**, min suffix **3**. [TUG patterns](http://www.tug.org/tex-hyphen/) · [Liang's thesis](https://www.tug.org/docs/liang/liang-thesis.pdf)
- **Maximum consecutive hyphenated lines** — Bringhurst: no more than **2**; 3 is a defect.
- **Last word of a paragraph or page**: never hyphenate.

Current setting: `hyphenate-limit-chars: 8 4 4` — that is, 8-letter min word, 4 before, 4 after. This is *conservative* (almost no Anglo-Saxon vocabulary qualifies); justification with this setting will produce wide word-spaces. Loosen to:

```css
p {
    hyphens: auto;
    -webkit-hyphens: auto;
    hyphenate-limit-chars: 6 3 3;
    hyphenate-limit-lines: 2;
    hyphenate-limit-last: always;
}
```

Recheck after the change — too-aggressive hyphenation produces "ladders" of hyphens down the right edge.

---

## 9. Headings — hierarchy, weight, scale

**Use the smallest contrast that signals the level. Prefer semibold (600) over bold (700).**

### 9.1 Why semibold beats bold on consumer printers

- **Xiong, Lorsung, Mansfield & Legge (2018)** — *Effect of Letter-stroke Boldness on Reading Speed*: reading speed is essentially **flat across 0.72×–1.89×** standard stroke weight in central vision but drops **~23 %** at the thin extreme and **21–51 %** in the periphery at 1.89× and 3× stroke. Mechanism: thicker strokes reduce effective letter spacing → *crowding*. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3642228/)
- **Printer ink-spread** at 600 dpi: true bold weights typically gain another 5–10 % stroke width over the digital outline; counters of `e`, `a`, `o` start filling in. Semibold leaves headroom.

Practical: **drop h1 from 700 → 600.** If headings still look smeary in test prints, drop to 500. Current h2/h3/h4 at 600 is already correct.

### 9.2 Scale

Modular scale ratios used in book typography: minor third (1.2), perfect fourth (1.333), golden (1.618). For body-heavy prose the **perfect fourth or smaller** is conventional. [Typographic scale](https://retinart.net/typography/typographicscale/)

Current scale: 11.5 / 12 / 12.5 / 13.5 / 16 pt — ratios 1.043, 1.042, 1.08, 1.185. h1 jumps by ~1.19 from h2; everything else is a *tighter than minor-third* progression. This is fine — it sacrifices visual punch for ink economy and lets the *weight + space + small-caps + italic* cues do hierarchy work.

### 9.3 Cue choice per level (recommended)

| Level | Cue                                            | Rationale                                                              |
| ----- | ---------------------------------------------- | ---------------------------------------------------------------------- |
| h1    | Size + weight 600 + generous space-above       | Page-defining; needs to be unambiguous.                                |
| h2    | Size + weight 600 + space                      | The workhorse heading.                                                 |
| h3    | Size (smaller jump) + weight 600               | Subsection.                                                            |
| h4    | Size = body + weight 600                       | Tertiary; same size as text saves vertical space.                      |
| h5    | Body size + *italic* (no weight change)        | Quiet level; italic is the lightest emphasis cue. [Butterick](https://practicaltypography.com/headings.html) |
| h6    | Body size + small-caps + letter-spacing 0.04 em | Quietest level; classical four-level-deep convention.                  |

Current `h5 { font-style: italic }` and `h6 { font-variant: small-caps; letter-spacing: 0.04em }` already follow this. **Keep them.**

### 9.4 Whitespace as hierarchy

Traditional typesetting often uses just *space + indent removal + small caps* for one level of subheading — no size or weight change at all. This is the most ink-saving option and is appropriate for short articles where the reader doesn't need to scan-jump between sections.

---

## 10. Blockquotes

**Indent left only by 1–2 em, keep the body face upright, slight size reduction is optional, no italic, no quotation marks.**

- Italic for *long* quotations is a 19th-century newspaper convention that hurts sustained reading; italic-everything induces slower reading and more regressions. [Block quotation](https://en.wikipedia.org/wiki/Block_quotation) · [Typography of quotations](https://www.sitepoint.com/typography-of-quotations/)
- Indent alone is sufficient to mark the quotation; ink-economy considerations push against quotation marks *and* against the italic.

Current CSS uses `font-style: italic` and a hairline left rule. The rule is fine (very low ink cost — 0.4 pt at one segment per quote). The italic should be **dropped** for any blockquote longer than 2–3 lines. Suggested change:

```css
blockquote {
    margin: 0.35em 0 0.35em 0.6em;
    padding: 0 0 0 0.6em;
    border-left: 0.4pt solid var(--ink);
    /* font-style: italic;  ← remove */
    color: var(--ink);
    text-indent: 0;
    break-inside: avoid;
}
```

If the visual cue feels too quiet without italic, restore italic *only* on short (<3-line) blockquotes via a class added at extraction time — or accept the very minor cue and trust the indent.

---

## 11. Links on printed paper

**Drop the underline entirely. The hairline is already minimal; removing it gains a small amount of ink and loses nothing the reader can use on paper.**

- Underlines on screen serve a navigational purpose (cue to click); on a static print they cue nothing — the paper isn't interactive.
- WCAG SC 1.4.1 requires non-colour link distinction *for screen colour-blindness*; irrelevant for B&W single-sided print.
- If preserving the link target is important, render an **endnote-style appendix** at the end of the document — a small monospace 8.5 pt list of `[n] resolved-URL` pairs, referenced from the body by superscript numerals.

Current CSS already underlines at 0.3 pt — a defensible halfway position. If the user wants the citation cue preserved without ink, the endnote block is the more honest convention for print and worth a future iteration.

---

## 12. Widows, orphans, page breaks

**3 / 3 minimum. Headings break-after: avoid. Code, tables, blockquotes break-inside: avoid.**

- Default CSS is `widows: 2; orphans: 2` — meets the absolute minimum but produces visible defects in long documents. Bumping to 3 is the practical standard. [PrintCSS](https://printcss.net/articles/widows-and-orphans) · [W3C §13 Paged Media](https://www.w3.org/TR/2006/WD-CSS21-20060411/page.html)
- **Bringhurst / Tschichold**: a widow (final short line orphaned at top of next page) is the worse offence; an orphan (first line of paragraph at bottom of previous page) is tolerable. [Widows and orphans](https://en.wikipedia.org/wiki/Widows_and_orphans)
- **Hochuli** (*Detail in Typography*) — tolerates the rule's relaxation when enforcement would otherwise produce inconsistent leading.

Current CSS uses `widows: 3; orphans: 3` and `page-break-after: avoid` / `break-after: avoid-page` on headings, with `break-inside: avoid` on tables, code, blockquotes, list items. **Correct and complete — no change.**

---

## 13. Tables

- **Body size inside tables: 8.5–9.5 pt.** Tighter than body lets rows fit; the table itself signals "this is reference, not prose," so the reader will tolerate the size drop.
- **Horizontal rules only above and below the table header.** No vertical rules. No alternating row stripes. (Tufte / Bringhurst convention; also the most ink-economical layout.)
- **Tabular numerals**: enable `font-variant-numeric: tabular-nums lining-nums` so columns of numbers align.

Current CSS does all three. **No change.**

---

## 14. Figures and images

The Readability extraction strips images. Recommendation:
- **Also strip figure captions** when the figure itself is gone — orphan captions ("Figure 3: distribution of …") confuse the reader and waste ink.
- If captions are retained for future use, prefix with `[Figure: ]` so the orphaned-image case is unambiguous.

Current CSS hides all visual media via `display: none !important`. **No change** beyond optionally extending the selector to `figcaption` and `figure > p` when figures are stripped.

---

## 15. Tensions the research can't resolve

These are the places where two of our three constraints pull in opposite directions and the literature gives no clean answer. Listed so future tweakers can re-litigate consciously.

1. **Margin width vs measure**: tighter margins save paper but push measure past the 75-CPL ceiling. We chose paper economy; the research prefers readability. §6 proposes a middle ground.
2. **Justification vs ragged-right**: justification with hyphenation reads at least as well as ragged for skilled readers, and *looks* like a printed book — but it commits us to good hyphenation patterns for every language we encounter. WeasyPrint supports `hyphens: auto` for any language with installed Pyphen dictionaries; coverage is good for English/major-European, patchy elsewhere. Default ragged is safer; English-only deployment can justify.
3. **Bold vs semibold headings**: semibold is empirically better but produces a quieter visual hierarchy. The Paper Saver aesthetic is already quiet; this is the right trade.
4. **Italic blockquotes vs upright**: research disfavours italic for long quotations; tradition still uses it widely. Upright is the more readable choice for the prose-heavy case we target.
5. **Endnote URL appendix vs in-body underline**: the appendix is more honest for print but adds page count. Defer until users ask for it.

---

## 16. Concrete change list (priority order)

If the next pass at `print_styles.css` were to act on this document, the highest-ROI changes are:

1. **Widen side margins** from 1.7 cm → 2.2 cm (§6). Brings measure into the 60–75 CPL sweet spot. Single-line CSS change; biggest readability win available.
2. **Drop h1 weight** from 700 → 600 (§9.1). Eliminates printer ink-spread filling counters on first-page headings.
3. **Loosen hyphenation** from `8 4 4` to `6 3 3`, add `hyphenate-limit-lines: 2; hyphenate-limit-last: always;` (§8). Lets justification (or even just ragged) breathe properly.
4. **Remove italic from blockquotes** longer than ~3 lines (§10). Either drop unconditionally, or class-gate at extraction time.
5. **Try justification** (`text-align: justify` on `p`) and compare against current ragged on a real test print (§7). Adopt if rivers/word-spacing look acceptable.
6. **Remove link underlines** entirely (§11), and optionally add an endnote URL block at the end of the rendered document. Lower priority — current hairline underline is already very low cost.

The remainder of the stylesheet — type face, body size, line-height, list and code styling, widow/orphan rules, table rules, image stripping — is already well-aligned with the research and needs no change.

---

## Sources

Primary research, in order of first citation:

- Delgado et al. 2018, *Don't throw away your printed books* — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1747938X18300101) / [PDF](https://www.uv.es/lasalgon/papers/Delgado%202018%20dont%20throw%20away%20your%20printed%20books.pdf)
- Salmerón et al. 2023 — [PDF](https://www.uv.es/lasalgon/papers/Salmeron%202023%20manuscript_tablets.pdf)
- Tinker 1963, *Legibility of Print* — [PDF](https://gwern.net/doc/design/typography/1963-tinker-legibilityofprint.pdf)
- Tinker & Paterson methods — [Design Regression](https://designregression.com/article/examining-the-research-methods-used-by-legibility-legends-tinker-and-paterson)
- Bringhurst, *Elements of Typographic Style* — [webtypography.net 2.1.2](http://webtypography.net/2.1.2) / [summary](https://www.inkwell.ie/typography/bringhurst.html)
- Dyson 2004, *How physical text layout affects reading from screen* — [PDF](https://stu.westga.edu/~ssynan1/literacy/Dyson.pdf)
- Atilgan, Xiong & Legge 2020, PNAS — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7720185/)
- Legge & Bigelow 2011, *Does print size matter for reading?* — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3428264/)
- Lund 1999 dissertation — [Alex Poole summary](https://alexpoole.info/blog/which-are-more-legible-serif-or-sans-serif-typefaces/)
- Arditi & Cho 2005, *Serifs and font legibility* — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4612630/)
- Richardson 2022, *The Legibility of Serif and Sans Serif Typefaces* — [OAPEN PDF](https://library.oapen.org/bitstream/id/165f35ac-584f-4a2e-ba84-6832faed7e69/978-3-030-90984-0.pdf)
- Tschichold canon — [Canons of page construction](https://en.wikipedia.org/wiki/Canons_of_page_construction) / [Tschichold rules](https://www.foglioprint.com/blog/jan-tschicholds-timeless-rules-what-modern-self-publishers-can-learn-from-the-father-of-book-design)
- Gregory & Poulton 1970 — [discussion](https://www.designthings.org/things/righthandedge) / [ResearchGate](https://www.researchgate.net/publication/230180398_Right_is_Wrong_an_examination_of_the_effect_of_right_justification_on_reading)
- Trollip & Sales 1986 — [SAGE](https://journals.sagepub.com/doi/abs/10.1177/001872088602800204)
- Modern justification roundup — [Heyman 2023](https://heyman.info/2023/fill-justified-text-on-the-web)
- Xiong, Lorsung, Mansfield & Legge 2018 — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3642228/)
- Knuth/Liang TeX hyphenation — [TUG patterns](http://www.tug.org/tex-hyphen/) / [Liang 1983 thesis PDF](https://www.tug.org/docs/liang/liang-thesis.pdf)
- Widows / orphans — [Wikipedia](https://en.wikipedia.org/wiki/Widows_and_orphans) / [PrintCSS](https://printcss.net/articles/widows-and-orphans) / [W3C CSS 2.1 §13](https://www.w3.org/TR/2006/WD-CSS21-20060411/page.html)
- Butterick, *Practical Typography* — [Point size](https://practicaltypography.com/point-size.html) / [Line spacing](https://practicaltypography.com/line-spacing.html) / [Headings](https://practicaltypography.com/headings.html)
- Typographic scale — [Retinart](https://retinart.net/typography/typographicscale/) / [Pimp my Type](https://pimpmytype.com/line-length-line-height/)
- Block quotation typography — [Wikipedia](https://en.wikipedia.org/wiki/Block_quotation) / [SitePoint](https://www.sitepoint.com/typography-of-quotations/)
- Older readers & font size — [Frontiers review](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.931646/full)
- Legible Typography overview — [legible-typography.com](https://legible-typography.com/en/5-overview-of-research-type)
