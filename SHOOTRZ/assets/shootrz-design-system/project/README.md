# SHOOTRZ Design System

**SHOOTRZ** is an AI-assisted basketball shooting analysis mobile app. Players record their shot, and the app analyzes biomechanics using a computer vision pipeline (YOLOv8 + pose estimation), returning a score, metric breakdown, and personalized coaching feedback. The tagline is **"PERFECT THE GAME."**

## Products

| Surface | Description |
|---|---|
| **Mobile App** | React Native (Expo) iOS/Android app — the primary product |
| **FastAPI Backend** | Python backend with YOLOv8/pose pipeline, Supabase data/auth |

## Sources

- **Codebase**: `Grad/SHOOTRZ/` (local mount via File System Access API)
- **GitHub Repo**: `badrwakid/SHOOTRZ` (ref: `aa114be82b94`)
- **Logo**: `assets/shootrz-logo.png` (uploaded directly)
- No Figma link was provided.

---

## CONTENT FUNDAMENTALS

### Voice & Tone
- **Direct, motivational, performance-obsessed.** Every word earns its place.
- Speaks to athletes: confident, peer-level ("What's up! I'm Coach J…"), not corporate.
- Short bursts of all-caps for emphasis and labels: `PERFECT THE GAME`, `ANALYZE SHOT`, `LAST SESSION`.
- Numbers and scores are prominent — data is celebrated, not buried.
- Second-person ("Your journey starts here", "Ask me anything about your game").
- No filler copy; empty states are honest and action-forward ("Your journey starts here / Analyze your first shot to see your score").

### Casing
- **ALL CAPS**: tab labels, button text, section labels, the tagline, tier badges (`ELITE`, `GREAT`).
- **Title Case**: screen titles, card titles, coach name "Coach J".
- **Sentence case**: body copy, subtitles, inline coach messages.

### Emoji
- **Not used** anywhere in the UI. Zero emoji.

### Numbers
- Scores are rounded integers (0–100).
- Displayed large, bold, and without a % suffix in hero positions.
- Metric values use one decimal place (e.g. `87.3`).

### Examples
> "Good morning, Marcus" / "PERFECT THE GAME" / "Start your basketball journey" / "Fix my follow-through" / "Give me a drill plan"

---

## VISUAL FOUNDATIONS

### Color System
- **Backgrounds**: Layered near-black system — void `#080A0E` → primary `#0D1117` → secondary `#13181F` → elevated `#1A2030` → overlay `#1F2737`. Always dark; no light mode.
- **Brand Orange** `#E8521A` — primary CTA, score glows, streak indicators. With glow: `#E8521A40`.
- **Brand Cyan** `#00D4FF` — secondary accent, Coach J, links, active states. With glow: `#00D4FF30`.
- **Chrome** `#C8D0DC` — hero score numbers, silver metallic text accent.
- **Score tier colors**: Elite `#FFD700` (gold) / Great `#22C55E` / Good `#3B82F6` / Fair `#F59E0B` / Poor `#EF4444`.
- **Semantic**: Success `#22C55E`, Warning `#F59E0B`, Error `#EF4444`, Info `#3B82F6`.

### Typography
- **Font family**: React Native system fonts (San Francisco on iOS, Roboto on Android). No custom typeface is installed in the codebase.
- **Design system sub**: Use **Barlow Condensed** for display/numeric heroes and **DM Sans** for body (Google Fonts substitutes — see caveat below).
- Weight scale: 400 regular → 500 medium → 600 semibold → 700 bold → 800 heavy → 900 black.
- Size scale: 11/13/15/17/20/24/30/38/48px.
- Letter spacing: hero labels use `widest` (2.0px), buttons use `widest`, body is `normal` (0).
- Labels always UPPERCASE with wide tracking. Body is sentence case with normal tracking.

### Spacing & Layout
- 4px base unit. Scale: 4/8/12/16/20/24/28/32/40/48/64/80px.
- Screen padding: 16px. Card padding: 16px. Section gap: 24px. Item gap: 12px.
- Tab bar height: 84px. Header height: 56px.

