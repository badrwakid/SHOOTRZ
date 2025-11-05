import * as Haptics from 'expo-haptics';

export const hapticFeedback = {
  // Light feedback for subtle interactions
  light: () => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } catch (error) {
      // Silently fail if haptics not supported
    }
  },

  // Medium feedback for button presses
  medium: () => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    } catch (error) {
      // Silently fail if haptics not supported
    }
  },

  // Heavy feedback for important actions
  heavy: () => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    } catch (error) {
      // Silently fail if haptics not supported
    }
  },

  // Selection feedback for toggles and switches
  selection: () => {
    try {
      Haptics.selectionAsync();
    } catch (error) {
      // Silently fail if haptics not supported
    }
  },

  // Success feedback for achievements
  success: () => {
    try {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      // Silently fail if haptics not supported
    }
  },

  // Warning feedback for errors
  warning: () => {
    try {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
    } catch (error) {
      // Silently fail if haptics not supported
    }
  },

  // Error feedback for failures
  error: () => {
    try {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } catch (error) {
      // Silently fail if haptics not supported
    }
  },
};
