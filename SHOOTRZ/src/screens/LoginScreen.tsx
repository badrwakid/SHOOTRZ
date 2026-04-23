import React, { useState, useRef, useEffect } from 'react'
import {
	View,
	Text,
	StyleSheet,
	TextInput,
	TouchableOpacity,
	Alert,
	KeyboardAvoidingView,
	Platform,
	ScrollView,
	Animated,
	Modal,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius, glass, animation } from '../constants/theme'
import { semanticTokens } from '../theme/tokens'
import { PrimaryButton } from '../components/PrimaryButton'
import { ShootrzLogo } from '../components/ShootrzLogo'
import { GoogleLogo } from '../components/GoogleLogo'
import { AppleLogo } from '../components/AppleLogo'
import { useAuth } from '../context/AuthContext'
import { hapticFeedback } from '../utils/hapticFeedback'

interface LoginScreenProps {
	onLogin: () => void
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLogin }) => {
	const {
		login,
		signup,
		resetPassword,
		signInWithApple,
		signInWithGoogle,
		setUser,
		setIsNewUser,
		isAuthenticated,
		setNavigationCallback,
	} = useAuth()
	const [emailOrUsername, setEmailOrUsername] = useState('')
	const [email, setEmail] = useState('')
	const [username, setUsername] = useState('')
	const [password, setPassword] = useState('')
	const [name, setName] = useState('')
	const [isSignUp, setIsSignUp] = useState(false)
	const [loading, setLoading] = useState(false)
	const navigationAttemptedRef = useRef(false)
	const [emailOrUsernameError, setEmailOrUsernameError] = useState('')
	const [emailError, setEmailError] = useState('')
	const [usernameError, setUsernameError] = useState('')
	const [passwordError, setPasswordError] = useState('')
	const [nameError, setNameError] = useState('')
	const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false)
	const [resetEmail, setResetEmail] = useState('')
	const [resetEmailError, setResetEmailError] = useState('')
	const [resetEmailSent, setResetEmailSent] = useState(false)
	const [inputFocus, setInputFocus] = useState<string | null>(null)

	const canSubmitSignIn =
		!!emailOrUsername.trim() && password.length > 0
	const canSubmitSignUp =
		!!name.trim() &&
		!!username.trim() &&
		!!email.trim() &&
		password.length > 0
	const canSubmit = isSignUp ? canSubmitSignUp : canSubmitSignIn

	useEffect(() => {
		const handleNavigation = () => {
			if (!navigationAttemptedRef.current && isAuthenticated) {
				navigationAttemptedRef.current = true
				setLoading(false)
				onLogin()
			}
		}
		setNavigationCallback(handleNavigation)
		return () => {
			setNavigationCallback(null)
			navigationAttemptedRef.current = false
		}
	}, [isAuthenticated, onLogin, setNavigationCallback])

	useEffect(() => {
		if (isAuthenticated && !navigationAttemptedRef.current) {
			navigationAttemptedRef.current = true
			setLoading(false)
			onLogin()
		}
	}, [isAuthenticated, onLogin])

	const fadeAnim = useRef(new Animated.Value(0)).current
	const slideAnim = useRef(new Animated.Value(50)).current
	const logoScaleAnim = useRef(new Animated.Value(0.85)).current
	const shakeAnim = useRef(new Animated.Value(0)).current

	useEffect(() => {
		Animated.parallel([
			Animated.timing(fadeAnim, {
				toValue: 1,
				duration: 600,
				useNativeDriver: true,
			}),
			Animated.timing(slideAnim, {
				toValue: 0,
				duration: 600,
				useNativeDriver: true,
			}),
			Animated.spring(logoScaleAnim, {
				toValue: 1,
				damping: animation.easing.spring.damping,
				stiffness: animation.easing.spring.stiffness,
				useNativeDriver: true,
			}),
		]).start()
	}, [])

	useEffect(() => {
		Animated.sequence([
			Animated.timing(fadeAnim, {
				toValue: 0.7,
				duration: 150,
				useNativeDriver: true,
			}),
			Animated.timing(fadeAnim, {
				toValue: 1,
				duration: 250,
				useNativeDriver: true,
			}),
		]).start()
	}, [isSignUp])

	const triggerShake = () => {
		hapticFeedback.warning()
		Animated.sequence([
			Animated.timing(shakeAnim, { toValue: 10, duration: 50, useNativeDriver: true }),
			Animated.timing(shakeAnim, { toValue: -10, duration: 50, useNativeDriver: true }),
			Animated.timing(shakeAnim, { toValue: 6, duration: 50, useNativeDriver: true }),
			Animated.timing(shakeAnim, { toValue: -6, duration: 50, useNativeDriver: true }),
			Animated.timing(shakeAnim, { toValue: 0, duration: 50, useNativeDriver: true }),
		]).start()
	}

	const validateEmail = (val: string): boolean => {
		const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
		if (!val) { setEmailError('Email is required'); return false }
		if (!emailRegex.test(val)) { setEmailError('Invalid email format'); return false }
		setEmailError('')
		return true
	}
	const validatePassword = (val: string): boolean => {
		if (!val) { setPasswordError('Password is required'); return false }
		if (val.length < 6) { setPasswordError('Password must be at least 6 characters'); return false }
		setPasswordError('')
		return true
	}
	const validateName = (val: string): boolean => {
		if (isSignUp && !val) { setNameError('Name is required'); return false }
		setNameError('')
		return true
	}
	const validateUsername = (val: string): boolean => {
		if (isSignUp) {
			if (!val) { setUsernameError('Username is required'); return false }
			if (val.length < 3) { setUsernameError('Username must be at least 3 characters'); return false }
			if (!/^[a-zA-Z0-9_]+$/.test(val)) { setUsernameError('Only letters, numbers, and underscores allowed'); return false }
		}
		setUsernameError('')
		return true
	}
	const validateEmailOrUsername = (val: string): boolean => {
		if (!val) { setEmailOrUsernameError('Email is required'); return false }
		setEmailOrUsernameError('')
		return true
	}

	const handleLogin = async () => {
		if (!validateEmailOrUsername(emailOrUsername) || !validatePassword(password)) {
			triggerShake()
			return
		}
		setLoading(true)
		hapticFeedback.medium()
		const result = await login(emailOrUsername, password)
		setLoading(false)
		if (result.success) {
			hapticFeedback.success()
			onLogin()
		} else {
			triggerShake()
			Alert.alert('Login Failed', result.error || 'Please try again')
		}
	}

	const handleSignUp = async () => {
		if (
			!validateEmail(email) ||
			!validateUsername(username) ||
			!validatePassword(password) ||
			!validateName(name)
		) {
			triggerShake()
			return
		}
		setLoading(true)
		hapticFeedback.medium()
		const result = await signup(email, password, name, username)
		setLoading(false)
		if (result.success) {
			if (result.requiresEmailConfirmation) {
				Alert.alert(
					'Check Your Email',
					'We\'ve sent a confirmation email to ' + email + '. Please click the link to verify your account, then sign in.',
					[{ text: 'OK', onPress: () => setIsSignUp(false) }],
				)
			} else {
				hapticFeedback.success()
				onLogin()
			}
		} else {
			triggerShake()
			Alert.alert('Signup Failed', result.error || 'Please try again')
		}
	}

	const handleGoogleSignIn = async () => {
		try {
			setLoading(true)
			navigationAttemptedRef.current = false
			const result = await signInWithGoogle()
			if (!result.success) {
				Alert.alert('Google Sign-In Failed', result.error || 'Please try again')
				setLoading(false)
			}
		} catch (error: any) {
			Alert.alert('Google Sign-In Failed', error.message || 'Please try again')
			setLoading(false)
		}
	}

	const handleAppleSignIn = async () => {
		setLoading(true)
		const result = await signInWithApple()
		setLoading(false)
		if (result.success) {
			onLogin()
		} else {
			Alert.alert('Apple Sign-In Failed', result.error || 'Please try again')
		}
	}

	const handleForgotPassword = () => {
		setResetEmail(emailOrUsername || '')
		setResetEmailError('')
		setResetEmailSent(false)
		setShowForgotPasswordModal(true)
	}

	const handleSendResetEmail = async () => {
		if (!resetEmail) { setResetEmailError('Email is required'); return }
		if (!resetEmail.includes('@')) { setResetEmailError('Please enter a valid email address'); return }
		setLoading(true)
		setResetEmailError('')
		const result = await resetPassword(resetEmail)
		setLoading(false)
		if (result.success) { setResetEmailSent(true) }
		else { setResetEmailError(result.error || 'Failed to send reset email') }
	}

	const closeForgotPasswordModal = () => {
		setShowForgotPasswordModal(false)
		setResetEmail('')
		setResetEmailError('')
		setResetEmailSent(false)
	}

	const toggleMode = () => {
		hapticFeedback.selection()
		setIsSignUp(!isSignUp)
		setEmailOrUsernameError('')
		setEmailError('')
		setUsernameError('')
		setPasswordError('')
		setNameError('')
	}

	const renderInput = (
		label: string,
		value: string,
		onChange: (t: string) => void,
		error: string,
		opts: { placeholder: string; secure?: boolean; autoCapitalize?: 'none' | 'words'; keyboardType?: 'email-address' | 'default' },
		fieldId: string,
	) => (
		<View style={styles.inputWrap}>
			<Text style={styles.inputLabel}>{label}</Text>
			<TextInput
				style={[
					styles.input,
					error ? styles.inputError : null,
					!error && inputFocus === fieldId ? styles.inputFocus : null,
				]}
				placeholder={opts.placeholder}
				placeholderTextColor={colors.text.tertiary}
				value={value}
				onChangeText={onChange}
				secureTextEntry={opts.secure}
				autoCapitalize={opts.autoCapitalize ?? 'none'}
				autoCorrect={false}
				keyboardType={opts.keyboardType ?? 'default'}
				editable={!loading}
				onFocus={() => setInputFocus(fieldId)}
				onBlur={() => {
					setInputFocus(f => (f === fieldId ? null : f))
				}}
			/>
			{error ? (
				<View style={styles.errorRow}>
					<Ionicons name="alert-circle" size={12} color={colors.error} />
					<Text style={styles.errorText}>{error}</Text>
				</View>
			) : null}
		</View>
	)

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
			<KeyboardAvoidingView
				style={styles.flex}
				behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
			>
				<ScrollView
					style={styles.flex}
					contentContainerStyle={styles.scrollContent}
					showsVerticalScrollIndicator={false}
					keyboardShouldPersistTaps="handled"
				>
					<Animated.View
						style={[
							styles.logoSection,
							{
								opacity: fadeAnim,
								transform: [{ scale: logoScaleAnim }],
							},
						]}
					>
						<ShootrzLogo size="large" showTagline={false} />
						<Text style={styles.tagline}>PERFECT THE GAME</Text>
					</Animated.View>

					<Animated.View
						style={[
							styles.formCard,
							{
								opacity: fadeAnim,
								transform: [
									{ translateY: slideAnim },
									{ translateX: shakeAnim },
								],
							},
						]}
					>
						<Text style={styles.formTitle}>
							{isSignUp ? 'Create Account' : 'Welcome Back'}
						</Text>
						<Text style={styles.formSubtitle}>
							{isSignUp ? 'Start your basketball journey' : 'Sign in to continue training'}
						</Text>

						{isSignUp ? (
							<>
								{renderInput('Full Name', name, t => { setName(t); setNameError('') }, nameError, { placeholder: 'Your name', autoCapitalize: 'words' }, 'name')}
								{renderInput('Username', username, t => { setUsername(t.toLowerCase()); setUsernameError('') }, usernameError, { placeholder: 'Choose a username' }, 'username')}
								{renderInput('Email', email, t => { setEmail(t); setEmailError('') }, emailError, { placeholder: 'you@example.com', keyboardType: 'email-address' }, 'signupEmail')}
							</>
						) : (
							renderInput('Email', emailOrUsername, t => { setEmailOrUsername(t); setEmailOrUsernameError('') }, emailOrUsernameError, { placeholder: 'you@example.com', keyboardType: 'email-address' }, 'emailOrUsername')
						)}

						{renderInput('Password', password, t => { setPassword(t); setPasswordError('') }, passwordError, { placeholder: 'Min 6 characters', secure: true }, 'password')}

						{!isSignUp ? (
							<TouchableOpacity onPress={handleForgotPassword} style={styles.forgotBtn}>
								<Text style={styles.forgotText}>Forgot Password?</Text>
							</TouchableOpacity>
						) : null}

						<PrimaryButton
							label={isSignUp ? 'Create Account' : 'Sign In'}
							onPress={isSignUp ? handleSignUp : handleLogin}
							loading={loading}
							disabled={!canSubmit}
							fullWidth
							size="lg"
							variant="orange"
							style={{ marginBottom: spacing[3] }}
						/>

						<TouchableOpacity onPress={toggleMode} style={styles.switchBtn}>
							<Text style={styles.switchText}>
								{isSignUp ? 'Already have an account? ' : "Don't have an account? "}
								<Text style={styles.switchHighlight}>
									{isSignUp ? 'Sign In' : 'Sign Up'}
								</Text>
							</Text>
						</TouchableOpacity>
					</Animated.View>

					{!isSignUp ? (
						<Animated.View style={[styles.socialSection, { opacity: fadeAnim }]}>
							<View style={styles.divider}>
								<View style={styles.dividerLine} />
								<Text style={styles.dividerText}>OR</Text>
								<View style={styles.dividerLine} />
							</View>
							<TouchableOpacity
								style={styles.googleBtn}
								onPress={handleGoogleSignIn}
								disabled={loading}
								activeOpacity={0.85}
							>
								<GoogleLogo size={20} />
								<Text style={styles.googleText}>Sign in with Google</Text>
							</TouchableOpacity>
							<TouchableOpacity
								style={styles.appleBtn}
								onPress={handleAppleSignIn}
								disabled={loading}
								activeOpacity={0.85}
							>
								<AppleLogo size={20} />
								<Text style={styles.appleText}>Sign in with Apple</Text>
							</TouchableOpacity>
						</Animated.View>
					) : null}
				</ScrollView>
			</KeyboardAvoidingView>

			<Modal
				visible={showForgotPasswordModal}
				animationType="slide"
				transparent
				onRequestClose={closeForgotPasswordModal}
			>
				<View style={styles.modalOverlay}>
					<View style={styles.modalCard}>
						{!resetEmailSent ? (
							<>
								<Text style={styles.modalTitle}>Reset Password</Text>
								<Text style={styles.modalDesc}>
									{"Enter your email and we'll send reset instructions."}
								</Text>
								<View style={styles.inputWrap}>
									<Text style={styles.inputLabel}>Email Address</Text>
									<TextInput
										style={[
											styles.input,
											resetEmailError && styles.inputError,
											!resetEmailError && inputFocus === 'resetEmail' && styles.inputFocus,
										]}
										placeholder="you@example.com"
										placeholderTextColor={colors.text.tertiary}
										value={resetEmail}
										onChangeText={t => { setResetEmail(t); setResetEmailError('') }}
										keyboardType="email-address"
										autoCapitalize="none"
										autoFocus
										editable={!loading}
										onFocus={() => setInputFocus('resetEmail')}
										onBlur={() => setInputFocus(f => (f === 'resetEmail' ? null : f))}
									/>
									{resetEmailError ? (
										<View style={styles.errorRow}>
											<Ionicons name="alert-circle" size={12} color={colors.error} />
											<Text style={styles.errorText}>{resetEmailError}</Text>
										</View>
									) : null}
								</View>
								<PrimaryButton
									label="Send Reset Link"
									onPress={handleSendResetEmail}
									loading={loading}
									disabled={!resetEmail.trim()}
									fullWidth
									size="lg"
									variant="orange"
									style={{ marginBottom: spacing[3] }}
								/>
								<TouchableOpacity onPress={closeForgotPasswordModal} style={styles.switchBtn}>
									<Text style={styles.forgotText}>Cancel</Text>
								</TouchableOpacity>
							</>
						) : (
							<>
								<View style={styles.successIcon}>
									<Ionicons name="checkmark-circle" size={48} color={colors.success} />
								</View>
								<Text style={styles.modalTitle}>Check Your Email</Text>
								<Text style={styles.modalDesc}>
									Reset instructions sent to:
								</Text>
								<Text style={styles.resetEmailHighlight}>{resetEmail}</Text>
								<Text style={styles.modalDescDim}>
									{
										"The link expires in 1 hour. Check your spam folder if you don't see it."
									}
								</Text>
								<PrimaryButton
									label="Done"
									onPress={closeForgotPasswordModal}
									fullWidth
									size="lg"
									variant="cyan"
									style={{ marginBottom: spacing[3] }}
								/>
								<TouchableOpacity
									onPress={() => { setResetEmailSent(false); setResetEmailError('') }}
									style={styles.switchBtn}
								>
									<Text style={styles.forgotText}>Send Again</Text>
								</TouchableOpacity>
							</>
						)}
					</View>
				</View>
			</Modal>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: colors.bg.primary,
	},
	flex: {
		flex: 1,
	},
	scrollContent: {
		flexGrow: 1,
		justifyContent: 'center',
		paddingHorizontal: spacing[5],
		paddingVertical: spacing[8],
	},
	logoSection: {
		alignItems: 'center',
		marginBottom: spacing[10],
	},
	tagline: {
		fontSize: typography.size.xs,
		fontWeight: typography.weight.medium,
		color: colors.brand.cyan,
		letterSpacing: typography.tracking.widest,
		marginTop: spacing[3],
	},
	formCard: {
		backgroundColor: glass.card.bg,
		borderWidth: 1,
		borderColor: glass.card.border,
		borderRadius: radius['2xl'],
		padding: spacing[6],
	},
	formTitle: {
		fontSize: typography.size.xl,
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
		textAlign: 'center',
		marginBottom: spacing[1],
	},
	formSubtitle: {
		fontSize: typography.size.sm,
		color: colors.text.secondary,
		textAlign: 'center',
		marginBottom: spacing[6],
	},
	inputWrap: {
		marginBottom: spacing[4],
	},
	inputLabel: {
		fontSize: typography.size.sm,
		fontWeight: typography.weight.semibold,
		color: colors.text.secondary,
		marginBottom: spacing[1],
	},
	input: {
		backgroundColor: colors.bg.elevated,
		borderWidth: 1,
		borderColor: colors.border.default,
		borderRadius: radius.md,
		paddingHorizontal: spacing[4],
		paddingVertical: spacing[3],
		fontSize: typography.size.base,
		color: colors.text.primary,
		minHeight: 52,
	},
	inputError: {
		borderColor: colors.error,
	},
	inputFocus: {
		borderColor: semanticTokens.focus.ring,
		borderWidth: 1,
	},
	errorRow: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[1],
		marginTop: spacing[1],
	},
	errorText: {
		fontSize: typography.size.xs,
		color: colors.error,
	},
	forgotBtn: {
		alignSelf: 'flex-end',
		marginBottom: spacing[4],
	},
	forgotText: {
		fontSize: typography.size.sm,
		color: colors.brand.cyan,
	},
	switchBtn: {
		alignItems: 'center',
		paddingVertical: spacing[2],
	},
	switchText: {
		fontSize: typography.size.sm,
		color: colors.text.secondary,
	},
	switchHighlight: {
		color: colors.brand.cyan,
		fontWeight: typography.weight.semibold,
	},
	socialSection: {
		marginTop: spacing[6],
	},
	divider: {
		flexDirection: 'row',
		alignItems: 'center',
		marginBottom: spacing[5],
	},
	dividerLine: {
		flex: 1,
		height: 1,
		backgroundColor: colors.border.default,
	},
	dividerText: {
		fontSize: typography.size.xs,
		color: colors.text.tertiary,
		marginHorizontal: spacing[4],
	},
	googleBtn: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		gap: spacing[2],
		height: 52,
		borderRadius: radius.button,
		backgroundColor: semanticTokens.oauth.google.surface,
		marginBottom: spacing[3],
	},
	googleText: {
		fontSize: typography.size.base,
		fontWeight: typography.weight.semibold,
		color: semanticTokens.oauth.google.label,
	},
	appleBtn: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		gap: spacing[2],
		height: 52,
		borderRadius: radius.button,
		backgroundColor: semanticTokens.oauth.apple.surface,
		borderWidth: 1,
		borderColor: colors.border.default,
	},
	appleText: {
		fontSize: typography.size.base,
		fontWeight: typography.weight.semibold,
		color: semanticTokens.oauth.apple.label,
	},
	modalOverlay: {
		flex: 1,
		backgroundColor: 'rgba(8, 10, 14, 0.85)',
		justifyContent: 'center',
		padding: spacing[5],
	},
	modalCard: {
		backgroundColor: colors.bg.elevated,
		borderRadius: radius['2xl'],
		padding: spacing[6],
		borderWidth: 1,
		borderColor: colors.border.default,
	},
	modalTitle: {
		fontSize: typography.size.xl,
		fontWeight: typography.weight.bold,
		color: colors.text.primary,
		textAlign: 'center',
		marginBottom: spacing[2],
	},
	modalDesc: {
		fontSize: typography.size.base,
		color: colors.text.secondary,
		textAlign: 'center',
		marginBottom: spacing[5],
		lineHeight: typography.size.base * typography.lineHeight.normal,
	},
	modalDescDim: {
		fontSize: typography.size.sm,
		color: colors.text.tertiary,
		textAlign: 'center',
		marginBottom: spacing[4],
		lineHeight: typography.size.sm * typography.lineHeight.normal,
	},
	successIcon: {
		alignSelf: 'center',
		marginBottom: spacing[4],
	},
	resetEmailHighlight: {
		fontSize: typography.size.base,
		fontWeight: typography.weight.semibold,
		color: colors.brand.orange,
		textAlign: 'center',
		marginBottom: spacing[4],
	},
})
