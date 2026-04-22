import React, { useState } from 'react'
import {
	View,
	Text,
	StyleSheet,
	FlatList,
	TouchableOpacity,
	Alert,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius } from '../constants/theme'
import { WorkoutCard } from '../components/WorkoutCard'
import { EmptyState } from '../components/EmptyState'
import { storageService } from '../services/storage.service'
import { useAuth } from '../context/AuthContext'
import { WORKOUTS } from '../constants/drills'
import { hapticFeedback } from '../utils/hapticFeedback'

type FilterTab = 'all' | 'active' | 'completed'

export const WorkoutsScreen: React.FC = () => {
	const { user } = useAuth()
	const [activeWorkouts, setActiveWorkouts] = useState<string[]>([])
	const [workoutStartTimes, setWorkoutStartTimes] = useState<Record<string, Date>>({})
	const [filterTab, setFilterTab] = useState<FilterTab>('all')

	const handleStartWorkout = (workoutId: string) => {
		if (activeWorkouts.includes(workoutId)) {
			Alert.alert(
				'Complete Workout?',
				'Would you like to mark this workout as complete?',
				[
					{ text: 'Cancel', style: 'cancel' },
					{
						text: 'Complete',
						onPress: async () => {
							const start = workoutStartTimes[workoutId]
							const durationMin = start ? Math.round((Date.now() - start.getTime()) / 60000) : 0
							await saveWorkoutSession(workoutId, durationMin)
							setActiveWorkouts(prev => prev.filter(id => id !== workoutId))
							setWorkoutStartTimes(prev => { const copy = { ...prev }; delete copy[workoutId]; return copy })
							hapticFeedback.success()
							Alert.alert('Workout Complete!', 'Great work!')
						},
					},
				],
			)
		} else {
			hapticFeedback.medium()
			setActiveWorkouts(prev => [...prev, workoutId])
			setWorkoutStartTimes(prev => ({ ...prev, [workoutId]: new Date() }))
		}
	}

	const saveWorkoutSession = async (workoutId: string, duration: number) => {
		const workout = WORKOUTS.find(w => w.id === workoutId)
		const session = {
			id: Date.now().toString(),
			userId: user?.id || 'guest',
			workoutId,
			workoutName: workout?.name || 'Workout',
			completedAt: new Date().toISOString(),
			duration,
			drillsCompleted: workout?.drills?.length || 0,
		}
		await storageService.saveWorkoutSession(session)
	}

	const filteredWorkouts = WORKOUTS.filter(w => {
		if (filterTab === 'active') return activeWorkouts.includes(w.id)
		if (filterTab === 'completed') return !activeWorkouts.includes(w.id)
		return true
	})

	const renderItem = ({ item }: { item: typeof WORKOUTS[0] }) => {
		const isActive = activeWorkouts.includes(item.id)
		return (
			<View style={[styles.cardWrap, isActive && styles.cardActive]}>
				<WorkoutCard
					name={item.name}
					drillCount={item.drills?.length || 0}
					estimatedMinutes={item.estimatedMinutes || 15}
					difficulty={item.difficulty || 'intermediate'}
					progress={isActive ? 0.5 : 0}
					onPress={() => handleStartWorkout(item.id)}
				/>
			</View>
		)
	}

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
			{/* Filter Tabs */}
			<View style={styles.tabs}>
				{(['all', 'active', 'completed'] as const).map(tab => (
					<TouchableOpacity
						key={tab}
						style={[styles.tab, filterTab === tab && styles.tabActive]}
						onPress={() => { hapticFeedback.selection(); setFilterTab(tab) }}
					>
						<Text style={[styles.tabText, filterTab === tab && styles.tabTextActive]}>
							{tab.charAt(0).toUpperCase() + tab.slice(1)}
						</Text>
					</TouchableOpacity>
				))}
			</View>

			{filteredWorkouts.length === 0 ? (
				<EmptyState
					icon="barbell-outline"
					title="No workouts here"
					message={filterTab === 'active' ? "Start a workout to see it here." : "No workouts match this filter."}
				/>
			) : (
				<FlatList
					data={filteredWorkouts}
					renderItem={renderItem}
					keyExtractor={w => w.id}
					contentContainerStyle={styles.list}
					showsVerticalScrollIndicator={false}
					removeClippedSubviews
				/>
			)}
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: { flex: 1, backgroundColor: colors.bg.primary },
	tabs: {
		flexDirection: 'row',
		gap: spacing[2],
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[3],
	},
	tab: {
		flex: 1,
		paddingVertical: spacing[2],
		borderRadius: radius.pill,
		borderWidth: 1,
		borderColor: colors.border.default,
		alignItems: 'center',
	},
	tabActive: {
		backgroundColor: colors.brand.orange,
		borderColor: colors.brand.orange,
	},
	tabText: {
		fontSize: typography.size.sm,
		color: colors.text.secondary,
		fontWeight: typography.weight.medium,
	},
	tabTextActive: {
		color: colors.text.primary,
		fontWeight: typography.weight.bold,
	},
	list: {
		paddingHorizontal: spacing.screenPadding,
		paddingBottom: spacing.tabBarHeight,
	},
	cardWrap: {
		marginBottom: spacing.itemGap,
	},
	cardActive: {
		borderWidth: 1,
		borderColor: colors.brand.orange,
		borderRadius: radius.card,
	},
})
