# SHOOTRZ UI Modernization Report

## 1. Design System

Extended `src/constants/theme.ts` with a complete, structured design system while preserving the legacy `SHOOTRZ_THEME` and `COMPONENT_STYLES` exports for backward compatibility.

### New Exports Added

| Export | Contents |
|--------|----------|
| `colors` | Layered dark backgrounds (`bg.void` through `bg.overlay`), brand colors (orange, cyan, chrome), 5-tier score system, text hierarchy, border tokens, semantic colors |
| `typography` | Size scale (xs–4xl), weight scale (regular–black), lineHeight tokens, letter spacing tokens |
| `spacing` | 8pt grid (0–20) + semantic aliases (`screenPadding`, `cardPadding`, `sectionGap`, `itemGap`, `tabBarHeight`, `headerHeight`) |
| `radius` | Size scale (xs–full) + semantic aliases (`card`, `button`, `pill`, `badge`, `avatar`) |
| `glass` | Glassmorphism tokens for card, sheet, orange-tinted, and cyan-tinted surfaces |
| `animation` | Duration tokens (instant–deliberate) + spring easing configs (standard, snappy, bouncy) |
| `shadows` | sm, md, orange, and cyan shadow presets for React Native |

### Utility Functions

- `getScoreTier(score: number): ScoreTier` — maps 0–100 to elite/great/good/fair/poor
- `getScoreColor(score: number)` — returns `{ bg, text, glow }` for a score

### Legacy Compatibility

`SHOOTRZ_THEME` keys now alias into the new system values. Screens not yet migrated continue to work. New code imports directly from `{ colors, typography, spacing, ... }`.

---

## 2. New Components

| Component | File | Props | Purpose |
|-----------|------|-------|---------|
| `PrimaryButton` | `src/components/PrimaryButton.tsx` | `label, onPress, loading, disabled, size, variant, icon, fullWidth` | Main CTA button with haptics and spring animation feel |
| `SecondaryButton` | `src/components/SecondaryButton.tsx` | `label, onPress, variant, disabled` | Outlined/ghost/danger button |
| `IconButton` | `src/components/IconButton.tsx` | `icon, onPress, size, color, badge` | Circular icon button with optional notification badge |
| `ScoreRing` | `src/components/ScoreRing.tsx` | `score, size, label, animated, showTier` | Hero SVG circular progress ring (react-native-svg) with animated fill and count-up |
| `MetricCard` | `src/components/MetricCard.tsx` | `label, value, unit, score, trend, trendValue, description, onPress` | Glass card with left accent bar, score progress bar, and trend indicator |
| `StatCard` | `src/components/StatCard.tsx` | `icon, label, value, unit, subtitle, color` | Compact stat display for dashboard rows |
| `StreakBadge` | `src/components/StreakBadge.tsx` | `count, active` | Fire icon + count + "DAY STREAK" label with orange glow |
| `TierBadge` | `src/components/TierBadge.tsx` | `tier, size` | Pill-shaped score tier label, color-coded |
| `AnalysisCard` | `src/components/AnalysisCard.tsx` | `sessionId, date, score, thumbnail, duration, shotCount, onPress` | History list item with inline ScoreRing and TierBadge |
| `WorkoutCard` | `src/components/WorkoutCard.tsx` | `name, drillCount, estimatedMinutes, difficulty, progress, onPress` | Workout list item with animated progress bar |
| `ChatBubble` | `src/components/ChatBubble.tsx` | `message, role, timestamp, streaming` | Chat message bubble (user=orange tint, coach=cyan glass) with streaming cursor |
| `TypingIndicator` | `src/components/TypingIndicator.tsx` | — | 3 bouncing cyan dots with Coach J avatar |
| `CoachContextChip` | `src/components/CoachContextChip.tsx` | `sessionLabel, onDismiss` | Cyan pill showing coaching context above chat input |
| `SkeletonLoader` | `src/components/SkeletonLoader.tsx` | `width, height, radius, style` | Pulsing placeholder (opacity 0.3→0.7→0.3, 1200ms loop) |
| `ErrorState` | `src/components/ErrorState.tsx` | `message, onRetry` | Error display with retry CTA |
| `ProgressBar` | `src/components/ProgressBar.tsx` | `progress, color, height, animated, showPercent` | Animated fill bar with spring easing |
| `LoadingOverlay` | `src/components/LoadingOverlay.tsx` | `visible, message` | Full-screen dark modal with pulsing SHOOTRZ wordmark |
| `SectionHeader` | `src/components/SectionHeader.tsx` | `title, subtitle, action` | Section label with optional "See all →" link |
| `ScreenHeader` | `src/components/ScreenHeader.tsx` | `title, subtitle, backButton, rightAction, transparent` | Shared screen header with back button support |

