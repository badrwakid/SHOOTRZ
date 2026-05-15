import React, { useEffect, useRef } from 'react'
import { View, Text, StyleSheet, Animated } from 'react-native'
import Svg, { Circle } from 'react-native-svg'
import { colors, typography, getScoreTier } from '../constants/theme'
import { SCORE_TIER_LABELS, SCORE_TIER_RING_STROKE } from '../theme/scoreTier'
import { hapticFeedback } from '../utils/hapticFeedback'

type RingSize = 'sm' | 'md' | 'lg' | 'hero'

interface ScoreRingProps {
	score: number
	size?: RingSize
	label?: string
	animated?: boolean
	showTier?: boolean
}

const DIMENSIONS: Record<RingSize, { diameter: number; stroke: number; fontSize: number }> = {
	sm: { diameter: 48, stroke: 8, fontSize: typography.size.sm },
	md: { diameter: 80, stroke: 10, fontSize: typography.size.xl },
	lg: { diameter: 120, stroke: 14, fontSize: typography.size['2xl'] },
	hero: { diameter: 200, stroke: 18, fontSize: typography.size['4xl'] },
}

const AnimatedCircle = Animated.createAnimatedComponent(Circle)

export function ScoreRing({
	score,
	size = 'md',
	label,
	animated = true,
	showTier = true,
}: ScoreRingProps) {
	const { diameter, stroke, fontSize } = DIMENSIONS[size]
	const r = (diameter - stroke) / 2
	const circumference = 2 * Math.PI * r
	const tier = getScoreTier(score)
	const ringColor = SCORE_TIER_RING_STROKE[tier]

	const animValue = useRef(new Animated.Value(0)).current
	const countValue = useRef(new Animated.Value(0)).current
	const [displayScore, setDisplayScore] = React.useState(animated ? 0 : score)

	useEffect(() => {
		if (!animated) {
			setDisplayScore(score)
			return
		}
		animValue.setValue(0)
		countValue.setValue(0)

		const listener = countValue.addListener(({ value }) => {
			setDisplayScore(Math.round(value))
		})

		Animated.parallel([
			Animated.timing(animValue, {
				toValue: score / 100,
				duration: 800,
				useNativeDriver: false,
			}),
			Animated.timing(countValue, {
				toValue: score,
				duration: 800,
				useNativeDriver: false,
			}),
		]).start(() => {
			if (score >= 75) hapticFeedback.success()
			else hapticFeedback.heavy()
		})

		return () => countValue.removeListener(listener)
	}, [score, animated])

	const strokeDashoffset = animated
		? animValue.interpolate({
				inputRange: [0, 1],
				outputRange: [circumference, 0],
			})
		: circumference * (1 - score / 100)

	return (
		<View style={[styles.container, { width: diameter, height: diameter }]}>
			<Svg width={diameter} height={diameter}>
				<Circle
					cx={diameter / 2}
					cy={diameter / 2}
					r={r}
					stroke={colors.bg.elevated}
					strokeWidth={stroke}
					fill="none"
				/>
				<AnimatedCircle
					cx={diameter / 2}
					cy={diameter / 2}
					r={r}
					stroke={ringColor}
					strokeWidth={stroke}
					fill="none"
					strokeLinecap="round"
					strokeDasharray={circumference}
					strokeDashoffset={strokeDashoffset}
					rotation={-90}
					origin={`${diameter / 2}, ${diameter / 2}`}
				/>
			</Svg>
			<View style={styles.inner}>
				<Text
					style={[
						styles.score,
						{ fontSize, color: colors.text.primary },
					]}
				>
					{displayScore}
				</Text>
				{showTier && size !== 'sm' ? (
					<Text style={[styles.tier, { color: ringColor }]}>
						{SCORE_TIER_LABELS[tier]}
					</Text>
				) : null}
				{label ? <Text style={styles.label}>{label}</Text> : null}
			</View>
		</View>
	)
}

const styles = StyleSheet.create({
	container: {
		alignItems: 'center',
		justifyContent: 'center',
	},
	inner: {
		...StyleSheet.absoluteFillObject,
		alignItems: 'center',
		justifyContent: 'center',
	},
	score: {
		...typography.roles.display,
	},
	tier: {
		...typography.roles.caption,
		fontWeight: typography.weight.bold,
		letterSpacing: typography.tracking.wider,
		textTransform: 'uppercase',
		marginTop: 2,
	},
	label: {
		...typography.roles.caption,
		color: colors.text.secondary,
		marginTop: 2,
	},
})
