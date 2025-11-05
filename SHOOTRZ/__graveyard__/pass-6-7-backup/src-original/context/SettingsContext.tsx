// Settings Context for App-Wide Settings Management
import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { storageService } from '../services/storage.service';
import { Appearance } from 'react-native';
import * as Notifications from 'expo-notifications';

interface SettingsContextType {
  notifications: boolean;
  darkMode: boolean;
  analytics: boolean;
  setNotifications: (enabled: boolean) => Promise<void>;
  setDarkMode: (enabled: boolean) => Promise<void>;
  setAnalytics: (enabled: boolean) => Promise<void>;
  loadSettings: () => Promise<void>;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

interface SettingsProviderProps {
  children: ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [notifications, setNotificationsState] = useState(true);
  const [darkMode, setDarkModeState] = useState(true);
  const [analytics, setAnalyticsState] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const prefs = await storageService.getPreferences();
      setNotificationsState(prefs.notifications);
      setDarkModeState(prefs.darkMode);
      setAnalyticsState(prefs.analytics);

      // Apply dark mode setting
      if (prefs.darkMode) {
        Appearance.setColorScheme('dark');
      } else {
        Appearance.setColorScheme('light');
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const setNotifications = async (enabled: boolean) => {
    try {
      setNotificationsState(enabled);
      
      const prefs = await storageService.getPreferences();
      prefs.notifications = enabled;
      await storageService.savePreferences(prefs);

      if (enabled) {
        // Request notification permissions
        const { status } = await Notifications.requestPermissionsAsync();
        if (status !== 'granted') {
          console.warn('Notification permission not granted');
          // User denied permissions
          return;
        }

        // Schedule practice reminders
        await schedulePracticeReminders();
      } else {
        // Cancel all notifications
        await Notifications.cancelAllScheduledNotificationsAsync();
      }
    } catch (error) {
      console.error('Error setting notifications:', error);
    }
  };

  const setDarkMode = async (enabled: boolean) => {
    try {
      setDarkModeState(enabled);
      
      const prefs = await storageService.getPreferences();
      prefs.darkMode = enabled;
      await storageService.savePreferences(prefs);

      // Apply theme change
      if (enabled) {
        Appearance.setColorScheme('dark');
      } else {
        Appearance.setColorScheme('light');
      }
    } catch (error) {
      console.error('Error setting dark mode:', error);
    }
  };

  const setAnalytics = async (enabled: boolean) => {
    try {
      setAnalyticsState(enabled);
      
      const prefs = await storageService.getPreferences();
      prefs.analytics = enabled;
      await storageService.savePreferences(prefs);

      // In production, this would enable/disable analytics tracking
      console.log(`Analytics ${enabled ? 'enabled' : 'disabled'}`);
    } catch (error) {
      console.error('Error setting analytics:', error);
    }
  };

  const schedulePracticeReminders = async () => {
    try {
      // Schedule daily practice reminder at 6 PM
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Time to Practice! 🏀',
          body: 'Keep your streak going! Practice your shooting form today.',
          sound: true,
        },
        trigger: {
          hour: 18,
          minute: 0,
          repeats: true,
        },
      });
    } catch (error) {
      console.error('Error scheduling notifications:', error);
    }
  };

  const value: SettingsContextType = {
    notifications,
    darkMode,
    analytics,
    setNotifications,
    setDarkMode,
    setAnalytics,
    loadSettings,
  };

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

export const useSettings = (): SettingsContextType => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};
