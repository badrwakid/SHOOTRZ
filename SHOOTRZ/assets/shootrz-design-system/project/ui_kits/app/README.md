# SHOOTRZ App UI Kit

Pixel-faithful React recreation of the SHOOTRZ mobile app (iOS).

## Screens
- **Login** — Email/password sign-in, sign-up toggle, social auth buttons
- **Home** — Greeting header, hero score card, stats row, Analyze Shot CTA, Coach J card, recent sessions
- **Progress** — Period selector pills, score ring, score chart, session history
- **Coach J (Chat)** — AI coaching chat interface with quick chips, streaming bubbles
- **Profile** — User stats, settings rows, sign out

## Usage
Open `index.html` in a browser. The prototype is a clickable mobile frame.

## Components (Components.jsx)
- `ScoreRing` — animated SVG ring with score value
- `TierBadge` — color-coded tier label (ELITE/GREAT/GOOD/FAIR/POOR)
- `StreakBadge` — orange flame streak counter
- `StatCard` — icon + value + label card
- `PrimaryButton` — orange/cyan/ghost/danger variants
- `ChatBubble` — user/coach message bubble
- `AnalysisCard` — session summary row card
- `TabBar` — 5-tab bottom navigation
- `ScreenHeader` — greeting + tagline + streak
- `SectionHeader` — title + optional action link

## Font Note
Uses **Barlow Condensed** (display/numeric) + **DM Sans** (body/UI) as web substitutes for the app's native system fonts.

## Icon Note
Uses inline SVGs matching Ionicons semantics. The native app uses `@expo/vector-icons` Ionicons.
