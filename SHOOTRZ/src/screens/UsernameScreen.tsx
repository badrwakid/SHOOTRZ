import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { ShootrzLogo } from '../components/ShootrzLogo';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../services/supabase.client';

interface UsernameScreenProps {
  onComplete: () => void;
}

export const UsernameScreen: React.FC<UsernameScreenProps> = ({ onComplete }) => {
  const { user, updateProfile } = useAuth();
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const validateUsername = (username: string): string | null => {
    if (!username.trim()) {
      return 'Username is required';
    }
    if (username.length < 3) {
      return 'Username must be at least 3 characters';
    }
    if (username.length > 20) {
      return 'Username must be less than 20 characters';
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      return 'Username can only contain letters, numbers, and underscores';
    }
    return null;
  };

  const checkUsernameAvailability = async (username: string): Promise<boolean> => {
    try {
      const { data, error } = await supabase
        .from('users')
        .select('id')
        .eq('username', username.toLowerCase())
        .single();

      // If user exists and it's not the current user, username is taken
      if (data && user && data.id !== user.id) {
        return false;
      }
      
      // If error is "not found", username is available
      if (error && error.code === 'PGRST116') {
        return true;
      }
      
      // If no error and no data conflict, username is available
      return !data;
    } catch (err) {
      console.error('Error checking username availability:', err);
      // On error, assume available (better UX than blocking)
      return true;
    }
  };

  const handleContinue = async () => {
    // Reset error
    setError('');

    // Validate username
    const validationError = validateUsername(username);
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    try {
      // Check if username is available
      const isAvailable = await checkUsernameAvailability(username);
      if (!isAvailable) {
        setError('This username is already taken. Please choose another.');
        setLoading(false);
        return;
      }

      const trimmedUsername = username.trim().toLowerCase();
      
      if (!user?.id) {
        setError('User ID not found. Please try logging in again.');
        setLoading(false);
        return;
      }
      
      // First, ensure user record exists in database
      // This handles the case where account was deleted but auth user still exists
      console.log('📝 Ensuring user record exists in database...');
      const { data: existingUser, error: checkError } = await supabase
        .from('users')
        .select('id, name')
        .eq('id', user.id)
        .single();
      
      if (checkError && checkError.code === 'PGRST116') {
        // User record doesn't exist - create it
        console.log('📝 User record not found - creating it...');
        const authProvider = user.authProvider || 'google';
        const { error: createError } = await supabase
          .from('users')
          .insert({
            id: user.id,
            email: user.email || '',
            auth_provider: authProvider,
            name: user.name, // Include name from user object
            username: trimmedUsername, // Set username immediately
          });
        
        if (createError) {
          console.error('❌ Failed to create user record:', createError);
          setError('Failed to create account. Please try again.');
          setLoading(false);
          return;
        }
        console.log('✅ User record created with username');
      } else if (checkError) {
        console.error('❌ Error checking user record:', checkError);
        setError('Failed to verify account. Please try again.');
        setLoading(false);
        return;
      } else {
        // User record exists - update username (and name if missing)
        console.log('📝 Updating username in database:', trimmedUsername);
        const updateData: any = { username: trimmedUsername };
        // Only update name if it's missing in database
        if (existingUser?.name === null || existingUser?.name === undefined) {
          updateData.name = user.name;
        }
        const { error: updateError } = await supabase
          .from('users')
          .update(updateData)
          .eq('id', user.id);

        if (updateError) {
          console.error('❌ Failed to update username in database:', updateError);
          setError('Failed to save username. Please try again.');
          setLoading(false);
          return;
        }
        console.log('✅ Username saved to database');
      }

      // Update local user profile (calls updateProfile which also updates DB, but we already did above)
      // This ensures local state is in sync
      await updateProfile({
        username: trimmedUsername,
      });

      // Username set successfully
      onComplete();
    } catch (err: any) {
      console.error('❌ Error setting username:', err);
      setError(err.message || 'Failed to set username. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 100 : 0}
      >
        <View style={styles.content}>
          {/* Logo */}
          <View style={styles.logoContainer}>
            <ShootrzLogo size="large" showTagline={false} />
          </View>

          {/* Title */}
          <View style={styles.titleContainer}>
            <Text style={styles.title}>Choose Your Username</Text>
            <Text style={styles.subtitle}>
              Pick a unique username for your SHOOTRZ profile
            </Text>
          </View>

          {/* Username Input */}
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Username</Text>
            <TextInput
              style={[styles.input, error && styles.inputError]}
              placeholder="Enter username"
              placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
              value={username}
              onChangeText={(text) => {
                setUsername(text);
                setError(''); // Clear error when typing
              }}
              autoCapitalize="none"
              autoCorrect={false}
              maxLength={20}
              editable={!loading}
            />
            {error ? (
              <Text style={styles.errorText}>{error}</Text>
            ) : (
              <Text style={styles.hintText}>
                3-20 characters, letters, numbers, and underscores only
              </Text>
            )}
          </View>

          {/* Continue Button */}
          <TouchableOpacity
            style={[styles.continueButton, (!username.trim() || loading) && styles.continueButtonDisabled]}
            onPress={handleContinue}
            disabled={!username.trim() || loading}
          >
            <Text style={styles.continueButtonText}>
              {loading ? 'Setting up...' : 'Continue →'}
            </Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: SHOOTRZ_THEME.spacing.xl,
    justifyContent: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xxl,
  },
  titleContainer: {
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xl,
  },
  title: {
    ...SHOOTRZ_THEME.typography.heading1,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  subtitle: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
  },
  inputContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.xl,
  },
  inputLabel: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  input: {
    ...COMPONENT_STYLES.input,
    fontSize: 18,
    paddingVertical: SHOOTRZ_THEME.spacing.md,
  },
  inputError: {
    borderColor: SHOOTRZ_THEME.colors.error,
    borderWidth: 2,
  },
  errorText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.error,
    marginTop: SHOOTRZ_THEME.spacing.xs,
  },
  hintText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.textMuted,
    marginTop: SHOOTRZ_THEME.spacing.xs,
  },
  continueButton: {
    ...COMPONENT_STYLES.button.primary,
    paddingVertical: SHOOTRZ_THEME.spacing.md,
  },
  continueButtonDisabled: {
    opacity: 0.5,
  },
  continueButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    textAlign: 'center',
  },
});

