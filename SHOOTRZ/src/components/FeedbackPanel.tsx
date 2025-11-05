import React, { useState } from 'react'
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	TouchableOpacity,
	FlatList,
} from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import { Ionicons } from '@expo/vector-icons'
import { SHOOTRZ_THEME } from '../constants/theme'

export interface FeedbackItem {
	message: string
	severity?: 'info' | 'warning' | 'error'
	details?: string
	metric_name?: string
	value?: number
	frame_idx?: number
}

interface FeedbackPanelProps {
	items: FeedbackItem[]
	onFeedbackPress?: (feedback: FeedbackItem) => void
	collapsible?: boolean
}

export function FeedbackPanel({
	items,
	onFeedbackPress,
	collapsible = true,
}: FeedbackPanelProps) {
	const [expandedSections, setExpandedSections] = useState<Set<string>>(
		new Set(['error', 'warning'])
	)

	const groupedFeedback = items.reduce(
		(acc, item) => {
			const severity = item.severity || 'info'
			if (!acc[severity]) {
				acc[severity] = []
			}
			acc[severity].push(item)
			return acc
		},
		{} as Record<string, FeedbackItem[]>
	)

	const toggleSection = (severity: string) => {
		if (!collapsible) return
		const newExpanded = new Set(expandedSections)
		if (newExpanded.has(severity)) {
			newExpanded.delete(severity)
		} else {
			newExpanded.add(severity)
		}
		setExpandedSections(newExpanded)
	}

	const getSeverityConfig = (severity: string) => {
		switch (severity) {
			case 'error':
				return {
					color: SHOOTRZ_THEME.colors.error,
					icon: 'alert-circle',
					label: 'Critical',
					bgColor: [SHOOTRZ_THEME.colors.error + '20', SHOOTRZ_THEME.colors.error + '10'],
				}
			case 'warning':
				return {
					color: SHOOTRZ_THEME.colors.warning,
					icon: 'warning',
					label: 'Warning',
					bgColor: [SHOOTRZ_THEME.colors.warning + '20', SHOOTRZ_THEME.colors.warning + '10'],
				}
			default:
				return {
					color: SHOOTRZ_THEME.colors.primary,
					icon: 'information-circle',
					label: 'Info',
					bgColor: [SHOOTRZ_THEME.colors.primary + '20', SHOOTRZ_THEME.colors.primary + '10'],
				}
		}
	}

	const renderFeedbackItem = (item: FeedbackItem, index: number) => {
		const severity = item.severity || 'info'
		const config = getSeverityConfig(severity)

		return (
			<TouchableOpacity
				key={index}
				style={styles.feedbackItem}
				onPress={() => onFeedbackPress?.(item)}
				activeOpacity={onFeedbackPress ? 0.7 : 1}
			>
				<View style={styles.feedbackContent}>
					{/* Icon and Message */}
					<View style={styles.feedbackHeader}>
						<Ionicons name={config.icon as any} size={20} color={config.color} />
						<View style={styles.messageContainer}>
							<Text style={styles.messageText}>{item.message}</Text>
							{item.frame_idx !== undefined && (
								<Text style={styles.frameReference}>
									Frame {item.frame_idx}
								</Text>
							)}
						</View>
					</View>

					{/* Details */}
					{item.details && (
						<View style={styles.detailsContainer}>
							<Text style={styles.detailsText}>{item.details}</Text>
						</View>
					)}

					{/* Metric Info */}
					{item.metric_name && (
						<View style={styles.metricInfoContainer}>
							<Text style={styles.metricInfoText}>
								Metric: {item.metric_name}
								{item.value !== undefined && ` (${item.value.toFixed(1)})`}
							</Text>
						</View>
					)}
				</View>
			</TouchableOpacity>
		)
	}

	const renderSection = (severity: string, items: FeedbackItem[]) => {
		const config = getSeverityConfig(severity)
		const isExpanded = expandedSections.has(severity)

		return (
			<View key={severity} style={styles.section}>
				{/* Section Header */}
				<TouchableOpacity
					style={styles.sectionHeader}
					onPress={() => toggleSection(severity)}
					activeOpacity={collapsible ? 0.7 : 1}
				>
					<LinearGradient
						colors={config.bgColor}
						style={styles.sectionHeaderGradient}
					>
						<View style={styles.sectionHeaderContent}>
							<Ionicons name={config.icon as any} size={24} color={config.color} />
							<Text style={[styles.sectionTitle, { color: config.color }]}>
								{config.label}
							</Text>
							<Text style={styles.sectionCount}>
								{items.length} item{items.length !== 1 ? 's' : ''}
							</Text>
						</View>
						{collapsible && (
							<Ionicons
								name={isExpanded ? 'chevron-up' : 'chevron-down'}
								size={20}
								color={config.color}
							/>
						)}
					</LinearGradient>
				</TouchableOpacity>

				{/* Section Items */}
				{isExpanded && (
					<View style={styles.sectionItems}>
						{items.map((item, index) => renderFeedbackItem(item, index))}
					</View>
				)}
			</View>
		)
	}

	if (items.length === 0) {
		return (
			<View style={styles.emptyContainer}>
				<Ionicons
					name="checkmark-circle-outline"
					size={48}
					color={SHOOTRZ_THEME.colors.success}
				/>
				<Text style={styles.emptyText}>Great job! No issues detected.</Text>
			</View>
		)
	}

	// Render sections in priority order: error, warning, info
	const sections = ['error', 'warning', 'info'].filter((s) => groupedFeedback[s])

	return (
		<View style={styles.container}>
			<View style={styles.header}>
				<Text style={styles.headerTitle}>Feedback & Tips</Text>
				<Text style={styles.headerSubtitle}>
					{items.length} tip{items.length !== 1 ? 's' : ''} for improvement
				</Text>
			</View>

			<ScrollView style={styles.scrollView} nestedScrollEnabled>
				{sections.map((severity) => renderSection(severity, groupedFeedback[severity]))}
			</ScrollView>
		</View>
	)
}

