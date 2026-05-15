import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing } from '../constants/theme'
import { PrimaryButton } from './PrimaryButton'

interface ErrorStateProps {
	message: string
	onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
	return (
		<View style={styles.container}>
			<Ionicons name="alert-circle" size={64} color={colors.error} />
			<Text style={styles.title}>Something went wrong</Text>
			<Text style={styles.message}>{message}</Text>
			{onRetry ? (
				<PrimaryButton
					label="Try Again"
					onPress={onRetry}
					variant="orange"
					size="md"
					style={styles.button}
				/>
			) : null}
		</View>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		alignItems: 'center',
		justifyContent: 'center',
		padding: spacing[8],
	},
	title: {
		fontSize: typography.size.lg,
		fontWeight: typography.weight.semibold,
		color: colors.text.primary,
		marginTop: spacing[4],
	},
	message: {
		fontSize: typography.size.base,
		color: colors.text.secondary,
		textAlign: 'center',
		marginTop: spacing[2],
		maxWidth: 280,
	},
	button: {
		marginTop: spacing[6],
	},
})
