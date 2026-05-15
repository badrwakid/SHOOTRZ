import React, { useState } from 'react'
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius } from '../constants/theme'
import { PrimaryButton } from '../components/PrimaryButton'
import { useAuth } from '../context/AuthContext'
import { hapticFeedback } from '../utils/hapticFeedback'

interface OnboardingScreenProps {
	onComplete: () => void
}

export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onComplete }) => {
	const { updateProfile } = useAuth()
	const [currentStep, setCurrentStep] = useState(0)
	const [isSaving, setIsSaving] = useState(false)
	const [saveError, setSaveError] = useState<string | null>(null)
	const [selectedSkillLevel, setSelectedSkillLevel] = useState<
		'beginner' | 'intermediate' | 'advanced'
	>('beginner')
	const [selectedPosition, setSelectedPosition] = useState('Guard')
	const [selectedPrimaryGoal, setSelectedPrimaryGoal] = useState('Improve shooting accuracy')
	const [selectedTrainingFrequency, setSelectedTrainingFrequency] = useState('3-4 times per week')
	const [preferredDrillDuration, setPreferredDrillDuration] = useState('30')
	const [selectedDominantHand, setSelectedDominantHand] = useState('right')
	const [yearsPlaying, setYearsPlaying] = useState('1')
	const [selectedCoachingStyle, setSelectedCoachingStyle] = useState('balanced')
	const [age, setAge] = useState('')
	const [heightCm, setHeightCm] = useState('')
	const [weightKg, setWeightKg] = useState('')

	const steps = [
		{ title: 'Welcome to SHOOTRZ', subtitle: 'Your AI-powered basketball training assistant', icon: 'basketball' },
		{ title: 'Your Skill Level', subtitle: 'This helps us personalize your training', icon: 'stats-chart' },
		{ title: 'Your Position', subtitle: 'What position do you play?', icon: 'people' },
		{ title: 'Primary Goal', subtitle: 'What should we focus on first?', icon: 'trophy' },
		{ title: 'Training Frequency', subtitle: 'How often do you train?', icon: 'calendar' },
		{ title: 'Drill Duration', subtitle: 'Preferred drill session duration', icon: 'time' },
		{ title: 'Dominant Hand', subtitle: 'Which hand do you shoot with?', icon: 'hand-left' },
		{ title: 'Experience', subtitle: 'How many years have you played?', icon: 'school' },
		{ title: 'Coaching Style', subtitle: 'How should feedback be delivered?', icon: 'chatbubble-ellipses' },
		{ title: 'Body Metrics', subtitle: 'Optional values improve coaching precision', icon: 'body' },
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
	const trainingFrequencyOptions = ['1-2 times per week', '3-4 times per week', '5+ times per week']
	const dominantHandOptions = [
		{ value: 'right', label: 'Right' },
		{ value: 'left', label: 'Left' },
		{ value: 'ambidextrous', label: 'Ambidextrous' },
	]
	const coachingStyleOptions = [
		{ value: 'encouraging', label: 'Encouraging' },
		{ value: 'balanced', label: 'Balanced' },
		{ value: 'direct', label: 'Direct' },
	]

	const parsePositiveInt = (raw: string): number | undefined => {
		if (!raw.trim()) {
			return undefined
		}
		const parsed = Number.parseInt(raw, 10)
		return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined
	}

	const parsePositiveNumber = (raw: string): number | undefined => {
		if (!raw.trim()) {
			return undefined
		}
		const parsed = Number.parseFloat(raw)
		return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined
	}

	const validateStep = (): string | null => {
		if (currentStep === 5 && preferredDrillDuration.trim() && !parsePositiveInt(preferredDrillDuration)) {
			return 'Please enter a valid drill duration in minutes.'
		}
		if (currentStep === 7 && yearsPlaying.trim() && !parsePositiveInt(yearsPlaying)) {
			return 'Please enter valid years playing.'
		}
		if (currentStep === 9) {
			if (age.trim() && !parsePositiveInt(age)) return 'Please enter a valid age.'
			if (heightCm.trim() && !parsePositiveNumber(heightCm)) return 'Please enter a valid height in cm.'
			if (weightKg.trim() && !parsePositiveNumber(weightKg)) return 'Please enter a valid weight in kg.'
		}
		return null
	}

	const getStepPayload = (): Record<string, unknown> => {
		switch (currentStep) {
			case 1:
				return { skillLevel: selectedSkillLevel }
			case 2:
				return { position: selectedPosition }
			case 3:
				return { primaryGoal: selectedPrimaryGoal }
			case 4:
				return { trainingFrequency: selectedTrainingFrequency }
			case 5: {
				const duration = parsePositiveInt(preferredDrillDuration)
				return duration ? { preferredDrillDuration: duration } : {}
			}
			case 6:
				return { dominantHand: selectedDominantHand }
			case 7: {
				const years = parsePositiveInt(yearsPlaying)
				return years ? { yearsPlaying: years } : {}
			}
			case 8:
				return { coachingStyle: selectedCoachingStyle }
			case 9: {
				const payload: Record<string, unknown> = {}
				const parsedAge = parsePositiveInt(age)
				const parsedHeight = parsePositiveNumber(heightCm)
				const parsedWeight = parsePositiveNumber(weightKg)
				if (parsedAge !== undefined) payload.age = parsedAge
				if (parsedHeight !== undefined) payload.heightCm = parsedHeight
				if (parsedWeight !== undefined) payload.weightKg = parsedWeight
				return payload
			}
			default:
				return {}
		}
	}

	const handleNext = async () => {
		hapticFeedback.medium()
		const validationError = validateStep()
		if (validationError) {
			setSaveError(validationError)
			return
		}
		const payload = getStepPayload()
		if (Object.keys(payload).length > 0) {
			try {
				setIsSaving(true)
				setSaveError(null)
				await updateProfile(payload as any)
			} catch {
				setSaveError('Failed to save this step. Please try again.')
				setIsSaving(false)
				return
			}
		}
		if (currentStep < steps.length - 1) {
			setCurrentStep(currentStep + 1)
		} else {
			await completeOnboarding()
		}
		setIsSaving(false)
	}

	const completeOnboarding = async () => {
		try {
			hapticFeedback.success()
			onComplete()
		} catch {
			onComplete()
		}
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
							const active = selectedPrimaryGoal === goal
							return (
								<TouchableOpacity
									key={goal}
									style={[styles.goalCard, active && styles.goalCardActive]}
									onPress={() => { hapticFeedback.selection(); setSelectedPrimaryGoal(goal) }}
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

				{currentStep === 4 ? (
					<View style={styles.options}>
						{trainingFrequencyOptions.map(option => {
							const active = selectedTrainingFrequency === option
							return (
								<TouchableOpacity
									key={option}
									style={[styles.goalCard, active && styles.goalCardActive]}
									onPress={() => { hapticFeedback.selection(); setSelectedTrainingFrequency(option) }}
									activeOpacity={0.85}
								>
									<Ionicons
										name={active ? 'checkmark-circle' : 'ellipse-outline'}
										size={20}
										color={active ? colors.brand.orange : colors.text.tertiary}
									/>
									<Text style={[styles.goalText, active && styles.goalTextActive]}>{option}</Text>
								</TouchableOpacity>
							)
						})}
					</View>
				) : null}

				{currentStep === 5 ? (
					<View style={styles.inputGroup}>
						<Text style={styles.inputLabel}>Minutes per drill session</Text>
						<TextInput
							style={styles.input}
							value={preferredDrillDuration}
							onChangeText={setPreferredDrillDuration}
							keyboardType="number-pad"
							placeholder="e.g. 30"
							placeholderTextColor={colors.text.tertiary}
						/>
					</View>
				) : null}

				{currentStep === 6 ? (
					<View style={styles.options}>
						{dominantHandOptions.map(option => {
							const active = selectedDominantHand === option.value
							return (
								<TouchableOpacity
									key={option.value}
									style={[styles.goalCard, active && styles.goalCardActive]}
									onPress={() => { hapticFeedback.selection(); setSelectedDominantHand(option.value) }}
									activeOpacity={0.85}
								>
									<Ionicons
										name={active ? 'checkmark-circle' : 'ellipse-outline'}
										size={20}
										color={active ? colors.brand.orange : colors.text.tertiary}
									/>
									<Text style={[styles.goalText, active && styles.goalTextActive]}>{option.label}</Text>
								</TouchableOpacity>
							)
						})}
					</View>
				) : null}

				{currentStep === 7 ? (
					<View style={styles.inputGroup}>
						<Text style={styles.inputLabel}>Years playing basketball</Text>
						<TextInput
							style={styles.input}
							value={yearsPlaying}
							onChangeText={setYearsPlaying}
							keyboardType="number-pad"
							placeholder="e.g. 3"
							placeholderTextColor={colors.text.tertiary}
						/>
					</View>
				) : null}

				{currentStep === 8 ? (
					<View style={styles.options}>
						{coachingStyleOptions.map(option => {
							const active = selectedCoachingStyle === option.value
							return (
								<TouchableOpacity
									key={option.value}
									style={[styles.goalCard, active && styles.goalCardActive]}
									onPress={() => { hapticFeedback.selection(); setSelectedCoachingStyle(option.value) }}
									activeOpacity={0.85}
								>
									<Ionicons
										name={active ? 'checkmark-circle' : 'ellipse-outline'}
										size={20}
										color={active ? colors.brand.orange : colors.text.tertiary}
									/>
									<Text style={[styles.goalText, active && styles.goalTextActive]}>{option.label}</Text>
								</TouchableOpacity>
							)
						})}
					</View>
				) : null}

				{currentStep === 9 ? (
					<View style={styles.inputGroup}>
						<Text style={styles.inputLabel}>Age (optional)</Text>
						<TextInput
							style={styles.input}
							value={age}
							onChangeText={setAge}
							keyboardType="number-pad"
							placeholder="e.g. 18"
							placeholderTextColor={colors.text.tertiary}
						/>
						<Text style={styles.inputLabel}>Height in cm (optional)</Text>
						<TextInput
							style={styles.input}
							value={heightCm}
							onChangeText={setHeightCm}
							keyboardType="decimal-pad"
							placeholder="e.g. 182"
							placeholderTextColor={colors.text.tertiary}
						/>
						<Text style={styles.inputLabel}>Weight in kg (optional)</Text>
						<TextInput
							style={styles.input}
							value={weightKg}
							onChangeText={setWeightKg}
							keyboardType="decimal-pad"
							placeholder="e.g. 78"
							placeholderTextColor={colors.text.tertiary}
						/>
					</View>
				) : null}

				{saveError ? <Text style={styles.errorText}>{saveError}</Text> : null}
			</ScrollView>

			<View style={styles.nav}>
				{currentStep > 0 ? (
					<TouchableOpacity
						onPress={() => { hapticFeedback.light(); setCurrentStep(currentStep - 1) }}
						style={styles.backBtn}
						activeOpacity={0.75}
					>
						<Ionicons name="chevron-back" size={20} color={colors.text.secondary} />
						<Text style={styles.backText}>Back</Text>
					</TouchableOpacity>
				) : (
					<TouchableOpacity onPress={onComplete} style={styles.backBtn} activeOpacity={0.75}>
						<Text style={styles.skipText}>Skip</Text>
					</TouchableOpacity>
				)}
				<PrimaryButton
					label={currentStep === steps.length - 1 ? 'Get Started' : 'Continue'}
					onPress={handleNext}
					size="md"
					loading={isSaving}
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
		...typography.roles.headingLg,
		color: colors.text.primary,
		textAlign: 'center',
		marginTop: spacing[5],
	},
	subtitle: {
		...typography.roles.body,
		color: colors.text.secondary,
		textAlign: 'center',
		marginTop: spacing[2],
		marginBottom: spacing[6],
	},
	desc: {
		...typography.roles.caption,
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
	inputGroup: {
		width: '100%',
		gap: spacing[2],
	},
	inputLabel: {
		...typography.roles.caption,
		color: colors.text.secondary,
		marginTop: spacing[2],
	},
	input: {
		backgroundColor: colors.bg.secondary,
		borderWidth: 1,
		borderColor: colors.border.default,
		borderRadius: radius.card,
		paddingHorizontal: spacing[3],
		paddingVertical: spacing[3],
		color: colors.text.primary,
	},
	errorText: {
		...typography.roles.caption,
		color: colors.error,
		marginTop: spacing[3],
		textAlign: 'center',
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
		...typography.roles.caption,
		fontSize: typography.size.sm,
		color: colors.text.secondary,
	},
	skipText: {
		...typography.roles.caption,
		fontSize: typography.size.sm,
		color: colors.text.tertiary,
	},
})
