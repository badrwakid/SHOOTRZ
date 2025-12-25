import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Linking from 'expo-linking';
import { Ionicons } from '@expo/vector-icons';
import { HomeScreen } from '../screens/HomeScreen';
import { DrillsScreen } from '../screens/DrillsScreen';
import { WorkoutsScreen } from '../screens/WorkoutsScreen';
import { ProgressScreen } from '../screens/ProgressScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { ChatScreen } from '../screens/ChatScreen';
import { SHOOTRZ_THEME } from '../constants/theme';

const Tab = createBottomTabNavigator();

// Configure linking for deep links
// Include exp:// scheme for development OAuth redirects
const linking = {
	prefixes: [
		Linking.createURL('/'), // shootrz://
		'exp://', // exp:// URLs for development (e.g., exp://192.168.56.1:8081)
	],
	config: {
		// Explicit screen mapping (optional, but helps with deep link routing)
		screens: {
			// Navigation screens can be mapped here if needed
			// For now, we're handling OAuth callbacks in useDeepLinks hook
		},
	},
};

export const AppNavigator: React.FC = () => {
  const insets = useSafeAreaInsets();

  return (
    <NavigationContainer linking={linking}>
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: SHOOTRZ_THEME.colors.background,
            borderTopWidth: 1,
            borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
            paddingBottom: Math.max(4, insets.bottom),
            paddingTop: 4,
            height: 60 + insets.bottom,
          },
          tabBarActiveTintColor: SHOOTRZ_THEME.colors.primary,
          tabBarInactiveTintColor: SHOOTRZ_THEME.colors.textSecondary,
          tabBarLabelStyle: {
            fontSize: 9,
            fontWeight: '500',
            marginTop: 1,
          },
          tabBarItemStyle: {
            paddingVertical: 2,
            paddingHorizontal: 1,
          },
        }}
      >
        <Tab.Screen
          name="Home"
          component={HomeScreen}
          options={{
            tabBarIcon: ({ color }) => <Ionicons name="home" size={20} color={color} />,
          }}
        />
        <Tab.Screen
          name="Drills"
          component={DrillsScreen}
          options={{
            tabBarIcon: ({ color }) => <Ionicons name="basketball" size={20} color={color} />,
          }}
        />
        <Tab.Screen
          name="Workouts"
          component={WorkoutsScreen}
          options={{
            tabBarIcon: ({ color }) => <Ionicons name="barbell" size={20} color={color} />,
          }}
        />
        <Tab.Screen
          name="Coach J"
          component={ChatScreen}
          options={{
            tabBarIcon: ({ color }) => <Ionicons name="chatbubbles" size={20} color={color} />,
          }}
        />
        <Tab.Screen
          name="Progress"
          component={ProgressScreen}
          options={{
            tabBarIcon: ({ color }) => <Ionicons name="stats-chart" size={20} color={color} />,
          }}
        />
        <Tab.Screen
          name="Profile"
          component={ProfileScreen}
          options={{
            tabBarIcon: ({ color }) => <Ionicons name="person" size={20} color={color} />,
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
};
