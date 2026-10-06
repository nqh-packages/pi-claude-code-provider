---
name: Claude Code provider for Pi
description: Concourse lettering, shaded charcoal materials and amber controls.
colors:
  primary: "#ffb000"
  neutral-bg: "#171a1b"
  recessed: "#101314"
  base-200: "#111415"
  ink: "#f2f2ef"
  muted: "#b4bbbc"
  steel: "#727c7e"
  rule: "#41494b"
  flap: "#1e2223"
typography:
  display:
    fontFamily: "Rajdhani, sans-serif"
    fontSize: "clamp(3rem, 6.7vw, 6rem)"
    fontWeight: 600
    lineHeight: 1.24
  display-mobile:
    fontFamily: "Rajdhani, sans-serif"
    fontSize: "clamp(1.7rem, 9vw, 2.8rem)"
    fontWeight: 600
    lineHeight: 1.95
  headline:
    fontFamily: "Rajdhani, sans-serif"
    fontSize: "clamp(2.2rem, 3.5vw, 3.2rem)"
    fontWeight: 600
    lineHeight: 1.05
  title:
    fontFamily: "Rajdhani, sans-serif"
    fontSize: "1.7rem"
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: "Barlow, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.55
  action:
    fontFamily: "Rajdhani, sans-serif"
    fontSize: "1.3rem"
    fontWeight: 600
    lineHeight: 1
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.7
rounded:
  cell: "2px"
  control: "3px"
spacing:
  micro: "2px"
  detail: "4px"
  compact: "0.75rem"
  content: "1rem"
  roomy: "1.5rem"
  group: "2rem"
  column: "3.5rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral-bg}"
    typography: "{typography.action}"
    rounded: "{rounded.control}"
    padding: "0 1.2rem"
  button-primary-hover:
    backgroundColor: "#ffc044"
  button-copy:
    backgroundColor: "#1a1e1f"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 0.65rem"
    height: "2.3rem"
  link-secondary:
    textColor: "{colors.ink}"
  navigation:
    textColor: "{colors.ink}"
  disclosure:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "0px"
  code-panel:
    backgroundColor: "{colors.recessed}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
---

# Design System: Claude Code provider for Pi

## Overview

**Creative North Star: "The Concourse"**

Condensed white lettering sits on matte charcoal flaps inside a brushed, recessed steel bezel. Amber marks actions and attention. Below the board, thin rules and aligned columns carry the reading rhythm without repeating the hero's material treatment.

The system pairs a physical display with plain, readable documentation. Painter-generated shaded raster artwork supplies the board's material detail; live text supplies its message. Controls stay compact and nearly square. The board is static, so its mechanical appearance does not delay reading.

**Key Characteristics:**
- Shaded charcoal flaps and a brushed steel bezel.
- Condensed display lettering with a separate body face.
- Amber controls and attention marks against dark neutrals.
- Ruled reading sections with responsive columns.
- Live text, visible keyboard focus and manual copy recovery.

This record applies to the static website under `site/`, not to Pi or provider runtime interfaces. The approved world is concourse/departure-board, `seed273011f1`. [PRODUCT.md](PRODUCT.md) owns product truth; the [landing-page surface brief](site/.impeccable/surfaces/site-src-pages-index-astro.md) owns its story and composition. [site.css](site/src/styles/site.css), especially `:root` and the `concourse` theme, owns the implemented values. [index.astro](site/src/pages/index.astro) owns markup and accessible labels. The frontmatter records their visual contract; it is not a separate runtime theme.

## Colors

One amber accent sits against charcoal, near-white lettering and cool gray rules. The frontmatter retains the source's hex values.

### Primary
- Signal amber, `primary`, maps to `--amber` and the theme's primary role. It fills the install action and marks the final destination dot, warning symbol, selection, copy status, link hover and keyboard focus.

**The Amber Signal Rule.** Use amber for an action or an attention state. Ordinary body text and structural rules stay neutral.

### Neutral
- Charcoal ground, `neutral-bg`, is the page background and primary-action foreground.
- Recessed charcoal, `recessed`, fills the board face and command containers.
- Deep charcoal, `base-200`, fills the ownership diagram and is the selection/skip-link foreground.
- Lettering white, `ink`, maps to `--ink` and base-content. It carries headings, live board letters and emphasized copy.
- Reading gray, `muted`, maps to `--muted`. It carries supporting prose and footer links.
- Steel gray, `steel`, maps to `--steel`. It marks container borders, section rules and diagram arrows, not body text.
- Divider gray, `rule`, maps to `--rule`. It separates requirements, steps, disclosures and credit rows.
- Flap charcoal, `flap`, maps to `--flap`. It backs the raster cells and fills the small brand cells and step numbers.

