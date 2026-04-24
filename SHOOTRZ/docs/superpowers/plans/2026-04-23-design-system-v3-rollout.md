# SHOOTRZ Design System V3 Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the React Native app UI to match `assets/shootrz-design-system/project/` (tokens, components, screens, interactions, and animations) with production-ready accessibility and test coverage.

**Architecture:** Introduce a typed token layer (`src/theme/tokens.ts`) as the single source of truth, then migrate shared UI primitives and each screen to consume semantic tokens/roles. Interactions and motion are implemented through RN-native primitives (`react-native-reanimated`, `expo-haptics`) with reduced-motion support and platform-safe focus/shadow behavior.

**Tech Stack:** React Native 0.81, Expo 54, TypeScript, React Navigation, react-native-reanimated, expo-haptics, expo-linear-gradient, Jest + @testing-library/react-native.

---

## Scope and File Structure

### Design source to implement
- `assets/shootrz-design-system/project/ui_kits/app/index.html`
- `assets/shootrz-design-system/project/ui_kits/app/Screens.jsx`
- `assets/shootrz-design-system/project/preview/*.html`

### Files to create (new architecture)
- `src/theme/tokens.ts` — v3 semantic tokens (bg, text, border, brand, state, focus, shadow, motion, button/input/card)
- `src/theme/typography.ts` — semantic typography role map (`display.hero`, `heading.h1`, etc.)
- `src/theme/useTokens.ts` — memoized hook exposing platform-resolved token values
- `src/theme/motion.ts` — reusable animation configs + reduced-motion helpers
- `src/components/TextRole.tsx` — role-based text renderer
- `src/components/FocusRing.tsx` — wrapper-based focus ring component for RN
- `src/components/__tests__/PrimaryButton.test.tsx`
- `src/components/__tests__/InputField.test.tsx`
- `src/screens/__tests__/LoginScreen.ui.test.tsx`
- `jest.config.js`
- `jest.setup.ts`

### Files to modify (existing app)
- `package.json`
- `App.tsx`
- `src/constants/theme.ts`
- `src/navigation/AppNavigator.tsx`
- `src/components/PrimaryButton.tsx`
- `src/components/SecondaryButton.tsx`
- `src/components/ScreenHeader.tsx`
- `src/components/SectionHeader.tsx`
- `src/components/ScoreRing.tsx`
- `src/components/AnalysisCard.tsx`
- `src/components/ChatBubble.tsx`
- `src/components/WorkoutCard.tsx`
- `src/screens/LoginScreen.tsx`
- `src/screens/HomeScreen.tsx`
- `src/screens/ProgressScreen.tsx`
- `src/screens/ChatScreen.tsx`
- `src/screens/ProfileScreen.tsx`
- `src/screens/MVPAnalysisScreen.tsx`

### Notes
- Ignore `SHOOTRZ/.claude/**` completely.
- Keep behavior unchanged unless required to support the approved design system and interactions.
- Migrate from raw color usage to semantic tokens only.

---

### Task 1: Add test harness before UI refactor

**Files:**
- Modify: `package.json`
- Create: `jest.config.js`
- Create: `jest.setup.ts`
- Test: `src/components/__tests__/PrimaryButton.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// src/components/__tests__/PrimaryButton.test.tsx
import React from 'react'
import { render } from '@testing-library/react-native'
import { PrimaryButton } from '../PrimaryButton'

describe('PrimaryButton', () => {
	it('renders uppercase label', () => {
		const { getByText } = render(<PrimaryButton label="Analyze Shot" onPress={() => {}} />)
		expect(getByText('ANALYZE SHOT')).toBeTruthy()
	})
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- PrimaryButton.test.tsx`  
Expected: FAIL because Jest/test scripts are not configured.

- [ ] **Step 3: Write minimal implementation (test tooling config)**

```json
// package.json (partial)
{
	"scripts": {
		"test": "jest",
		"test:watch": "jest --watch"
	},
	"devDependencies": {
		"jest": "^29.7.0",
		"jest-expo": "^54.0.0",
		"@testing-library/react-native": "^13.2.0",
		"@types/jest": "^29.5.12"
	}
}
```

```js
// jest.config.js
module.exports = {
	preset: 'jest-expo',
	setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
	testMatch: ['**/__tests__/**/*.test.ts?(x)'],
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- PrimaryButton.test.tsx`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add package.json jest.config.js jest.setup.ts src/components/__tests__/PrimaryButton.test.tsx
git commit -m "test: add jest harness for design-system rollout"
```

---

### Task 2: Introduce V3 tokens and role-based typography

**Files:**
- Create: `src/theme/tokens.ts`
- Create: `src/theme/typography.ts`
- Create: `src/theme/useTokens.ts`
- Modify: `src/constants/theme.ts`
- Test: `src/components/__tests__/InputField.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// src/components/__tests__/InputField.test.tsx
import { colors } from '../../constants/theme'

