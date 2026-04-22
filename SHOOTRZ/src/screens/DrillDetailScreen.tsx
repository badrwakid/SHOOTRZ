import React, { useState, useEffect } from 'react'
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	Alert,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius, glass, shadows } from '../constants/theme'
import { PrimaryButton } from '../components/PrimaryButton'
import { IconButton } from '../components/IconButton'
import { storageService } from '../services/storage.service'
import { getDrillCategoryIcon } from '../utils/iconMapper'
import { hapticFeedback } from '../utils/hapticFeedback'
import type { Drill } from '../constants/drills'

interface DrillDetailScreenProps {
	drill: Drill
	onClose: () => void
}

export const DrillDetailScreen: React.FC<DrillDetailScreenProps> = ({ drill, onClose }) => {
	const [completionCount, setCompletionCount] = useState(0)
	const [isCompleting, setIsCompleting] = useState(false)

	useEffect(() => {
		storageService.getDrillCompletionCount(drill.id).then(setCompletionCount).catch(() => {})
	}, [])

	const getDifficultyColor = () => {
		switch (drill.difficulty) {
			case 'beginner': return colors.success
			case 'advanced': return colors.error
			default: return colors.warning
		}
	}

	const handleMarkCompleted = async () => {
		setIsCompleting(true)
		try {
			await storageService.markDrillCompleted(drill.id)
			const newCount = completionCount + 1
			setCompletionCount(newCount)
			hapticFeedback.success()
			Alert.alert(
				'Drill Completed!',
				`You've completed this drill ${newCount} time${newCount !== 1 ? 's' : ''}. Keep grinding!`,
				[{ text: 'Done', onPress: onClose }],
			)
		} catch {
			Alert.alert('Error', 'Failed to save completion.')
		} finally {
			setIsCompleting(false)
		}
	}

	const diffColor = getDifficultyColor()
	const catIcon = getDrillCategoryIcon(drill.category)

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
			{/* Header */}
			<View style={[styles.headerBg, { backgroundColor: diffColor + '15' }]}>
				<View style={styles.headerTop}>
					<IconButton icon="chevron-back" onPress={onClose} size={40} color={colors.text.primary} />
					<View style={styles.headerBadges}>
						<View style={[styles.badge, { backgroundColor: diffColor + '30' }]}>
							<Text style={[styles.badgeText, { color: diffColor }]}>
								{drill.difficulty.toUpperCase()}
							</Text>
						</View>
						{drill.duration ? (
							<View style={styles.timeBadge}>
								<Ionicons name="time-outline" size={12} color={colors.text.primary} />
								<Text style={styles.timeText}>{drill.duration}</Text>
							</View>
						) : null}
					</View>
				</View>
				<View style={styles.headerCenter}>
					<Ionicons name={catIcon as any} size={48} color={diffColor} />
				</View>
			</View>

			<ScrollView showsVerticalScrollIndicator={false} style={styles.scrollContent}>
				<Text style={styles.title}>{drill.name}</Text>
				<View style={styles.tagRow}>
					<View style={styles.categoryPill}>
						<Text style={styles.categoryText}>{drill.category}</Text>
					</View>
					{completionCount > 0 ? (
						<Text style={styles.completions}>
							Completed {completionCount} time{completionCount !== 1 ? 's' : ''}
						</Text>
					) : null}
				</View>

				{drill.description ? (
					<View style={styles.section}>
						<Text style={styles.sectionTitle}>Description</Text>
						<Text style={styles.bodyText}>{drill.description}</Text>
					</View>
				) : null}

				{drill.instructions && drill.instructions.length > 0 ? (
					<View style={styles.section}>
						<Text style={styles.sectionTitle}>How to Do It</Text>
						{drill.instructions.map((step, i) => (
							<View key={i} style={styles.stepRow}>
								<View style={styles.stepNum}>
									<Text style={styles.stepNumText}>{i + 1}</Text>
								</View>
								<Text style={styles.stepText}>{step}</Text>
							</View>
						))}
					</View>
				) : null}

				{drill.tips && drill.tips.length > 0 ? (
					<View style={styles.section}>
						<Text style={styles.sectionTitle}>Tips</Text>
						{drill.tips.map((tip, i) => (
							<View key={i} style={styles.tipRow}>
								<Ionicons name="bulb" size={16} color={colors.brand.orange} />
								<Text style={styles.tipText}>{tip}</Text>
							</View>
						))}
					</View>
				) : null}

				<View style={{ height: 120 }} />
			</ScrollView>

			{/* Sticky CTA */}
			<View style={styles.stickyBtn}>
				<PrimaryButton
					label={isCompleting ? 'Saving...' : 'Complete Drill'}
					icon="checkmark-circle"
					onPress={handleMarkCompleted}
					loading={isCompleting}
					fullWidth
					size="lg"
				/>
			</View>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: { flex: 1, backgroundColor: colors.bg.primary },
	headerBg: {
		height: 200,
		justifyContent: 'space-between',
	},
	headerTop: {
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		paddingHorizontal: spacing[3],
		paddingTop: spacing[2],
	},
	headerBadges: { flexDirection: 'row', gap: spacing[2] },
	badge: {
		paddingHorizontal: spacing[2],
		paddingVertical: 2,
		borderRadius: radius.pill,
	},
	badgeText: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.bold,
		letterSpacing: typography.tracking.wide,
	},
	timeBadge: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: 3,
		backgroundColor: 'rgba(0,0,0,0.4)',
		borderRadius: radius.pill,
		paddingHorizontal: spacing[2],
		paddingVertical: 2,
	},
	timeText: { fontSize: typography.size.xs, color: colors.text.primary },
	headerCenter: {
		alignItems: 'center',
		paddingBottom: spacing[4],
	},
	scrollContent: {
		paddingHorizontal: spacing.screenPadding,
		paddingTop: spacing[5],
	},
	title: {
		fontSize: typography.size['2xl'],
		fontWeight: typography.weight.heavy,
		color: colors.text.primary,
	},
	tagRow: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[3],
		marginTop: spacing[2],
	},
	categoryPill: {
		backgroundColor: colors.brand.orangeDim,
		borderRadius: radius.pill,
		paddingHorizontal: spacing[3],
		paddingVertical: spacing[1],
	},
	categoryText: {
		fontSize: typography.size.xs,
		color: colors.brand.orangeLight,
		fontWeight: typography.weight.medium,
	},
	completions: {
		fontSize: typography.size.xs,
		color: colors.text.tertiary,
	},
	section: { marginTop: spacing.sectionGap },
	sectionTitle: {
		fontSize: typography.size.md,
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
		marginBottom: spacing[3],
	},
	bodyText: {
		fontSize: typography.size.base,
		color: colors.text.secondary,
		lineHeight: typography.size.base * typography.lineHeight.normal,
	},
	stepRow: {
		flexDirection: 'row',
		alignItems: 'flex-start',
		gap: spacing[3],
		marginBottom: spacing[3],
	},
	stepNum: {
		width: 28,
		height: 28,
		borderRadius: 14,
		backgroundColor: colors.brand.orangeDim,
		alignItems: 'center',
		justifyContent: 'center',
	},
	stepNumText: {
		fontSize: typography.size.sm,
		fontWeight: typography.weight.bold,
		color: colors.brand.orange,
	},
	stepText: {
		flex: 1,
		fontSize: typography.size.base,
		color: colors.text.primary,
		lineHeight: typography.size.base * typography.lineHeight.normal,
	},
	tipRow: {
		flexDirection: 'row',
		alignItems: 'flex-start',
		gap: spacing[2],
		marginBottom: spacing[2],
		backgroundColor: colors.bg.secondary,
		borderRadius: radius.md,
		padding: spacing[3],
	},
	tipText: {
		flex: 1,
		fontSize: typography.size.sm,
		color: colors.text.primary,
		lineHeight: typography.size.sm * typography.lineHeight.normal,
	},
	stickyBtn: {
		position: 'absolute',
		bottom: 0,
		left: 0,
		right: 0,
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[4],
		backgroundColor: colors.bg.primary,
		borderTopWidth: 1,
		borderTopColor: colors.border.subtle,
	},
})
