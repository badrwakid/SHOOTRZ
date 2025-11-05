import React, { useState } from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { LinearGradient } from 'expo-linear-gradient'
import { SHOOTRZ_THEME } from '../constants/theme'
import { GradientCard } from './GradientCard'

interface FeedbackItem {
	message: string
	severity?: 'info' | 'warning' | 'critical'
	metricName?: string
	frameReference?: number
}

interface FeedbackCategoryPanelProps {
	category: string
	feedbackItems: FeedbackItem[]
	icon?: keyof typeof Ionicons.glyphMap
	color?: string
}

export const FeedbackCategoryPanel: React.FC<FeedbackCategoryPanelProps> = ({
	category,
	feedbackItems,
	icon = 'bulb',
	color = SHOOTRZ_THEME.colors.primary,
}) => {
	const [isExpanded, setIsExpanded] = useState(true)

	if (!feedbackItems || feedbackItems.length === 0) {
		return null
	}

	const getSeverityColor = (severity?: string) => {
		switch (severity) {
			case 'critical':
				return SHOOTRZ_THEME.colors.error
			case 'warning':
				return SHOOTRZ_THEME.colors.warning
			case 'info':
			default:
				return SHOOTRZ_THEME.colors.accent
		}
	}

	const getSeverityIcon = (severity?: string) => {
		switch (severity) {
			case 'critical':
				return 'alert-circle'
			case 'warning':
				return 'warning'
			case 'info':
			default:
				return 'information-circle'
		}
	}

	return (
		<View style={styles.container}>
			<TouchableOpacity
				style={styles.header}
				onPress={() => setIsExpanded(!isExpanded)}
				activeOpacity={0.7}
			>
				<View style={styles.headerContent}>
					<Ionicons name={icon} size={24} color={color} />
					<Text style={styles.categoryTitle}>{category}</Text>
					<Text style={styles.count}>{feedbackItems.length}</Text>
				</View>
				<Ionicons
					name={isExpanded ? 'chevron-up' : 'chevron-down'}
					size={20}
					color={SHOOTRZ_THEME.colors.textSecondary}
				/>
			</TouchableOpacity>

			{isExpanded && (
				<View style={styles.content}>
					{feedbackItems.map((item, index) => (
						<GradientCard
							key={index}
							style={styles.feedbackItem}
							glowColor={getSeverityColor(item.severity)}
						>
							<View style={styles.feedbackHeader}>
								<Ionicons
									name={getSeverityIcon(item.severity) as any}
									size={18}
									color={getSeverityColor(item.severity)}
									style={styles.severityIcon}
								/>
								{item.metricName && (
									<Text style={styles.metricLabel}>{item.metricName}</Text>
								)}
								{item.frameReference !== undefined && (
									<Text style={styles.frameLabel}>
										Frame {item.frameReference}
									</Text>
								)}
							</View>
							<Text style={styles.feedbackMessage}>{item.message}</Text>
						</GradientCard>
					))}
				</View>
			)}
		</View>
	)
}

const styles = StyleSheet.create({
	container: {
		marginBottom: SHOOTRZ_THEME.spacing.lg,
	},
	header: {
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		padding: SHOOTRZ_THEME.spacing.md,
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		borderRadius: SHOOTRZ_THEME.borderRadius.md,
		marginBottom: SHOOTRZ_THEME.spacing.sm,
	},
	headerContent: {
		flexDirection: 'row',
		alignItems: 'center',
		flex: 1,
	},
	categoryTitle: {
		...SHOOTRZ_THEME.typography.heading3,
		marginLeft: SHOOTRZ_THEME.spacing.sm,
		flex: 1,
	},
	count: {
		...SHOOTRZ_THEME.typography.caption,
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		paddingHorizontal: 8,
		paddingVertical: 4,
		borderRadius: 12,
		marginLeft: SHOOTRZ_THEME.spacing.sm,
	},
	content: {
		paddingHorizontal: SHOOTRZ_THEME.spacing.sm,
	},
	feedbackItem: {
		marginBottom: SHOOTRZ_THEME.spacing.sm,
	},
	feedbackHeader: {
		flexDirection: 'row',
		alignItems: 'center',
		marginBottom: SHOOTRZ_THEME.spacing.xs,
	},
	severityIcon: {
		marginRight: SHOOTRZ_THEME.spacing.xs,
	},
	metricLabel: {
		...SHOOTRZ_THEME.typography.caption,
		color: SHOOTRZ_THEME.colors.primary,
		fontWeight: '600',
		marginRight: SHOOTRZ_THEME.spacing.sm,
	},
	frameLabel: {
		...SHOOTRZ_THEME.typography.caption,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginLeft: 'auto',
	},
	feedbackMessage: {
		...SHOOTRZ_THEME.typography.body,
		color: SHOOTRZ_THEME.colors.textPrimary,
		lineHeight: 20,
	},
})