---

## 3. Upgraded Components

| Component | Changes |
|-----------|---------|
| `EmptyState` | Removed LinearGradient card wrapper. Now uses flat dark bg with chrome icon (64px), centered layout, and new `action` prop (object with `label` + `onPress`). Preserved `actionText`/`onAction` backward compat via internal resolution. Uses new theme tokens. |
| `DrillCard` (in DrillsScreen) | Redesigned inline as part of DrillsScreen FlatList. Header gradient area with difficulty badge and duration pill. Footer with name + category pill. |
| `AnimatedStatCard` | Replaced by new `StatCard` component in HomeScreen. Old file preserved for backward compat but new screens use `StatCard`. |

---

## 4. Screens Redesigned

| Screen | Key Changes |
|--------|-------------|
| **SplashScreen** | `bg.void` background, ShootrzLogo with fade-in + scale spring, 3 pulsing orange dots, "PERFECT THE GAME" in brand.cyan at bottom |
| **LoginScreen** | Full dark bg, logo top section with cyan tagline, glass card auth form with elevated inputs, orange-glow focused inputs, shake animation on error, haptic feedback on submit/error, social login buttons restyled |
| **OnboardingScreen** | Step progress dots (orange active + elongated current), centered content with icon/title/subtitle, selection cards with orange tint on select + checkmark spring animation, slide transitions between steps |
| **UsernameScreen** | Centered layout, person-circle icon, elevated input, PrimaryButton CTA |
| **HomeScreen** | Time-of-day greeting + streak badge, hero stat card (orange glass, ScoreRing lg + tier badge), 3 StatCards row, full-width "Analyze Shot" CTA, Coach J card (cyan glass), recent sessions list with AnalysisCards, skeleton loading state |
| **MVPAnalysisScreen** | 4-phase UI: dashed upload zone with side selector pills → processing overlay with pulsing ring + cycling labels → results with ScoreRing hero (200px) + MetricCards grid + phase timeline bar + feedback cards + angle graph + overlay video + CTAs |
| **ProgressScreen** | Period selector pills (week/month/all), overall score card with ScoreRing + stats, LineChart with orange line, metric improvements grid with trend indicators, session history FlatList |
| **DrillsScreen** | Horizontal category + difficulty filter pills, 2-column FlatList grid with difficulty-colored headers, duration pills, category badges |
| **DrillDetailScreen** | Full-bleed colored header with difficulty badge + time badge + category icon, scrollable content with numbered steps + tip cards, sticky "Complete Drill" button at bottom |
| **WorkoutsScreen** | Filter tabs (All/Active/Completed), FlatList of WorkoutCards with progress bars, active workout orange border highlight |
| **ChatScreen** | Coach J header (cyan avatar + title + subtitle), CoachContextChip, inverted message list with ChatBubble + TypingIndicator, quick prompt chips, artifacts toggle, glass input row with orange send button |
| **ProfileScreen** | Avatar initials circle (64px, brand.orange), name + handle, edit profile touchable, 3 StatCards, preferences toggles, account actions (export, delete), sign-out danger button, edit modal with glass card |

---

## 5. Animations Added

