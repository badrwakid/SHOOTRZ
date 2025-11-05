import React, { Component, ErrorInfo, ReactNode } from 'react'
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { SHOOTRZ_THEME } from '../constants/theme'

interface Props {
	children: ReactNode
	fallback?: ReactNode
}

interface State {
	hasError: boolean
	error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
	constructor(props: Props) {
		super(props)
		this.state = { hasError: false, error: null }
	}

	static getDerivedStateFromError(error: Error): State {
		return { hasError: true, error }
	}

	componentDidCatch(error: Error, errorInfo: ErrorInfo) {
		console.error('ErrorBoundary caught error:', error, errorInfo)
		// TODO: Log to error tracking service (Sentry, etc.)
	}

	handleReset = () => {
		this.setState({ hasError: false, error: null })
	}

	render() {
		if (this.state.hasError) {
			if (this.props.fallback) {
				return this.props.fallback
			}

			return (
				<View style={styles.container}>
					<Ionicons name="alert-circle" size={64} color={SHOOTRZ_THEME.colors.error} />
					<Text style={styles.title}>Something went wrong</Text>
					<Text style={styles.message}>
						{this.state.error?.message || 'An unexpected error occurred'}
					</Text>
					<TouchableOpacity style={styles.button} onPress={this.handleReset}>
						<Text style={styles.buttonText}>Try Again</Text>
					</TouchableOpacity>
				</View>
			)
		}

		return this.props.children
	}
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		alignItems: 'center',
		justifyContent: 'center',
		padding: 20,
		backgroundColor: SHOOTRZ_THEME.colors.background,
	},
	title: {
		fontSize: 24,
		fontWeight: 'bold',
		color: SHOOTRZ_THEME.colors.text,
		marginTop: 16,
		marginBottom: 8,
	},
	message: {
		fontSize: 16,
		color: SHOOTRZ_THEME.colors.textSecondary,
		textAlign: 'center',
		marginBottom: 24,
	},
	button: {
		backgroundColor: SHOOTRZ_THEME.colors.primary,
		paddingHorizontal: 24,
		paddingVertical: 12,
		borderRadius: 8,
	},
	buttonText: {
		color: '#fff',
		fontSize: 16,
		fontWeight: '600',
	},
})



