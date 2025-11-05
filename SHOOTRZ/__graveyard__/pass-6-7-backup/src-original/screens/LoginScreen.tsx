import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, KeyboardAvoidingView, Platform, ActivityIndicator, ScrollView, Animated, Modal } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { ShootrzLogo } from '../components/ShootrzLogo';
import { GoogleLogo } from '../components/GoogleLogo';
import { AppleLogo } from '../components/AppleLogo';
import { useAuth } from '../context/AuthContext';
import { useGoogleAuth } from '../hooks/useGoogleAuth';
import { socialAuthService } from '../services/socialAuth.service';

interface LoginScreenProps {
  onLogin: () => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLogin }) => {
  const { login, signup, resetPassword, signInWithApple, setUser, setIsNewUser } = useAuth();
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [emailOrUsernameError, setEmailOrUsernameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [nameError, setNameError] = useState('');
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetEmailError, setResetEmailError] = useState('');
  const [resetEmailSent, setResetEmailSent] = useState(false);
  
  // Google Auth hook
  const { request: googleRequest, response: googleResponse, promptAsync: promptGoogleAsync } = useGoogleAuth();
  
  // Animation refs
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const logoScaleAnim = useRef(new Animated.Value(0.8)).current;

  // Animation effects
  useEffect(() => {
    const startAnimations = () => {
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.spring(logoScaleAnim, {
          toValue: 1,
          tension: 100,
          friction: 8,
          useNativeDriver: true,
        }),
      ]).start();
    };

    startAnimations();
  }, []);

  // Animate form transition when switching between login/signup
  useEffect(() => {
    Animated.sequence([
      Animated.timing(fadeAnim, {
        toValue: 0.7,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  }, [isSignUp]);

  // Handle Google Sign-In response
  useEffect(() => {
    const handleGoogleResponse = async () => {
      if (googleResponse?.type === 'success') {
        const { authentication } = googleResponse;
        
        if (authentication?.idToken) {
          setLoading(true);
          
          const result = await socialAuthService.processGoogleSignIn(
            authentication.idToken,
            authentication.accessToken, // displayName (if available)
            null // email (will be fetched from Firebase)
          );
          
          setLoading(false);
          
          if (result.success && result.user) {
            setUser(result.user);
            setIsNewUser(result.isNewUser || false);
            onLogin();
          } else {
            Alert.alert('Sign-in failed', result.error || 'Unknown error occurred');
          }
        }
      }
    };
    
    handleGoogleResponse();
  }, [googleResponse]);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) {
      setEmailError('Email is required');
      return false;
    }
    if (!emailRegex.test(email)) {
      setEmailError('Invalid email format');
      return false;
    }
    setEmailError('');
    return true;
  };

  const validatePassword = (password: string): boolean => {
    if (!password) {
      setPasswordError('Password is required');
      return false;
    }
    if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      return false;
    }
    setPasswordError('');
    return true;
  };

  const validateName = (name: string): boolean => {
    if (isSignUp && !name) {
      setNameError('Name is required');
      return false;
    }
    setNameError('');
    return true;
  };

  const validateUsername = (username: string): boolean => {
    if (isSignUp) {
      if (!username) {
        setUsernameError('Username is required');
        return false;
      }
      if (username.length < 3) {
        setUsernameError('Username must be at least 3 characters');
        return false;
      }
      if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        setUsernameError('Only letters, numbers, and underscores allowed');
        return false;
      }
    }
    setUsernameError('');
    return true;
  };

  const validateEmailOrUsername = (value: string): boolean => {
    if (!value) {
      setEmailOrUsernameError('Email or username is required');
      return false;
    }
    setEmailOrUsernameError('');
    return true;
  };

  const handleLogin = async () => {
    if (!validateEmailOrUsername(emailOrUsername) || !validatePassword(password)) {
      return;
    }

    setLoading(true);
    const result = await login(emailOrUsername, password);
    setLoading(false);

    if (result.success) {
      onLogin();
    } else {
      Alert.alert('Login Failed', result.error || 'Please try again');
    }
  };

  const handleSignUp = async () => {
    if (!validateEmail(email) || !validateUsername(username) || !validatePassword(password) || !validateName(name)) {
      return;
    }

    setLoading(true);
    const result = await signup(email, password, name, username);
    setLoading(false);

    if (result.success) {
      // New signup - will trigger onboarding in App.tsx
      onLogin();
    } else {
      Alert.alert('Signup Failed', result.error || 'Please try again');
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      if (!googleRequest) {
        Alert.alert('Error', 'Google Sign-In is not ready. Please try again.');
        return;
      }
      
      // Trigger the Google Sign-In flow
      await promptGoogleAsync();
      // The response will be handled by the useEffect above
    } catch (error: any) {
      console.error('Google Sign-In error:', error);
      Alert.alert('Google Sign-In Failed', error.message || 'Please try again');
    }
  };

  const handleAppleSignIn = async () => {
    setLoading(true);
    const result = await signInWithApple();
    setLoading(false);

    if (result.success) {
      onLogin();
    } else {
      Alert.alert('Apple Sign-In Failed', result.error || 'Please try again');
    }
  };

  const handleForgotPassword = () => {
    setResetEmail(emailOrUsername || '');
    setResetEmailError('');
    setResetEmailSent(false);
    setShowForgotPasswordModal(true);
  };

  const handleSendResetEmail = async () => {
    // Validate email
    if (!resetEmail) {
      setResetEmailError('Email is required');
      return;
    }

    if (!resetEmail.includes('@')) {
      setResetEmailError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setResetEmailError('');
    
    const result = await resetPassword(resetEmail);
    setLoading(false);

    if (result.success) {
      setResetEmailSent(true);
    } else {
      setResetEmailError(result.error || 'Failed to send reset email');
    }
  };

  const closeForgotPasswordModal = () => {
    setShowForgotPasswordModal(false);
    setResetEmail('');
    setResetEmailError('');
    setResetEmailSent(false);
  };

  const toggleMode = () => {
    setIsSignUp(!isSignUp);
    setEmailOrUsernameError('');
    setEmailError('');
    setUsernameError('');
    setPasswordError('');
    setNameError('');
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
      <KeyboardAvoidingView 
        style={styles.keyboardAvoidingView} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <Animated.View 
          style={[
            styles.content,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
        {/* Logo Section */}
        <Animated.View 
          style={[
            styles.logoSection,
            {
              transform: [{ scale: logoScaleAnim }],
            },
          ]}
        >
          <View style={styles.logoContainer}>
            <ShootrzLogo size="large" showTagline={false} />
          </View>
        </Animated.View>

        {/* Form Section */}
        <View style={styles.formSection}>
          <Text style={styles.formTitle}>
            {isSignUp ? 'Create Account' : 'Welcome Back'}
          </Text>
          <Text style={styles.formSubtitle}>
            {isSignUp ? 'Start your basketball journey' : 'Sign in to continue training'}
          </Text>

          {isSignUp && (
            <>
              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Full Name</Text>
                <TextInput
                  style={[styles.input, nameError && styles.inputError]}
                  placeholder="Enter your full name"
                  placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                  value={name}
                  onChangeText={(text) => {
                    setName(text);
                    setNameError('');
                  }}
                  autoCapitalize="words"
                  autoCorrect={false}
                />
                {nameError ? <Text style={styles.errorText}>{nameError}</Text> : null}
              </View>

              <View style={styles.inputContainer}>
                <Text style={styles.inputLabel}>Username</Text>
                <TextInput
                  style={[styles.input, usernameError && styles.inputError]}
                  placeholder="Choose a unique username"
                  placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                  value={username}
                  onChangeText={(text) => {
                    setUsername(text.toLowerCase());
                    setUsernameError('');
                  }}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
                {usernameError ? <Text style={styles.errorText}>{usernameError}</Text> : null}
              </View>
            </>
          )}

          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>{isSignUp ? 'Email' : 'Email or Username'}</Text>
            <TextInput
              style={[styles.input, (isSignUp ? emailError : emailOrUsernameError) && styles.inputError]}
              placeholder={isSignUp ? 'Enter your email' : 'Enter email or username'}
              placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
              value={isSignUp ? email : emailOrUsername}
              onChangeText={(text) => {
                if (isSignUp) {
                  setEmail(text);
                  setEmailError('');
                } else {
                  setEmailOrUsername(text);
                  setEmailOrUsernameError('');
                }
              }}
              keyboardType={isSignUp ? 'email-address' : 'default'}
              autoCapitalize="none"
              autoCorrect={false}
            />
            {isSignUp 
              ? (emailError ? <Text style={styles.errorText}>{emailError}</Text> : null)
              : (emailOrUsernameError ? <Text style={styles.errorText}>{emailOrUsernameError}</Text> : null)
            }
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Password</Text>
            <TextInput
              style={[styles.input, passwordError && styles.inputError]}
              placeholder="Enter your password"
              placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
              value={password}
              onChangeText={(text) => {
                setPassword(text);
                setPasswordError('');
              }}
              secureTextEntry
              autoCapitalize="none"
              autoCorrect={false}
            />
            {passwordError ? <Text style={styles.errorText}>{passwordError}</Text> : null}
          </View>

          {!isSignUp && (
            <TouchableOpacity style={styles.forgotButton} onPress={handleForgotPassword}>
              <Text style={styles.forgotButtonText}>Forgot Password?</Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={[styles.submitButton, loading && styles.submitButtonDisabled]}
            onPress={isSignUp ? handleSignUp : handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color={SHOOTRZ_THEME.colors.textPrimary} />
            ) : (
              <Text style={styles.submitButtonText}>
                {isSignUp ? 'Create Account' : 'Sign In'}
              </Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.switchButton}
            onPress={toggleMode}
          >
            <Text style={styles.switchButtonText}>
              {isSignUp 
                ? 'Already have an account? Sign In' 
                : "Don't have an account? Sign Up"
              }
            </Text>
          </TouchableOpacity>
        </View>

        {/* Social Login */}
        {!isSignUp && (
          <>
            <View style={styles.orDivider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>OR</Text>
              <View style={styles.dividerLine} />
            </View>

            <View style={styles.socialButtonsContainer}>
              <TouchableOpacity 
                style={styles.googleButton} 
                onPress={handleGoogleSignIn}
                disabled={loading}
              >
                <GoogleLogo size={20} />
                <Text style={[styles.socialButtonText, { color: '#1F1F1F' }]}>Sign in with Google</Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={styles.appleButton} 
                onPress={handleAppleSignIn}
                disabled={loading}
              >
                <AppleLogo size={20} color="#FFFFFF" />
                <Text style={[styles.socialButtonText, { color: '#FFFFFF' }]}>Sign in with Apple</Text>
              </TouchableOpacity>
            </View>
          </>
        )}

        </Animated.View>
      </ScrollView>
      </KeyboardAvoidingView>

      {/* Forgot Password Modal */}
      <Modal
        visible={showForgotPasswordModal}
        animationType="slide"
        transparent={true}
        onRequestClose={closeForgotPasswordModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {!resetEmailSent ? (
              <>
                <Text style={styles.modalTitle}>Reset Password</Text>
                <Text style={styles.modalDescription}>
                  Enter your email address and we'll send you instructions to reset your password.
                </Text>
                
                <View style={styles.modalInputContainer}>
                  <Text style={styles.modalInputLabel}>Email Address</Text>
                  <TextInput
                    style={[styles.modalInput, resetEmailError && styles.modalInputError]}
                    placeholder="Enter your email"
                    placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
                    value={resetEmail}
                    onChangeText={(text) => {
                      setResetEmail(text);
                      setResetEmailError('');
                    }}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoCorrect={false}
                    autoFocus={true}
                  />
                  {resetEmailError ? (
                    <Text style={styles.modalErrorText}>{resetEmailError}</Text>
                  ) : null}
                </View>

                <TouchableOpacity
                  style={[styles.modalButton, loading && styles.modalButtonDisabled]}
                  onPress={handleSendResetEmail}
                  disabled={loading}
                >
                  {loading ? (
                    <ActivityIndicator color={SHOOTRZ_THEME.colors.textPrimary} />
                  ) : (
                    <Text style={styles.modalButtonText}>Send Reset Link</Text>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.modalCancelButton}
                  onPress={closeForgotPasswordModal}
                  disabled={loading}
                >
                  <Text style={styles.modalCancelButtonText}>Cancel</Text>
                </TouchableOpacity>
              </>
            ) : (
              <>
                <View style={styles.successIconContainer}>
                  <Text style={styles.successIcon}>✓</Text>
                </View>
                <Text style={styles.modalTitle}>Check Your Email</Text>
                <Text style={styles.modalDescription}>
                  We've sent password reset instructions to:
                </Text>
                <Text style={styles.resetEmailText}>{resetEmail}</Text>
                <Text style={styles.modalDescriptionSecondary}>
                  Click the link in the email to create a new password. The link will expire in 1 hour.
                </Text>
                <Text style={styles.modalDescriptionSecondary}>
                  Didn't receive the email? Check your spam folder or try again.
                </Text>

                <TouchableOpacity
                  style={styles.modalButton}
                  onPress={closeForgotPasswordModal}
                >
                  <Text style={styles.modalButtonText}>Done</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.modalCancelButton}
                  onPress={() => {
                    setResetEmailSent(false);
                    setResetEmailError('');
                  }}
                >
                  <Text style={styles.modalCancelButtonText}>Send Again</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    padding: SHOOTRZ_THEME.spacing.lg,
    minHeight: '100%',
    justifyContent: 'center',
  },
  logoSection: {
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xxl,
    width: '100%',
  },
  logoContainer: {
    width: '100%',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  formSection: {
    marginBottom: SHOOTRZ_THEME.spacing.xxl,
  },
  formTitle: {
    ...SHOOTRZ_THEME.typography.heading2,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  formSubtitle: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xl,
  },
  inputContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  inputLabel: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    fontWeight: '600',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  input: {
    ...COMPONENT_STYLES.input,
    fontSize: 16,
  },
  inputError: {
    borderColor: SHOOTRZ_THEME.colors.error,
    borderWidth: 1,
  },
  errorText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.error,
    marginTop: SHOOTRZ_THEME.spacing.xs,
  },
  forgotButton: {
    alignSelf: 'flex-end',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  forgotButtonText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.secondary,
  },
  submitButton: {
    ...COMPONENT_STYLES.button.primary,
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    textAlign: 'center',
  },
  switchButton: {
    alignItems: 'center',
  },
  switchButtonText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.secondary,
  },
  orDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: SHOOTRZ_THEME.spacing.lg,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  dividerText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textMuted,
    marginHorizontal: SHOOTRZ_THEME.spacing.md,
  },
  socialButtonsContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  googleButton: {
    ...COMPONENT_STYLES.button.secondary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SHOOTRZ_THEME.spacing.sm,
    marginBottom: SHOOTRZ_THEME.spacing.md,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#DADCE0',
  },
  appleButton: {
    ...COMPONENT_STYLES.button.secondary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SHOOTRZ_THEME.spacing.sm,
    backgroundColor: '#000000',
  },
  socialButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  // Forgot Password Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  modalContent: {
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
    padding: SHOOTRZ_THEME.spacing.xl,
    width: '100%',
    maxWidth: 400,
    ...SHOOTRZ_THEME.shadows.large,
  },
  modalTitle: {
    ...SHOOTRZ_THEME.typography.heading2,
    marginBottom: SHOOTRZ_THEME.spacing.md,
    textAlign: 'center',
  },
  modalDescription: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.lg,
    lineHeight: 22,
  },
  modalDescriptionSecondary: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textMuted,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
    lineHeight: 20,
  },
  modalInputContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  modalInputLabel: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    fontWeight: '600',
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  modalInput: {
    ...COMPONENT_STYLES.input,
    fontSize: 16,
  },
  modalInputError: {
    borderColor: SHOOTRZ_THEME.colors.error,
    borderWidth: 1,
  },
  modalErrorText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.error,
    marginTop: SHOOTRZ_THEME.spacing.xs,
  },
  modalButton: {
    ...COMPONENT_STYLES.button.primary,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  modalButtonDisabled: {
    opacity: 0.6,
  },
  modalButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    textAlign: 'center',
  },
  modalCancelButton: {
    padding: SHOOTRZ_THEME.spacing.md,
    alignItems: 'center',
  },
  modalCancelButtonText: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  successIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: SHOOTRZ_THEME.colors.secondary + '20',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  successIcon: {
    fontSize: 48,
    color: SHOOTRZ_THEME.colors.secondary,
    fontWeight: 'bold',
  },
  resetEmailText: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    color: SHOOTRZ_THEME.colors.primary,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
});
