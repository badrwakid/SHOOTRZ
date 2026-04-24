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
import { spacing } from '../constants/theme'
import { useTokens } from '../theme/useTokens'
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

type TabIconName = keyof typeof Ionicons.glyphMap
type TabIconProps = { name: TabIconName; focused: boolean; color: string; brandPrimary: string }

function TabIcon({ name, focused, color, brandPrimary }: TabIconProps) {
	return (
		<View style={{ alignItems: 'center' }}>
			{focused ? (
				<View
					style={{
						width: 24,
						height: 2,
						borderRadius: 1,
						backgroundColor: brandPrimary,
						marginBottom: spacing[1],
					}}
				/>
			) : (
				<View style={{ height: 6 }} />
			)}
			<Ionicons name={name} size={22} color={color} />
		</View>
	)
}

export const AppNavigator: React.FC = () => {
	const insets = useSafeAreaInsets()
	const t = useTokens()
	const brandPrimary = t.tokens.brand.primary

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
						backgroundColor: t.tokens.bg.secondary,
						borderTopWidth: 1,
						borderTopColor: t.tokens.border.subtle,
						paddingTop: spacing[1],
						paddingBottom: Math.max(6, insets.bottom),
						paddingHorizontal: spacing[1],
						height: 56 + insets.bottom,
					},
					tabBarActiveTintColor: brandPrimary,
					tabBarInactiveTintColor: t.tokens.text.tertiary,
					tabBarLabelStyle: {
						...t.typography.caption,
						marginTop: 0,
					},
					tabBarItemStyle: {
						paddingVertical: spacing[1],
					},
				}}
			>
				<Tab.Screen
					name="Home"
					component={HomeScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon
								name={focused ? 'home' : 'home-outline'}
								focused={focused}
								color={color}
								brandPrimary={brandPrimary}
							/>
						),
					}}
				/>
				<Tab.Screen
					name="Analyze"
					component={MVPAnalysisScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon
								name={focused ? 'analytics' : 'analytics-outline'}
								focused={focused}
								color={color}
								brandPrimary={brandPrimary}
							/>
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
							<TabIcon
								name={focused ? 'basketball' : 'basketball-outline'}
								focused={focused}
								color={color}
								brandPrimary={brandPrimary}
							/>
						),
					}}
				/>
				<Tab.Screen
					name="Workouts"
					component={WorkoutsScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon
								name={focused ? 'barbell' : 'barbell-outline'}
								focused={focused}
								color={color}
								brandPrimary={brandPrimary}
							/>
						),
					}}
				/>
				<Tab.Screen
					name="Coach J"
					component={ChatScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon
								name={focused ? 'chatbubbles' : 'chatbubbles-outline'}
								focused={focused}
								color={color}
								brandPrimary={brandPrimary}
							/>
						),
					}}
				/>
				<Tab.Screen
					name="Progress"
					component={ProgressScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon
								name={focused ? 'stats-chart' : 'stats-chart-outline'}
								focused={focused}
								color={color}
								brandPrimary={brandPrimary}
							/>
						),
					}}
				/>
				<Tab.Screen
					name="Profile"
					component={ProfileScreen}
					listeners={tabListeners}
					options={{
						tabBarIcon: ({ color, focused }) => (
							<TabIcon
								name={focused ? 'person' : 'person-outline'}
								focused={focused}
								color={color}
								brandPrimary={brandPrimary}
							/>
						),
					}}
				/>
			</Tab.Navigator>
		</NavigationContainer>
	)
}