Component-local fills and the lighter primary hover remain with their selectors rather than becoming another palette. The theme declares additional semantic aliases for daisyUI, but the page does not establish distinct secondary, success or error color systems. The sidecar's synthesized tonal ramps are panel previews, not additional approved CSS colors.

## Typography

**Display Font:** Rajdhani, with sans-serif fallback.
**Body Font:** Barlow, with sans-serif fallback.
**Label/Mono Font:** Rajdhani for labels; the platform monospace stack for code only.

**Character:** Rajdhani's narrow lettering fits the flap grid, headings and controls. Barlow carries continuous prose without making the whole page look like a terminal. The font imports at the top of `site.css` self-host the display weight and the body weights actually used.

### Hierarchy
- **Display:** The `display` role belongs to live board lettering. The `display-mobile` role applies at the narrow breakpoint; its taller line box preserves the upright cell silhouette.
- **Headline:** Section headings use `headline` and balanced wrapping. At the narrow breakpoint they use `2.3rem`.
- **Title:** Step and prerequisite headings use `title`. Narrow layouts reduce them to `1.5rem`; the ownership and credit headings have their own component sizes.
- **Body:** The `body` role sets the default. At the narrow breakpoint it becomes `1.0625rem`. Longer setup and credit prose has a `75ch` cap; the board explanation has a `60ch` cap and its own larger size.
- **Action:** The shared button role uses `action`. Navigation, secondary links and copy controls retain their smaller selector-specific sizes.
- **Code:** Preformatted commands use `code`. Inline code scales with its surrounding text and may wrap anywhere; preformatted code scrolls horizontally instead of wrapping.

**The Live Lettering Rule.** Keep board letters as text. The heading supplies one complete accessible label, while its decorative rows are hidden from assistive technology. Material artwork contains no message.

## Layout

The shared page wrapper is centered and capped at `1320px`. Its width is `min(100% - 6rem, 1320px)` on wide screens, `calc(100% - 3rem)` at `850px` and below, and `calc(100% - 1.5rem)` at `560px` and below. These are the source's two content breakpoints, not framework-default breakpoints.

Reading sections use rules and asymmetric columns. Setup and credits share a wide `19rem` label column, flexible content and the `column` gap. Setup becomes one column at the middle breakpoint. Credit rows use a smaller label column there and become one column at the narrow breakpoint. The ownership diagram changes from two parties with a central connection column to a vertical stack at the narrow breakpoint.

Recurring spacing uses small gaps inside controls and larger gaps between reading groups. The frontmatter records repeated steps, not a claim that every measurement follows a strict base grid. Document sections have `5.5rem` top spacing on wide screens and `3.5rem` on narrow screens. Paragraphs and linked details stay closer to their headings than the next section does.

**The Ruled Reading Rule.** Separate related reading groups with thin neutral rules and alignment. Reserve the raster enclosure for the signature board rather than wrapping every section in a material card.

The landing-page board's three fifteen-cell rows and copy/action placement belong to its surface brief and `index.astro`'s `offer`. At the middle breakpoint its footer stacks and actions sit in a row; at the narrow breakpoint actions stack again. The fifteen columns remain intact at both scales. This is the implemented signature composition, not a mandatory grid for every future page.

## Elevation & Depth

Most of the website is flat. Borders, darker fills and spacing distinguish code, notices and reading groups. The `concourse` theme sets daisyUI depth and noise to zero. The board alone has a soft mounting shadow, `filter: drop-shadow(0 12px 13px #0005)`, and shaded material detail.

The board uses **Painter-generated shaded raster material**, not photography. [board-bezel.webp](site/src/assets/materials/board-bezel.webp) supplies brushed grain, edge light and the recessed rim. [blank-flap.webp](site/src/assets/materials/blank-flap.webp) supplies matte grain, shaded halves, the center seam and hinge ends. These lossless WebP assets are the material owners; `site.css` owns their placement.

The bezel is a border image on the board's background pseudo-element, with `72 fill` source slices, `stretch` repeat and an `11px` rendered ring. At the narrow breakpoint the ring is `7px`. Each upright flap stretches its artwork to `100% 100%` over the `flap` fallback. A separate one-pixel line across the live glyph continues the image seam through the lettering. It is not another CSS material layer.