| Animation | Library | Trigger | Details |
|-----------|---------|---------|---------|
| Score ring fill | `Animated` + `react-native-svg` | Analysis result load | Stroke-dashoffset 0→final over 800ms + number count-up |
| Skeleton pulse | `Animated` | Loading states | Opacity 0.3→0.7→0.3, 1200ms loop |
| Splash logo entrance | `Animated` | SplashScreen mount | Fade-in 600ms + scale 0.85→1.0 spring |
| Splash dots | `Animated` | SplashScreen mount | Sequential opacity pulse, staggered 200ms |
| Login form entrance | `Animated` | LoginScreen mount | Slide-up 50→0 + fade-in 600ms + logo scale spring |
| Login shake | `Animated` | Validation error | translateX oscillation (10→-10→6→-6→0) |
| Processing pulse | `Animated` | MVPAnalysis processing | Ring opacity 0.4→1→0.4, 1600ms loop |
| Processing labels | `setInterval` | MVPAnalysis processing | Cycle through 4 labels every 2 seconds |
| Typing dots | `Animated` | Chat streaming wait | 3 dots sequential bounce, staggered 150ms |
| Progress bar fill | `Animated.spring` | Progress change | Spring fill with damping:15, stiffness:150 |
| EmptyState entrance | `Animated` | Component mount | Slide-up 20→0 + fade-in 500ms |

---

## 6. Haptics Map

| Trigger | Haptic Type | Function |
|---------|-------------|----------|
| Tab switch | `selectionAsync()` | `hapticFeedback.selection()` |
| Filter pill selection | `selectionAsync()` | `hapticFeedback.selection()` |
| Toggle changes | `selectionAsync()` | `hapticFeedback.selection()` |
| Standard button tap | `impactAsync(Light)` | `hapticFeedback.light()` |
| Card selection | `impactAsync(Light)` | `hapticFeedback.light()` |
| Primary CTA tap | `impactAsync(Medium)` | `hapticFeedback.medium()` |
| Drill start / Record Video | `impactAsync(Medium)` | `hapticFeedback.medium()` |
| Score reveal moment | `impactAsync(Heavy)` | `hapticFeedback.heavy()` |
| Analysis complete | `notificationAsync(Success)` | `hapticFeedback.success()` |
| Drill completion | `notificationAsync(Success)` | `hapticFeedback.success()` |
| Profile save | `notificationAsync(Success)` | `hapticFeedback.success()` |
| Login error / validation | `notificationAsync(Warning)` | `hapticFeedback.warning()` |
| Chat stream error | `notificationAsync(Warning)` | `hapticFeedback.warning()` |
| Analysis failed | `notificationAsync(Error)` | `hapticFeedback.error()` |

---

## 7. Dependencies

| Package | Version | Justification |
|---------|---------|---------------|
| `expo-blur` | SDK 54 compatible | Required for glassmorphism BlurView effects. Ships with Expo SDK 54, no native rebuild needed. Managed workflow safe. |

No other new dependencies were added. All features use libraries already in `package.json`:
- `react-native-reanimated` ^4.1.3 (available for advanced animations)
- `expo-haptics` ~15.0.8 (tactile feedback)
- `react-native-svg` 15.12.1 (ScoreRing circular progress)
- `react-native-chart-kit` ^6.12.0 (Progress screen trend chart)
- `expo-linear-gradient` ~15.0.8 (gradient effects)
- `@expo/vector-icons` (Ionicons throughout)

---

## 8. Known Limitations

1. **Logo PNG missing**: `assets/shootrz-logo.png` is referenced by `ShootrzLogo.tsx` but the file does not exist (only a placeholder .txt). The app may show a broken image or crash on splash. The user needs to provide the actual logo asset.

2. **expo-blur not yet used in screens**: `expo-blur` was installed but BlurView is not currently rendering in any screen. It was planned for glass card backgrounds but `rgba()` overlays were used instead for performance safety. BlurView can be layered on top of the glass card backgrounds (max 2 per screen) in a future pass.

3. **react-native-reanimated**: While installed, the current implementation uses the built-in `Animated` API for all animations (which provides `useNativeDriver: true` for transform/opacity). A future pass could migrate to Reanimated's `useSharedValue` + `useAnimatedStyle` for gesture-driven interactions and more complex spring physics.

4. **DrillCard component file**: The `DrillCard.tsx` component file was not updated separately — the drill card UI is embedded inline in `DrillsScreen.tsx`. The original `DrillCard.tsx` file still exists but is not used by the new screens.