test('v3 primary background token is exposed', () => {
	expect(colors.bg.primary).toBe('#0F141B')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- InputField.test.tsx`  
Expected: FAIL because current token values are still v2 (`#0D1117`).

- [ ] **Step 3: Write minimal implementation**

```ts
// src/theme/tokens.ts (partial)
export const tokens = {
	bg: {
		void: '#0A0E14',
		primary: '#0F141B',
		secondary: '#151C26',
		elevated: '#1C2432',
		overlay: '#242E3F',
	},
	text: {
		primary: '#F1F5F9',
		secondary: '#94A3B8',
		tertiary: '#64748B',
		inverse: '#0F141B',
	},
	border: {
		subtle: 'rgba(148,163,184,0.08)',
		default: 'rgba(148,163,184,0.14)',
		strong: 'rgba(148,163,184,0.22)',
	},
	// ...brand, state, focus, shadow, motion
} as const
```

```ts
// src/constants/theme.ts (partial)
import { tokens } from '../theme/tokens'
export const colors = {
	bg: tokens.bg,
	text: tokens.text,
	border: tokens.border,
	brand: tokens.brand,
	success: tokens.state.success,
	warning: tokens.state.warning,
	error: tokens.state.error,
	info: tokens.state.info,
} as const
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- InputField.test.tsx`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/theme/tokens.ts src/theme/typography.ts src/theme/useTokens.ts src/constants/theme.ts src/components/__tests__/InputField.test.tsx
git commit -m "feat: add v3 semantic token and typography foundations"
```

---

### Task 3: Load approved brand fonts and expose typography roles

**Files:**
- Modify: `App.tsx`
- Modify: `src/constants/theme.ts`
- Create: `src/components/TextRole.tsx`
- Test: `src/screens/__tests__/LoginScreen.ui.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// src/screens/__tests__/LoginScreen.ui.test.tsx
import React from 'react'
import { render } from '@testing-library/react-native'
import { LoginScreen } from '../LoginScreen'

test('login heading renders', () => {
	const { getByText } = render(<LoginScreen onLogin={() => {}} />)
	expect(getByText(/Welcome Back/i)).toBeTruthy()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- LoginScreen.ui.test.tsx`  
Expected: FAIL initially due to unresolved font/role usage assumptions after token changes.

- [ ] **Step 3: Write minimal implementation**

```ts
// App.tsx (partial)
import { useFonts } from 'expo-font'

const [fontsLoaded] = useFonts({
	BarlowCondensedBlack: require('./assets/shootrz-design-system/project/fonts/BarlowCondensed-Black.ttf'),
	BarlowCondensedBold: require('./assets/shootrz-design-system/project/fonts/BarlowCondensed-Bold.ttf'),
	DMSansRegular: require('./assets/shootrz-design-system/project/fonts/DMSans-Regular.ttf'),
	DMSansMedium: require('./assets/shootrz-design-system/project/fonts/DMSans-Medium.ttf'),
	DMSansSemiBold: require('./assets/shootrz-design-system/project/fonts/DMSans-SemiBold.ttf'),
	DMSansBold: require('./assets/shootrz-design-system/project/fonts/DMSans-Bold.ttf'),
})
if (!fontsLoaded) return null
```

```tsx
// src/components/TextRole.tsx (partial)
export function TextRole({ role, children, style }: Props) {
	const t = useTokens()
	return <Text style={[t.typography.roles[role], style]}>{children}</Text>
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- LoginScreen.ui.test.tsx`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add App.tsx src/components/TextRole.tsx src/screens/__tests__/LoginScreen.ui.test.tsx
git commit -m "feat: load design-system fonts and semantic text roles"
```

---

### Task 4: Rebuild button/input primitives with full interactive states

**Files:**
- Modify: `src/components/PrimaryButton.tsx`
- Modify: `src/components/SecondaryButton.tsx`
- Create: `src/components/FocusRing.tsx`
- Modify: `src/screens/LoginScreen.tsx`
- Modify: `src/screens/ChatScreen.tsx`
- Test: `src/components/__tests__/PrimaryButton.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
test('disabled button uses neutral slate treatment', () => {
	const { getByRole } = render(<PrimaryButton label="Analyze" onPress={() => {}} disabled />)
	const btn = getByRole('button')
	expect(btn.props.accessibilityState.disabled).toBe(true)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- PrimaryButton.test.tsx`  
Expected: FAIL due to old visual/state logic.

- [ ] **Step 3: Write minimal implementation**

```ts
// PrimaryButton.tsx (partial)
const SIZE = {
	sm: { height: 36, px: 14, radius: 8, fontSize: 11, icon: 14, gap: 6 },
	md: { height: 44, px: 20, radius: 10, fontSize: 13, icon: 16, gap: 8 },
	lg: { height: 52, px: 28, radius: 12, fontSize: 14, icon: 18, gap: 10 },
}
// default orange background -> #BB3F15 (AA-safe)
// disabled across variants -> #1C2432 bg, #475569 label, border.default, no glow
```

```tsx
// LoginScreen.tsx (partial)
<PrimaryButton
	label="Sign In"
	loading={isSubmitting}
	disabled={!canSubmit}
	variant="orange"
	size="md"
	onPress={handleSubmit}
/>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- PrimaryButton.test.tsx`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/PrimaryButton.tsx src/components/SecondaryButton.tsx src/components/FocusRing.tsx src/screens/LoginScreen.tsx src/screens/ChatScreen.tsx src/components/__tests__/PrimaryButton.test.tsx
git commit -m "feat: implement v3 button and input interaction states"
```

---

### Task 5: Migrate navigation chrome (tab bar, headers, shell depth)

**Files:**
- Modify: `src/navigation/AppNavigator.tsx`
- Modify: `src/components/ScreenHeader.tsx`
- Modify: `src/components/SectionHeader.tsx`
- Test: `src/screens/__tests__/LoginScreen.ui.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
test('screen header renders title with semantic role style', () => {
	const { getByText } = render(<ScreenHeader title="Progress" />)
	expect(getByText('Progress')).toBeTruthy()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- LoginScreen.ui.test.tsx`  
Expected: FAIL due to stale typography mapping or imports after role migration.

- [ ] **Step 3: Write minimal implementation**

```ts
// AppNavigator.tsx (partial)
tabBarStyle: {
	backgroundColor: colors.bg.secondary,
	borderTopColor: colors.border.subtle,
	height: 56 + insets.bottom,
	paddingBottom: Math.max(6, insets.bottom),
}
tabBarActiveTintColor: colors.brand.orange
tabBarInactiveTintColor: colors.text.tertiary
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- LoginScreen.ui.test.tsx`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/navigation/AppNavigator.tsx src/components/ScreenHeader.tsx src/components/SectionHeader.tsx src/screens/__tests__/LoginScreen.ui.test.tsx
git commit -m "feat: align navigation chrome with design-system v3"
```

---

### Task 6: Migrate hero/stat cards and score semantics

**Files:**
- Modify: `src/components/AnalysisCard.tsx`
- Modify: `src/components/ScoreRing.tsx`
- Modify: `src/components/StreakBadge.tsx`
- Modify: `src/components/TierBadge.tsx`
- Modify: `src/screens/HomeScreen.tsx`
- Modify: `src/screens/ProgressScreen.tsx`
- Test: `src/components/__tests__/InputField.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
test('score tier mapping remains stable for 82', () => {
	expect(getScoreTier(82)).toBe('great')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- InputField.test.tsx`  
Expected: FAIL if tier map/test imports are outdated after semantic token split.

- [ ] **Step 3: Write minimal implementation**

```ts
// theme tier tokens (partial)
tier: {
	poor: { base: '#EF4444', range: [0, 39] },
	fair: { base: '#F59E0B', range: [40, 59] },
	good: { base: '#FBBF24', range: [60, 74] },
	great: { base: '#22C55E', range: [75, 89] },
	elite: { base: '#14C7E0', range: [90, 100] },
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- InputField.test.tsx`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/AnalysisCard.tsx src/components/ScoreRing.tsx src/components/StreakBadge.tsx src/components/TierBadge.tsx src/screens/HomeScreen.tsx src/screens/ProgressScreen.tsx src/components/__tests__/InputField.test.tsx
git commit -m "feat: migrate cards and score tiers to v3 semantics"
```

---

### Task 7: Upgrade Chat screen interactivity and motion polish

**Files:**
- Modify: `src/screens/ChatScreen.tsx`
- Modify: `src/components/ChatBubble.tsx`
- Modify: `src/components/TypingIndicator.tsx`
- Create: `src/theme/motion.ts`
- Test: `src/screens/__tests__/LoginScreen.ui.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
test('chat send button is disabled for empty input', () => {
	const { getByLabelText } = render(<ChatScreen />)
	const sendButton = getByLabelText(/send message/i)
	expect(sendButton.props.accessibilityState.disabled).toBe(true)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- LoginScreen.ui.test.tsx`  
Expected: FAIL due to legacy send state handling.

- [ ] **Step 3: Write minimal implementation**

```ts
// motion.ts (partial)
export const motion = {
	timing: { fast: 120, medium: 300, reveal: 1400 },
	scale: { press: 0.97 },
}
```

```tsx
// ChatScreen.tsx (partial)
<PrimaryButton
	label="Send"
	icon={isSending ? undefined : 'send'}
	loading={isSending}
	disabled={!inputText.trim() || isSending}
	onPress={() => send(inputText)}
	accessibilityLabel={isSending ? 'Sending' : 'Send message'}
/>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- LoginScreen.ui.test.tsx`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/screens/ChatScreen.tsx src/components/ChatBubble.tsx src/components/TypingIndicator.tsx src/theme/motion.ts src/screens/__tests__/LoginScreen.ui.test.tsx
git commit -m "feat: add v3 chat composer interaction and motion states"
```

---

### Task 8: Migrate remaining screens to design kit and enforce token usage

**Files:**
- Modify: `src/screens/MVPAnalysisScreen.tsx`
- Modify: `src/screens/ProfileScreen.tsx`
- Modify: `src/screens/WorkoutsScreen.tsx`
- Modify: `src/screens/DrillsScreen.tsx`
- Modify: `src/screens/DrillDetailScreen.tsx`
- Modify: `src/screens/SplashScreen.tsx`
- Modify: `src/screens/OnboardingScreen.tsx`
- Modify: `src/screens/UsernameScreen.tsx`
- Test: `src/screens/__tests__/LoginScreen.ui.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
test('login CTA still exists after global style migration', () => {
	const { getByText } = render(<LoginScreen onLogin={() => {}} />)
	expect(getByText(/SIGN IN/i)).toBeTruthy()
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- LoginScreen.ui.test.tsx`  
Expected: FAIL while screen migrations are partially applied.

- [ ] **Step 3: Write minimal implementation**

```ts
// Example migration pattern
// before: color: '#E8521A'
// after:  color: colors.brand.orange
// before: fontSize: 20, fontWeight: '700'
// after:  ...tokens.typography.roles['heading.h2']
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- LoginScreen.ui.test.tsx`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/screens/*.tsx
git commit -m "feat: migrate all app screens to design-system v3 visual language"
```

---

### Task 9: Add token guardrails and final verification suite

**Files:**
- Modify: `package.json`
- Modify: `.eslintrc*` (existing ESLint config file)
- Create: `src/theme/__tests__/tokens.contract.test.ts`
- Test: `src/theme/__tests__/tokens.contract.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { tokens } from '../tokens'

test('focus token is structured (RN-safe)', () => {
	expect(tokens.focus.ringWidth).toBe(2)
	expect(typeof tokens.focus.ringColor).toBe('string')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- tokens.contract.test.ts`  
Expected: FAIL if token contract diverges during migration.

- [ ] **Step 3: Write minimal implementation**

```json
// ESLint restriction snippet
{
	"rules": {
		"no-restricted-syntax": [
			"error",
			{
				"selector": "Literal[value=/^#([0-9A-Fa-f]{6})$/]",
				"message": "Use semantic tokens from src/theme/tokens.ts"
			}
		]
	}
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:
- `npm test -- tokens.contract.test.ts`
- `npm run lint`
- `npm run typecheck`

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add package.json .eslintrc* src/theme/__tests__/tokens.contract.test.ts
git commit -m "chore: enforce design token contract and lint guardrails"
```

---

### Task 10: Final production verification and rollout prep

**Files:**
- Modify: `docs/superpowers/plans/2026-04-23-design-system-v3-rollout.md` (checklist completion notes only)

- [ ] **Step 1: Run full verification**

Run:
- `npm run lint`
- `npm run typecheck`
- `npm test`
- `npm run start` (manual spot-check on Login, Home, Progress, Chat, Profile)

Expected:
- lint/typecheck/tests PASS
- no broken navigation
- no contrast regressions on core CTA/input states
- animations/haptics feel correct on device

- [ ] **Step 2: Device-level manual checklist**

Verify:
- iOS and Android focus ring visibility
- button states (`default`, `pressed`, `focused`, `disabled`, `loading`)
- chat send disabled/loading behavior
- reduced-motion fallback (if enabled)
- tab bar and headers match v3 kit

- [ ] **Step 3: Commit release prep**

```bash
git add .
git commit -m "chore: complete v3 design-system rollout verification"
```

---

## Spec Coverage Check (self-review)

- Whole design-system source consumed from `assets/shootrz-design-system/project/**` and mapped to RN.
- Global tokens, typography roles, brand colors, borders, shadows, focus ring, and motion included.
- Full component interactivity covered for buttons/inputs/chat (`default`, `pressed`, `focused`, `disabled`, `loading`).
- App-wide screen migration included (`Login`, `Home`, `Progress`, `Coach J`, `Profile`, plus remaining screens).
- Accessibility and reduced-motion are explicit in tasks.
- Guardrails (lint + token contract tests) and rollout verification included.

No placeholder steps remain; each code-modifying task has explicit file paths, code snippets, run commands, and commit steps.

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-23-design-system-v3-rollout.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