### Cards & Surfaces
- Cards: `background #13181F`, `borderRadius 16px`, `border rgba(255,255,255,0.12)`, medium drop shadow.
- **Glass orange card**: `background rgba(232,82,26,0.12)`, `border rgba(232,82,26,0.25)` — used for hero/score highlights.
- **Glass cyan card**: `background rgba(0,212,255,0.08)`, `border rgba(0,212,255,0.20)` — used for Coach J.
- **Glass sheet**: `background rgba(8,10,14,0.85)`, `border rgba(255,255,255,0.06)`, `borderRadius 24px` — modals/bottom sheets.
- Press state: `scale(0.98)` via spring animation (not opacity change).
- Hover/focus: no web hover states in native; active opacity `0.85`.

### Borders
- `subtle`: `rgba(255,255,255,0.08)` — dividers, header lines.
- `default`: `rgba(255,255,255,0.12)` — card borders.
- `strong`: `rgba(255,255,255,0.20)` — emphasized borders.
- `brand`: `rgba(232,82,26,0.40)` — orange focus/brand borders.
- `cyan`: `rgba(0,212,255,0.30)` — cyan accent borders.

### Shadows
- **sm**: `0 2px 4px rgba(0,0,0,0.3)`
- **md**: `0 4px 8px rgba(0,0,0,0.4)`
- **orange glow**: `0 4px 12px rgba(232,82,26,0.35)` — applied to primary CTA buttons.
- **cyan glow**: `0 4px 12px rgba(0,212,255,0.25)` — applied to cyan variant buttons.

### Border Radius
- `xs 4` / `sm 8` / `md 12` / `lg 16` / `xl 20` / `2xl 24` / `3xl 32` / `full 9999`
- Cards: 16px. Buttons: 12px. Pills/badges: 9999px. Modals: 24px.

### Animations
- Spring physics: `damping 15, stiffness 150, mass 1` (standard). Snappy: `damping 20, stiffness 300`. Bouncy: `damping 10, stiffness 100`.
- Duration scale: instant 100ms / fast 200ms / normal 300ms / slow 500ms / deliberate 800ms.
- Intro animations: fade + slide-up (600ms) + logo spring scale from 0.85→1.
- Haptic feedback on every interaction (light/medium/heavy/success/warning).

### Backgrounds
- Solid near-black. No textures, no patterns, no gradients as backgrounds.
- Glow effects via translucent colored overlays (not actual gradients).
- No full-bleed imagery used in UI.

### Imagery
- No decorative photography in the app UI itself.
- Score rings and animated loading basketball (`LoadingBasketball.tsx`) are the primary brand illustrations (drawn in code).

---

## ICONOGRAPHY

- **Icon library**: `@expo/vector-icons` → **Ionicons** exclusively.
- All icons are referenced by semantic names mapped in `src/utils/iconMapper.ts`.
- **No SVG icon files** are stored as assets; all icons rendered via Ionicons font.
- **No emoji** used anywhere.
- **No PNG icons** beyond the app icon/splash assets.
- Key icon semantics: `basketball` → home/sessions, `stats-chart` → progress, `chatbubbles` → Coach J, `videocam` → analyze, `barbell` → workouts, `trophy` → best score, `flame` → streak.
- Icon sizes: 16px (small), 18px (default), 20px (medium), 24px (large).
- Icon tint follows context: orange for primary, cyan for secondary, `chromeMid #8B95A3` for neutral.

---

## FILE INDEX

```
README.md                     ← You are here
SKILL.md                      ← Agent skill definition
colors_and_type.css           ← CSS custom properties for colors + typography
assets/
  shootrz-logo.png            ← Primary horizontal logo
preview/
  colors-bg.html              ← Background color swatches
  colors-brand.html           ← Brand orange + cyan palette
  colors-semantic.html        ← Score tier + status colors
  type-scale.html             ← Typography size + weight scale
  type-specimens.html         ← Heading/body/label specimens
  spacing-tokens.html         ← Spacing + radius tokens
  shadows-borders.html        ← Shadow + border system
  components-buttons.html     ← Button variants
  components-cards.html       ← Card variants + glass surfaces
  components-badges.html      ← Tier badges + streak badges
  components-inputs.html      ← Input fields + form elements
  brand-logo.html             ← Logo display
ui_kits/
  app/
    README.md                 ← App UI kit docs
    index.html                ← Interactive prototype (Home → Chat → Progress)
    Components.jsx            ← Core UI components
    Screens.jsx               ← Screen implementations
```
