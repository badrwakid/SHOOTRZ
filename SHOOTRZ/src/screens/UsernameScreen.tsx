import React, { useState } from 'react'
import {
	View,
	Text,
	StyleSheet,
	TextInput,
	KeyboardAvoidingView,
	Platform,
	Alert,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius } from '../constants/theme'
import { PrimaryButton } from '../components/PrimaryButton'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../services/supabase.client'
import { hapticFeedback } from '../utils/hapticFeedback'

interface UsernameScreenProps {
	onComplete: () => void
}

export const UsernameScreen: React.FC<UsernameScreenProps> = ({ onComplete }) => {
	const { user, updateProfile } = useAuth()
	const [username, setUsername] = useState('')
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState('')

	const validateUsername = (val: string): string | null => {
		if (!val.trim()) return 'Username is required'
		if (val.length < 3) return 'Username must be at least 3 characters'
		if (val.length > 20) return 'Username must be less than 20 characters'
		if (!/^[a-zA-Z0-9_]+$/.test(val)) return 'Only letters, numbers, and underscores'
		return null
	}

	const checkUsernameAvailability = async (val: string): Promise<boolean> => {
		try {
			const { data } = await supabase
				.from('users')
				.select('id')
				.eq('username', val.toLowerCase())
				.single()
			if (data && data.id !== user?.id) return false
			return true
		} catch {
			return true
		}
	}

	const handleSubmit = async () => {
		const validationError = validateUsername(username)
		if (validationError) {
			setError(validationError)
			hapticFeedback.warning()
			return
		}

		setLoading(true)
		setError('')

		const available = await checkUsernameAvailability(username)
		if (!available) {
			setError('This username is already taken')
			setLoading(false)
			hapticFeedback.warning()
			return
		}

		try {
			await updateProfile({ username: username.toLowerCase() })
			hapticFeedback.success()
			onComplete()
		} catch (err) {
			Alert.alert('Error', 'Failed to save username. Please try again.')
		} finally {
			setLoading(false)
		}
	}

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
			<KeyboardAvoidingView
				style={styles.flex}
				behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
			>
				<View style={styles.content}>
					<View style={styles.iconWrap}>
						<Ionicons name="person-circle" size={64} color={colors.brand.orange} />
					</View>
					<Text style={styles.title}>Choose Your Username</Text>
					<Text style={styles.subtitle}>
						This is how other players will see you.
					</Text>

					<View style={styles.inputWrap}>
						<Text style={styles.inputLabel}>Username</Text>
						<TextInput
							style={[styles.input, error ? styles.inputError : null]}
							placeholder="e.g. hoopstar23"
							placeholderTextColor={colors.text.tertiary}
							value={username}
							onChangeText={t => { setUsername(t.toLowerCase()); setError('') }}
							autoCapitalize="none"
							autoCorrect={false}
							maxLength={20}
						/>
						{error ? (
							<View style={styles.errorRow}>
								<Ionicons name="alert-circle" size={12} color={colors.error} />
								<Text style={styles.errorText}>{error}</Text>
							</View>
						) : null}
					</View>

					<PrimaryButton
						label="Continue"
						onPress={handleSubmit}
						loading={loading}
						fullWidth
						size="lg"
					/>
				</View>
			</KeyboardAvoidingView>
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
	content: {
		flex: 1,
		justifyContent: 'center',
		paddingHorizontal: spacing[6],
	},
	iconWrap: {
		alignSelf: 'center',
		marginBottom: spacing[6],
	},
	title: {
		...typography.roles.headingLg,
		color: colors.text.primary,
		textAlign: 'center',
	},
	subtitle: {
		...typography.roles.body,
		color: colors.text.secondary,
		textAlign: 'center',
		marginTop: spacing[2],
		marginBottom: spacing[8],
	},
	inputWrap: {
		marginBottom: spacing[6],
	},
	inputLabel: {
		...typography.roles.caption,
		color: colors.text.secondary,
		fontWeight: typography.weight.semibold,
		fontFamily: 'DMSansSemiBold',
		marginBottom: spacing[1],
	},
	input: {
		backgroundColor: colors.bg.elevated,
		borderWidth: 1,
		borderColor: colors.border.default,
		borderRadius: radius.md,
		paddingHorizontal: spacing[4],
		paddingVertical: spacing[3],
		...typography.roles.body,
		color: colors.text.primary,
		minHeight: 52,
	},
	inputError: {
		borderColor: colors.error,
	},
	errorRow: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[1],
		marginTop: spacing[1],
	},
	errorText: {
		...typography.roles.caption,
		color: colors.error,
	},
})