5. **Chart library**: `react-native-chart-kit` is used for the Progress screen. For more interactive charts (tap-to-show-value tooltips), a library like `victory-native` would be better, but was not added to avoid new dependencies.

6. **Offline handling**: No offline data caching or queue was added. Error states display retry buttons but there is no automatic retry or background sync.

---

## 9. Accessibility Audit

### Implemented

- `accessibilityRole="button"` on all touchable elements (PrimaryButton, SecondaryButton, IconButton, tab bar items)
- `accessibilityLabel` on interactive elements (buttons, icons, send button, analysis cards)
- `accessibilityState={{ disabled }}` on buttons
- Minimum touch targets: all buttons have 48pt minimum height, icon buttons are 40–48px
- Color contrast: `text.primary` (#F0F4F8) on `bg.primary` (#0D1117) passes WCAG AA (contrast ratio ~14:1)
- `text.secondary` (#8B95A3) on `bg.primary` passes WCAG AA (contrast ratio ~5.2:1)
- Color is never the sole indicator — tier badges use text labels alongside color

### Gaps

- `accessibilityHint` is not set on all non-obvious actions (e.g., drill cards, analysis cards)
- Chart data is not accessible to screen readers
- Streaming chat content updates are not announced to assistive technology
- Custom focus order management is not implemented for modals

---

## 10. Performance Notes

### FlatList Optimization

- `keyExtractor` uses stable unique IDs (session IDs, drill IDs) — never array indices
- `removeClippedSubviews={true}` on DrillsScreen grid and WorkoutsScreen list
- `showsVerticalScrollIndicator={false}` on all ScrollViews for clean appearance
- `keyboardShouldPersistTaps="handled"` on ChatScreen and LoginScreen

### Blur Usage

- **0 BlurView layers** currently rendered (within the 2-per-screen budget)
- Glass effects use `rgba()` backgrounds instead, which are zero-cost
- BlurView can be added selectively where needed without performance risk

### Memo Usage

- `useMemo` for: `filteredDrills` (DrillsScreen), `filteredSessions` + `avgScore` + `chartData` (ProgressScreen), `contextLabel` (ChatScreen), `initials` (ProfileScreen), `overlayUri` (MVPAnalysisScreen)
- `useCallback` for: `send` + `handleClear` + `renderItem` (ChatScreen), `loadSessions` (ProgressScreen), `loadData` (HomeScreen)

### Images

- All images specify explicit dimensions (no auto-sizing)
- `resizeMode="cover"` used for overlay video

---

## 11. Next Steps (v2)

1. **BlurView glassmorphism**: Add `expo-blur` BlurView beneath glass card backgrounds on HomeScreen hero card and ChatScreen input row for true glassmorphism depth.

2. **Reanimated migration**: Replace `Animated` API with `react-native-reanimated` shared values for gesture-driven interactions (press scale, swipe-to-dismiss, drag-to-reorder drills).

3. **Lottie celebrations**: Add `lottie-react-native` for score reveal celebrations (confetti on Elite tier, fireworks on personal best).

4. **AR court overlay**: Integrate camera-based AR overlay showing ideal shooting form silhouette during recording.

5. **Share to socials**: Add score card image generation (react-native-view-shot) + share sheet for Instagram Stories / Twitter.

6. **Apple Watch companion**: Build a watchOS app showing live session stats, streak count, and quick-start drill reminders.

7. **Skeleton screen fidelity**: Create screen-specific skeleton compositions that match the exact layout silhouette (3 AnalysisCards skeleton, stat cards skeleton, etc.).

8. **Onboarding video**: Replace the static onboarding steps with short auto-playing demo videos showing the analysis flow.

9. **Pull-to-refresh animations**: Custom pull-to-refresh indicator with basketball bounce animation instead of the default spinner.

10. **Micro-interactions**: Add subtle parallax scroll effects on the HomeScreen hero card, and spring-based tab bar icon bounce on selection.

11. **Light mode**: Implement a full light theme variant with appropriate contrast adjustments for outdoor court use.
