import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { HomeScreen } from '../screens/HomeScreen';
import { AnalyzeScreen } from '../screens/AnalyzeScreen';
import { DrillsScreen } from '../screens/DrillsScreen';
import { WorkoutsScreen } from '../screens/WorkoutsScreen';
import { ProgressScreen } from '../screens/ProgressScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { ChatScreen } from '../screens/ChatScreen';
import { SHOOTRZ_THEME } from '../constants/theme';

const Tab = createBottomTabNavigator();

export const AppNavigator: React.FC = () => {
  const insets = useSafeAreaInsets();
  
  return (
    <NavigationContainer>
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
            tabBarIcon: ({ color }) => (
              <Ionicons name="home" size={20} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Analyze"
          component={AnalyzeScreen}
          options={{
            tabBarIcon: ({ color }) => (
              <Ionicons name="videocam" size={20} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Drills"
          component={DrillsScreen}
          options={{
            tabBarIcon: ({ color }) => (
              <Ionicons name="basketball" size={20} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Workouts"
          component={WorkoutsScreen}
          options={{
            tabBarIcon: ({ color }) => (
              <Ionicons name="barbell" size={20} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Coach J"
          component={ChatScreen}
          options={{
            tabBarIcon: ({ color }) => (
              <Ionicons name="chatbubbles" size={20} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Progress"
          component={ProgressScreen}
          options={{
            tabBarIcon: ({ color }) => (
              <Ionicons name="stats-chart" size={20} color={color} />
            ),
          }}
        />
        <Tab.Screen
          name="Profile"
          component={ProfileScreen}
          options={{
            tabBarIcon: ({ color }) => (
              <Ionicons name="person" size={20} color={color} />
            ),
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
};
