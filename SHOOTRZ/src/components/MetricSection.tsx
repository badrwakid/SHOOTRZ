import React from 'react'
import { View, Text, StyleSheet, FlatList } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { SHOOTRZ_THEME } from '../constants/theme'
import { MetricCard } from './MetricCard'

interface Metric {
	title: string
	description?: string
	value: number
	unit: string
	optimalRange?: [number, number]
	score?: number
	confidence?: number
	color?: string
	icon?: keyof typeof Ionicons.glyphMap
	showScore?: boolean
}

interface MetricSectionProps {
	title: string
	metrics: Metric[]
	layout?: 'grid' | 'list'
	numColumns?: number
}

export const MetricSection: React.FC<MetricSectionProps> = ({
	title,
	metrics,
	layout = 'grid',
	numColumns = 2,
}) => {
	const renderMetric = ({ item }: { item: Metric }) => (
					<MetricCard
						title={item.title}
						description={item.description}
						value={item.value}
						unit={item.unit}
						optimalRange={item.optimalRange}
						score={item.score}
						confidence={item.confidence}
						color={item.color}
						icon={item.icon}
						showScore={item.showScore !== false}
					/>
	)

	return (
		<View style={styles.container}>
			{title && title.trim() !== '' && (
				<Text style={styles.title}>{title}</Text>
			)}
			{layout === 'grid' ? (
				<FlatList
					data={metrics}
					renderItem={renderMetric}
					keyExtractor={(item, index) => `${item.title}-${index}`}
					numColumns={numColumns}
					scrollEnabled={false}
					columnWrapperStyle={numColumns > 1 ? styles.row : undefined}
					contentContainerStyle={styles.gridContent}
				/>
			) : (
				<View>
					{metrics.map((metric, index) => (
						<MetricCard
							key={`${metric.title}-${index}`}
							{...metric}
						/>
					))}
				</View>
			)}
		</View>
	)
}

const styles = StyleSheet.create({
	container: {
		marginBottom: 0,
	},
	title: {
		...SHOOTRZ_THEME.typography.heading2,
		marginBottom: SHOOTRZ_THEME.spacing.md,
		paddingHorizontal: SHOOTRZ_THEME.spacing.md,
	},
	gridContent: {
		paddingHorizontal: 0,
	},
	row: {
		justifyContent: 'space-between',
	},
})

