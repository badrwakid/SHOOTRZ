import React, { useCallback } from 'react'
import { View } from 'react-native'
import { NavigationContainer } from '@react-navigation/native'
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { useSafeAreaInsets } from 'react-native-safe-area-context'
import * as Linking from 'expo-linking'
import { Ionicons } from '@expo/vector-icons'
import { HomeScreen } from '../screens/HomeScreen'
import { MVPAnalysisScreen } from '../screens/MVPAnalysisScreen'
import { DrillsScreen } from '../screens/DrillsScreen'
import { WorkoutsScreen } from '../screens/WorkoutsScreen'
import { ProgressScreen } from '../screens/ProgressScreen'
import { ProfileScreen } from '../screens/ProfileScreen'
import { ChatScreen } from '../screens/ChatScreen'
import { colors, typography, spacing } from '../constants/theme'
import { hapticFeedback } from '../utils/hapticFeedback'

const Tab = createBottomTabNavigator()

const linking = {
	prefixes: [
		Linking.createURL('/'),
		'exp://',
	],
	config: {
		screens: {},
	},
}

function TabIcon({ name, focused, color }: { name: string; focused: boolean; color: string }) {
	return (
		<View style={{ alignItems: 'center' }}>
			{focused ? (
				<View
					style={{
						width: 24,
						height: 2,
						borderRadius: 1,
						backgroundColor: colors.brand.orange,
						marginBottom: 4,
					}}
				/>
			) : (
				<View style={{ height: 6 }} />
			)}
			<Ionicons name={name as any} size={22} color={color} />
		</View>
	)
}

export const AppNavigator: React.FC = () => {
	const insets = useSafeAreaInsets()

	const tabListeners = useCallback(
		() => ({
			tabPress: () => hapticFeedback.selection(),
		}),
		[],
	)

	return (
		<NavigationContainer linking={linking}>
			<Tab.Navigator
				screenOptions={{
					headerShown: false,
					tabBarStyle: {
						backgroundColor: colors.bg.secondary,
						borderTopWidth: 1,
						borderTopColor: colors.border.subtle,
						paddingBottom: Math.max(4, insets.bottom),
						paddingTop: 0,
						height: 49 + insets.bottom,
					},
					tabBarActiveTintColor: colors.brand.orange,
					tabBarInactiveTintColor: colors.text.tertiary,
					tabBarLabelStyle: {
						fontSize: typography.size.xs,
						fontWeight: typography.weight.semibold,
						marginTop: 0,
					},
					tabBarItemStyle: {
						paddingVertical: 0,
					},
				}}
			>
				<Tab.Screen
					name="Home"
					component={HomeScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon name={focused ? 'home' : 'home-outline'} focused={focused} color={color} />
						),
					}}
				/>
				<Tab.Screen
					name="Analyze"
					component={MVPAnalysisScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon name={focused ? 'analytics' : 'analytics-outline'} focused={focused} color={color} />
						),
						tabBarLabel: 'Analyze',
					}}
				/>
				<Tab.Screen
					name="Drills"
					component={DrillsScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon name={focused ? 'basketball' : 'basketball-outline'} focused={focused} color={color} />
						),
					}}
				/>
				<Tab.Screen
					name="Workouts"
					component={WorkoutsScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon name={focused ? 'barbell' : 'barbell-outline'} focused={focused} color={color} />
						),
					}}
				/>
				<Tab.Screen
					name="Coach J"
					component={ChatScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon name={focused ? 'chatbubbles' : 'chatbubbles-outline'} focused={focused} color={color} />
						),
					}}
				/>
				<Tab.Screen
					name="Progress"
					component={ProgressScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon name={focused ? 'stats-chart' : 'stats-chart-outline'} focused={focused} color={color} />
						),
					}}
				/>
				<Tab.Screen
					name="Profile"
					component={ProfileScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon name={focused ? 'person' : 'person-outline'} focused={focused} color={color} />
						),
					}}
				/>
			</Tab.Navigator>
		</NavigationContainer>
	)
}
