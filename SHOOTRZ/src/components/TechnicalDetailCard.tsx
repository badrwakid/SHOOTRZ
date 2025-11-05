import React, { useState } from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { LinearGradient } from 'expo-linear-gradient'
import { SHOOTRZ_THEME } from '../constants/theme'
import { ProgressRing } from './ProgressRing'

interface TechnicalDetailCardProps {
	title: string
	icon?: keyof typeof Ionicons.glyphMap
	color?: string
	score?: number // 0-100 score
	details?: Array<{ label: string; value: string | number; unit?: string }>
	visualization?: React.ReactNode
	description?: string
}

export const TechnicalDetailCard: React.FC<TechnicalDetailCardProps> = ({
	title,
	icon = 'analytics',
	color = SHOOTRZ_THEME.colors.primary,
	score,
	details = [],
	visualization,
	description,
}) => {
	const [isExpanded, setIsExpanded] = useState(false)

	return (
		<LinearGradient
			colors={[SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated]}
			start={{ x: 0, y: 0 }}
			end={{ x: 1, y: 1 }}
			style={styles.container}
		>
			{/* Border accent */}
			<View style={[styles.borderAccent, { backgroundColor: color }]} />

			{/* Header */}
			<TouchableOpacity
				style={styles.header}
				onPress={() => setIsExpanded(!isExpanded)}
				activeOpacity={0.7}
			>
				<View style={styles.headerContent}>
					<Ionicons name={icon} size={24} color={color} />
					<View style={styles.headerText}>
						<Text style={styles.title}>{title}</Text>
						{description && (
							<Text style={styles.description}>{description}</Text>
						)}
					</View>
				</View>
				{score !== undefined && (
					<View style={styles.scoreContainer}>
						<ProgressRing
							progress={score}
							size={50}
							strokeWidth={4}
							color={color}
							showPercentage={false}
						/>
					</View>
				)}
				<Ionicons
					name={isExpanded ? 'chevron-up' : 'chevron-down'}
					size={20}
					color={SHOOTRZ_THEME.colors.textSecondary}
				/>
			</TouchableOpacity>

			{/* Expanded Content */}
			{isExpanded && (
				<View style={styles.content}>
					{visualization && (
						<View style={styles.visualizationContainer}>
							{visualization}
						</View>
					)}

					{details.length > 0 && (
						<View style={styles.detailsContainer}>
							{details.map((detail, index) => (
								<View key={index} style={styles.detailRow}>
									<Text style={styles.detailLabel}>{detail.label}</Text>
									<View style={styles.detailValueContainer}>
										<Text style={[styles.detailValue, { color }]}>
											{typeof detail.value === 'number'
												? detail.value.toFixed(2)
												: detail.value}
										</Text>
										{detail.unit && (
											<Text style={styles.detailUnit}>{detail.unit}</Text>
										)}
									</View>
								</View>
							))}
						</View>
					)}
				</View>
			)}
		</LinearGradient>
	)
}

const styles = StyleSheet.create({
	container: {
		borderRadius: SHOOTRZ_THEME.borderRadius.lg,
		padding: SHOOTRZ_THEME.spacing.lg,
		marginVertical: SHOOTRZ_THEME.spacing.sm,
		position: 'relative',
		overflow: 'hidden',
	},
	borderAccent: {
		position: 'absolute',
		left: 0,
		top: 0,
		bottom: 0,
		width: 4,
		borderTopLeftRadius: SHOOTRZ_THEME.borderRadius.lg,
		borderBottomLeftRadius: SHOOTRZ_THEME.borderRadius.lg,
	},
	header: {
		flexDirection: 'row',
		alignItems: 'center',
	},
	headerContent: {
		flexDirection: 'row',
		alignItems: 'center',
		flex: 1,
	},
	headerText: {
		marginLeft: SHOOTRZ_THEME.spacing.sm,
		flex: 1,
	},
	title: {
		...SHOOTRZ_THEME.typography.heading3,
		marginBottom: 4,
	},
	description: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		fontSize: 12,
	},
	scoreContainer: {
		marginRight: SHOOTRZ_THEME.spacing.md,
	},
	content: {
		marginTop: SHOOTRZ_THEME.spacing.md,
		paddingTop: SHOOTRZ_THEME.spacing.md,
		borderTopWidth: 1,
		borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
	},
	visualizationContainer: {
		marginBottom: SHOOTRZ_THEME.spacing.md,
	},
	detailsContainer: {
		gap: SHOOTRZ_THEME.spacing.sm,
	},
	detailRow: {
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		paddingVertical: SHOOTRZ_THEME.spacing.xs,
	},
	detailLabel: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		flex: 1,
	},
	detailValueContainer: {
		flexDirection: 'row',
		alignItems: 'baseline',
	},
	detailValue: {
		...SHOOTRZ_THEME.typography.heading3,
		marginRight: 4,
	},
	detailUnit: {
		...SHOOTRZ_THEME.typography.caption,
		color: SHOOTRZ_THEME.colors.textSecondary,
	},
})



