import React, { useState, useMemo } from 'react'
import {
	View,
	Text,
	StyleSheet,
	FlatList,
	TouchableOpacity,
	Modal,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius } from '../constants/theme'
import { DrillDetailScreen } from './DrillDetailScreen'
import { EmptyState } from '../components/EmptyState'
import { hapticFeedback } from '../utils/hapticFeedback'
import { DRILLS, Drill } from '../constants/drills'

const CATEGORIES = ['all', 'shooting', 'form', 'footwork', 'follow-through']
const DIFFICULTIES = ['all', 'beginner', 'intermediate', 'advanced']

export const DrillsScreen: React.FC = () => {
	const [selectedCategory, setSelectedCategory] = useState('all')
	const [selectedDifficulty, setSelectedDifficulty] = useState('all')
	const [selectedDrill, setSelectedDrill] = useState<Drill | null>(null)

	const filteredDrills = useMemo(() => {
		return DRILLS.filter(d => {
			if (selectedCategory !== 'all' && d.category.toLowerCase() !== selectedCategory) return false
			if (selectedDifficulty !== 'all' && d.difficulty !== selectedDifficulty) return false
			return true
		})
	}, [selectedCategory, selectedDifficulty])

	const handleDrillPress = (drill: Drill) => {
		hapticFeedback.light()
		setSelectedDrill(drill)
	}

	const renderDrillItem = ({ item }: { item: Drill }) => (
		<TouchableOpacity
			style={styles.drillCard}
			onPress={() => handleDrillPress(item)}
			activeOpacity={0.85}
		>
			<View style={[styles.drillHeader, {
				backgroundColor:
					item.difficulty === 'beginner' ? colors.success + '15'
						: item.difficulty === 'advanced' ? colors.error + '15'
							: colors.warning + '15',
			}]}>
				<View style={[styles.diffBadge, {
					backgroundColor:
						item.difficulty === 'beginner' ? colors.success + '30'
							: item.difficulty === 'advanced' ? colors.error + '30'
								: colors.warning + '30',
				}]}>
					<Text style={[styles.diffText, {
						color:
							item.difficulty === 'beginner' ? colors.success
								: item.difficulty === 'advanced' ? colors.error
									: colors.warning,
					}]}>
						{item.difficulty.toUpperCase()}
					</Text>
				</View>
				{item.duration ? (
					<View style={styles.durationPill}>
						<Ionicons name="time-outline" size={12} color={colors.text.primary} />
						<Text style={styles.durationText}>{item.duration}</Text>
					</View>
				) : null}
			</View>
			<View style={styles.drillBody}>
				<Text style={styles.drillName} numberOfLines={2}>{item.name}</Text>
				<View style={styles.categoryPill}>
					<Text style={styles.categoryText}>{item.category}</Text>
				</View>
			</View>
		</TouchableOpacity>
	)

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
			{/* Category Filter */}
			<FlatList
				horizontal
				data={CATEGORIES}
				keyExtractor={c => c}
				showsHorizontalScrollIndicator={false}
				contentContainerStyle={styles.filterRow}
				renderItem={({ item: cat }) => (
					<TouchableOpacity
						style={[styles.filterPill, selectedCategory === cat && styles.filterPillActive]}
						onPress={() => { hapticFeedback.selection(); setSelectedCategory(cat) }}
					>
						<Text style={[styles.filterText, selectedCategory === cat && styles.filterTextActive]}>
							{cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)}
						</Text>
					</TouchableOpacity>
				)}
			/>

			{/* Difficulty Filter */}
			<FlatList
				horizontal
				data={DIFFICULTIES}
				keyExtractor={d => d}
				showsHorizontalScrollIndicator={false}
				contentContainerStyle={styles.filterRow}
				renderItem={({ item: diff }) => (
					<TouchableOpacity
						style={[styles.filterPill, selectedDifficulty === diff && styles.filterPillActive]}
						onPress={() => { hapticFeedback.selection(); setSelectedDifficulty(diff) }}
					>
						<Text style={[styles.filterText, selectedDifficulty === diff && styles.filterTextActive]}>
							{diff === 'all' ? 'All' : diff.charAt(0).toUpperCase() + diff.slice(1)}
						</Text>
					</TouchableOpacity>
				)}
			/>

			{/* Drill Grid */}
			{filteredDrills.length === 0 ? (
				<EmptyState
					icon="basketball-outline"
					title="No drills match"
					message="Try adjusting your filters."
					action={{ label: 'Clear Filters', onPress: () => { setSelectedCategory('all'); setSelectedDifficulty('all') } }}
				/>
			) : (
				<FlatList
					data={filteredDrills}
					renderItem={renderDrillItem}
					keyExtractor={d => d.id}
					numColumns={2}
					contentContainerStyle={styles.grid}
					columnWrapperStyle={styles.gridRow}
					showsVerticalScrollIndicator={false}
					removeClippedSubviews
				/>
			)}

			{/* Drill Detail Modal */}
			<Modal
				visible={selectedDrill !== null}
				animationType="slide"
				transparent={false}
				onRequestClose={() => setSelectedDrill(null)}
			>
				{selectedDrill ? (
					<DrillDetailScreen drill={selectedDrill} onClose={() => setSelectedDrill(null)} />
				) : null}
			</Modal>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: { flex: 1, backgroundColor: colors.bg.primary },
	filterRow: {
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[2],
		gap: spacing[2],
	},
	filterPill: {
		paddingHorizontal: spacing[3],
		paddingVertical: spacing[2],
		borderRadius: radius.pill,
		borderWidth: 1,
		borderColor: colors.border.default,
	},
	filterPillActive: {
		backgroundColor: colors.brand.orange,
		borderColor: colors.brand.orange,
	},
	filterText: {
		fontSize: typography.size.sm,
		color: colors.text.secondary,
	},
	filterTextActive: {
		color: colors.text.primary,
		fontWeight: typography.weight.bold,
	},
	grid: {
		paddingHorizontal: spacing.screenPadding,
		paddingTop: spacing[2],
		paddingBottom: spacing.tabBarHeight,
	},
	gridRow: {
		gap: spacing[3],
	},
	drillCard: {
		flex: 1,
		backgroundColor: colors.bg.secondary,
		borderRadius: radius.card,
		borderWidth: 1,
		borderColor: colors.border.default,
		overflow: 'hidden',
		marginBottom: spacing[3],
	},
	drillHeader: {
		height: 80,
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'flex-start',
		padding: spacing[2],
	},
	diffBadge: {
		paddingHorizontal: spacing[2],
		paddingVertical: 2,
		borderRadius: radius.pill,
	},
	diffText: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.bold,
		letterSpacing: typography.tracking.wide,
	},
	durationPill: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: 3,
		backgroundColor: 'rgba(0,0,0,0.4)',
		borderRadius: radius.pill,
		paddingHorizontal: spacing[2],
		paddingVertical: 2,
	},
	durationText: {
		fontSize: typography.size.xs,
		color: colors.text.primary,
	},
	drillBody: {
		padding: spacing[3],
	},
	drillName: {
		fontSize: typography.size.sm,
		fontWeight: typography.weight.semibold,
		color: colors.text.primary,
		marginBottom: spacing[2],
	},
	categoryPill: {
		backgroundColor: colors.brand.orangeDim,
		borderRadius: radius.pill,
		paddingHorizontal: spacing[2],
		paddingVertical: 2,
		alignSelf: 'flex-start',
	},
	categoryText: {
		fontSize: typography.size.xs,
		color: colors.brand.orangeLight,
		fontWeight: typography.weight.medium,
	},
})