const styles = StyleSheet.create({
	container: {
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: 12,
		padding: 16,
		marginVertical: 8,
		maxHeight: 600,
	},
	header: {
		marginBottom: 16,
	},
	headerTitle: {
		fontSize: 20,
		fontWeight: 'bold',
		color: SHOOTRZ_THEME.colors.text,
	},
	headerSubtitle: {
		fontSize: 14,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: 4,
	},
	scrollView: {
		flex: 1,
	},
	section: {
		marginBottom: 12,
	},
	sectionHeader: {
		borderRadius: 8,
		overflow: 'hidden',
		marginBottom: 8,
	},
	sectionHeaderGradient: {
		padding: 12,
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'space-between',
	},
	sectionHeaderContent: {
		flexDirection: 'row',
		alignItems: 'center',
		flex: 1,
	},
	sectionTitle: {
		fontSize: 16,
		fontWeight: 'bold',
		marginLeft: 8,
	},
	sectionCount: {
		fontSize: 12,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginLeft: 'auto',
		marginRight: 8,
	},
	sectionItems: {
		gap: 8,
	},
	feedbackItem: {
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		borderRadius: 8,
		padding: 12,
		marginVertical: 4,
	},
	feedbackContent: {
		flex: 1,
	},
	feedbackHeader: {
		flexDirection: 'row',
		alignItems: 'flex-start',
		marginBottom: 8,
	},
	messageContainer: {
		flex: 1,
		marginLeft: 12,
	},
	messageText: {
		fontSize: 15,
		fontWeight: '600',
		color: SHOOTRZ_THEME.colors.text,
		lineHeight: 20,
	},
	frameReference: {
		fontSize: 12,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: 4,
		fontStyle: 'italic',
	},
	detailsContainer: {
		marginTop: 8,
		paddingLeft: 32,
	},
	detailsText: {
		fontSize: 13,
		color: SHOOTRZ_THEME.colors.textSecondary,
		lineHeight: 18,
	},
	metricInfoContainer: {
		marginTop: 8,
		paddingTop: 8,
		borderTopWidth: 1,
		borderTopColor: SHOOTRZ_THEME.colors.surface,
	},
	metricInfoText: {
		fontSize: 12,
		color: SHOOTRZ_THEME.colors.primary,
		fontWeight: '500',
	},
	emptyContainer: {
		alignItems: 'center',
		justifyContent: 'center',
		padding: 40,
	},
	emptyText: {
		fontSize: 16,
		color: SHOOTRZ_THEME.colors.success,
		marginTop: 12,
		fontWeight: '600',
	},
})