**The Material Owns Shading Rule.** Let the accepted raster artwork carry grain, recesses and hinge shading. CSS supplies layout, solid fallbacks, the mounting shadow and the seam through live letters.

## Shapes

Forms are nearly square. The `cell` radius recurs on flap cells, step numbers and the connection label. The `control` radius recurs on buttons, code containers, the board face and the ownership panel. The outer board has its own `6px` radius. These small radii belong to the concourse world; generic pill and soft-card geometry is not part of this implementation.

Thin borders and open-ended horizontal rules carry most boundaries. The source uses inline SVG geometry, with a shared `1.7` stroke width and `1.35rem` base size; smaller or larger variants stay with their components. It does not use an icon font or decorative glyphs.

## Components

### Buttons and secondary links

The install action is an amber daisyUI button with charcoal text, the shared action type, `3.3rem` minimum height, `1.2rem` inline padding and the control radius. Its label and trailing SVG sit at opposite ends. Fine-pointer hover uses the lighter fill recorded in `button-primary-hover`.

Copy controls are dark outlined daisyUI buttons with white text. Their wide-screen height is recorded in `button-copy`; the narrow layout increases it to `2.75rem`, increases inline padding and spreads the controls across the toolbar. daisyUI supplies default pressed and disabled mechanics; `site.css` owns these visual overrides. Reduced-motion mode removes button transitions. There is no custom loading spinner.

Secondary reading actions are underlined text links, not competing filled buttons. Fine-pointer hover turns links amber. The shared keyboard rule outlines anchors, buttons, summaries, preformatted blocks and main with a three-pixel amber ring and a five-pixel offset. The command block uses an inset offset so its ring stays inside the panel.

### Navigation

The header pairs the small split-cell brand mark with plain Rajdhani links. The source link has a neutral divider on wide screens. At the narrow breakpoint, local section links hide; the brand and source link remain. Section anchors and the keyboard skip link retain native navigation. There is no mobile menu or theme switcher.

### Command containers and copy feedback

Command containers use the recessed fill and control radius. The larger panel has a steel border, a slightly lighter toolbar, neutral separators and a reading footnote. The smaller command block uses the divider-gray border. Its preformatted text is keyboard-focusable and horizontally scrollable.

[copy-code.ts](site/src/scripts/copy-code.ts) owns progressive enhancement. Copy and selection buttons start hidden and become available only when their required elements exist. Copy disables its button during the clipboard attempt and reports success or failure in a polite live region. The selection action selects the command text and focuses the block for manual copying. Without JavaScript, commands and manual-copy guidance remain visible. These controls copy or select text; they do not execute it.

### Disclosures

Native `details` and `summary` carry the setup and account-policy disclosures. They have transparent backgrounds, top/bottom divider rules, square corners and Rajdhani summary text. The open state adds bottom content padding. daisyUI supplies the disclosure mechanics and reduced-motion-aware content transitions; the source disables the chevron transition. Essential limits remain in visible copy outside the disclosure.

### Reading groups and ownership diagram

Requirements use aligned definition rows. Setup steps use small numbered cells because sequence is meaningful. Credits use ruled label/content rows. The ownership diagram uses two text columns and drawn directional arrows on deep charcoal. It explains an actual boundary rather than adding a decorative illustration. None of these patterns establishes a general card, input or chip library.

### Split-flap board

The board is the signature component. Its live heading, raster cells, recessed face and bezel work together; blank cells are intentional spacing, not missing data. The final destination dot is amber. The small brand mark repeats the split-cell silhouette with solid fills and a seam, without duplicating the large board artwork.

The board has no autoplay, flip animation or entrance sequence. Keep the default readable immediately. The full rendered board is owned by the site, including its asset imports; the sidecar samples its existing controls and reading components without embedding a second copy of the raster assets.

## Do's and Don'ts

### Do:
- Do keep Rajdhani for display and controls, Barlow for prose, and monospace for actual commands.
- Do preserve live board lettering, its complete accessible label and the accepted raster material owners.
- Do keep keyboard focus visible and leave a manual selection path when clipboard access fails.
- Do use rules and responsive columns to organize reading content without repeating the hero enclosure.

### Don't:
- Don't bake the headline into artwork or let decorative rows replace the accessible heading.
- Don't re-create raster grain, recessed edges or hinges with CSS gradients and procedural overlays.
- Don't treat synthesized sidecar tonal ramps or unused theme aliases as additional brand accents.
- Don't infer an input, chip, modal or generic card system from this landing page.

Not canonized: unused theme aliases, preview-only tonal ramps and one-page composition measurements do not establish additional reusable design rules.
