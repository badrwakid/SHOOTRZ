import React, { useState } from 'react'
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius, shadows } from '../constants/theme'
import { PrimaryButton } from '../components/PrimaryButton'
import { useAuth } from '../context/AuthContext'
import { hapticFeedback } from '../utils/hapticFeedback'

interface OnboardingScreenProps {
	onComplete: () => void
}

export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onComplete }) => {
	const { updateProfile } = useAuth()
	const [currentStep, setCurrentStep] = useState(0)
	const [selectedSkillLevel, setSelectedSkillLevel] = useState<
		'beginner' | 'intermediate' | 'advanced'
	>('beginner')
	const [selectedPosition, setSelectedPosition] = useState('Guard')
	const [selectedGoals, setSelectedGoals] = useState<string[]>([])

	const steps = [
		{ title: 'Welcome to SHOOTRZ', subtitle: 'Your AI-powered basketball training assistant', icon: 'basketball' },
		{ title: 'Your Skill Level', subtitle: 'This helps us personalize your training', icon: 'stats-chart' },
		{ title: 'Your Position', subtitle: 'What position do you play?', icon: 'people' },
		{ title: 'Your Goals', subtitle: 'What do you want to improve?', icon: 'trophy' },
	]

	const positions = ['Guard', 'Forward', 'Center', 'All-Around']
	const goalOptions = [
		'Improve shooting accuracy',
		'Perfect my form',
		'Increase consistency',
		'Better balance',
		'Faster release',
		'Stronger follow-through',
	]

	const handleNext = async () => {
		hapticFeedback.medium()
		if (currentStep < steps.length - 1) {
			setCurrentStep(currentStep + 1)
		} else {
			await completeOnboarding()
		}
	}

	const completeOnboarding = async () => {
		try {
			await updateProfile({ skillLevel: selectedSkillLevel, position: selectedPosition })
			hapticFeedback.success()
			onComplete()
		} catch {
			onComplete()
		}
	}

	const toggleGoal = (goal: string) => {
		hapticFeedback.selection()
		setSelectedGoals(prev =>
			prev.includes(goal) ? prev.filter(g => g !== goal) : [...prev, goal],
		)
	}

	const step = steps[currentStep]

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
			<View style={styles.dots}>
				{steps.map((_, i) => (
					<View
						key={i}
						style={[
							styles.dot,
							i <= currentStep && styles.dotActive,
							i === currentStep && styles.dotCurrent,
						]}
					/>
				))}
			</View>

			<ScrollView style={styles.content} contentContainerStyle={styles.contentInner}>
				<Ionicons name={step.icon as any} size={56} color={colors.brand.orange} />
				<Text style={styles.title}>{step.title}</Text>
				<Text style={styles.subtitle}>{step.subtitle}</Text>

				{currentStep === 0 ? (
					<Text style={styles.desc}>
						Perfect your shooting form with AI analysis and personalized coaching.
					</Text>
				) : null}

				{currentStep === 1 ? (
					<View style={styles.options}>
						{(['beginner', 'intermediate', 'advanced'] as const).map(level => {
							const active = selectedSkillLevel === level
							return (
								<TouchableOpacity
									key={level}
									style={[styles.optionCard, active && styles.optionCardActive]}
									onPress={() => { hapticFeedback.selection(); setSelectedSkillLevel(level) }}
									activeOpacity={0.85}
								>
									{active ? (
										<Ionicons name="checkmark-circle" size={20} color={colors.brand.orange} style={styles.checkIcon} />
									) : null}
									<Text style={[styles.optionTitle, active && styles.optionTitleActive]}>
										{level.charAt(0).toUpperCase() + level.slice(1)}
									</Text>
									<Text style={styles.optionDesc}>
										{level === 'beginner' ? 'Learning fundamentals' : level === 'intermediate' ? 'Improving consistency' : 'Perfecting technique'}
									</Text>
								</TouchableOpacity>
							)
						})}
					</View>
				) : null}

				{currentStep === 2 ? (
					<View style={styles.posGrid}>
						{positions.map(pos => {
							const active = selectedPosition === pos
							return (
								<TouchableOpacity
									key={pos}
									style={[styles.posCard, active && styles.posCardActive]}
									onPress={() => { hapticFeedback.selection(); setSelectedPosition(pos) }}
									activeOpacity={0.85}
								>
									{active ? <Ionicons name="checkmark-circle" size={18} color={colors.brand.orange} style={styles.checkIcon} /> : null}
									<Text style={[styles.posText, active && styles.posTextActive]}>{pos}</Text>
								</TouchableOpacity>
							)
						})}
					</View>
				) : null}

				{currentStep === 3 ? (
					<View style={styles.options}>
						{goalOptions.map(goal => {
							const active = selectedGoals.includes(goal)
							return (
								<TouchableOpacity
									key={goal}
									style={[styles.goalCard, active && styles.goalCardActive]}
									onPress={() => toggleGoal(goal)}
									activeOpacity={0.85}
								>
									<Ionicons
										name={active ? 'checkmark-circle' : 'ellipse-outline'}
										size={20}
										color={active ? colors.brand.orange : colors.text.tertiary}
									/>
									<Text style={[styles.goalText, active && styles.goalTextActive]}>{goal}</Text>
								</TouchableOpacity>
							)
						})}
					</View>
				) : null}
			</ScrollView>

			<View style={styles.nav}>
				{currentStep > 0 ? (
					<TouchableOpacity
						onPress={() => { hapticFeedback.light(); setCurrentStep(currentStep - 1) }}
						style={styles.backBtn}
					>
						<Ionicons name="chevron-back" size={20} color={colors.text.secondary} />
						<Text style={styles.backText}>Back</Text>
					</TouchableOpacity>
				) : (
					<TouchableOpacity onPress={onComplete} style={styles.backBtn}>
						<Text style={styles.skipText}>Skip</Text>
					</TouchableOpacity>
				)}
				<PrimaryButton
					label={currentStep === steps.length - 1 ? 'Get Started' : 'Continue'}
					onPress={handleNext}
					size="md"
				/>
			</View>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: colors.bg.primary,
	},
	dots: {
		flexDirection: 'row',
		justifyContent: 'center',
		paddingVertical: spacing[4],
		gap: spacing[2],
	},
	dot: {
		width: 8,
		height: 8,
		borderRadius: 4,
		backgroundColor: colors.bg.elevated,
	},
	dotActive: {
		backgroundColor: colors.brand.orange,
	},
	dotCurrent: {
		width: 24,
	},
	content: {
		flex: 1,
	},
	contentInner: {
		alignItems: 'center',
		paddingHorizontal: spacing.screenPadding,
		paddingTop: spacing[8],
	},
	title: {
		fontSize: typography.size['2xl'],
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
		textAlign: 'center',
		marginTop: spacing[5],
	},
	subtitle: {
		fontSize: typography.size.base,
		color: colors.text.secondary,
		textAlign: 'center',
		marginTop: spacing[2],
		marginBottom: spacing[6],
	},
	desc: {
		fontSize: typography.size.sm,
		color: colors.text.tertiary,
		textAlign: 'center',
		maxWidth: 280,
		lineHeight: typography.size.sm * typography.lineHeight.relaxed,
	},
	options: {
		width: '100%',
		gap: spacing[3],
	},
	optionCard: {
		backgroundColor: colors.bg.secondary,
		borderRadius: radius.card,
		borderWidth: 1,
		borderColor: colors.border.default,
		padding: spacing[4],
		alignItems: 'center',
	},
	optionCardActive: {
		backgroundColor: colors.brand.orangeDim,
		borderColor: colors.brand.orange,
	},
	checkIcon: {
		position: 'absolute',
		top: spacing[3],
		right: spacing[3],
	},
	optionTitle: {
		fontSize: typography.size.md,
		fontWeight: typography.weight.semibold,
		color: colors.text.primary,
		marginBottom: spacing[1],
	},
	optionTitleActive: {
		color: colors.brand.orangeLight,
	},
	optionDesc: {
		fontSize: typography.size.xs,
		color: colors.text.tertiary,
	},
	posGrid: {
		width: '100%',
		flexDirection: 'row',
		flexWrap: 'wrap',
		gap: spacing[3],
	},
	posCard: {
		width: '47%',
		backgroundColor: colors.bg.secondary,
		borderRadius: radius.card,
		borderWidth: 1,
		borderColor: colors.border.default,
		padding: spacing[4],
		alignItems: 'center',
	},
	posCardActive: {
		backgroundColor: colors.brand.orangeDim,
		borderColor: colors.brand.orange,
	},
	posText: {
		fontSize: typography.size.base,
		fontWeight: typography.weight.semibold,
		color: colors.text.primary,
	},
	posTextActive: {
		color: colors.brand.orangeLight,
	},
	goalCard: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[3],
		backgroundColor: colors.bg.secondary,
		borderRadius: radius.card,
		borderWidth: 1,
		borderColor: colors.border.default,
		padding: spacing[4],
	},
	goalCardActive: {
		backgroundColor: colors.brand.orangeDim,
		borderColor: colors.brand.orange,
	},
	goalText: {
		fontSize: typography.size.base,
		color: colors.text.primary,
		flex: 1,
	},
	goalTextActive: {
		color: colors.brand.orangeLight,
		fontWeight: typography.weight.semibold,
	},
	nav: {
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[4],
		borderTopWidth: 1,
		borderTopColor: colors.border.subtle,
		backgroundColor: colors.bg.secondary,
	},
	backBtn: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[1],
		paddingVertical: spacing[2],
		paddingHorizontal: spacing[3],
	},
	backText: {
		fontSize: typography.size.sm,
		color: colors.text.secondary,
	},
	skipText: {
		fontSize: typography.size.sm,
		color: colors.text.tertiary,
	},
})
