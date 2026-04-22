import React, { useEffect, useRef } from 'react'
import { View, Text, StyleSheet, Animated, Modal } from 'react-native'
import { colors, typography, spacing } from '../constants/theme'

interface LoadingOverlayProps {
	visible: boolean
	message?: string
}

export function LoadingOverlay({ visible, message }: LoadingOverlayProps) {
	const pulse = useRef(new Animated.Value(0.6)).current

	useEffect(() => {
		if (!visible) return
		const anim = Animated.loop(
			Animated.sequence([
				Animated.timing(pulse, {
					toValue: 1,
					duration: 800,
					useNativeDriver: true,
				}),
				Animated.timing(pulse, {
					toValue: 0.6,
					duration: 800,
					useNativeDriver: true,
				}),
			]),
		)
		anim.start()
		return () => anim.stop()
	}, [visible, pulse])

	if (!visible) return null

	return (
		<Modal transparent animationType="fade" visible={visible}>
			<View style={styles.overlay}>
				<Animated.Text style={[styles.logo, { opacity: pulse }]}>
					SHOOTRZ
				</Animated.Text>
				{message ? <Text style={styles.message}>{message}</Text> : null}
			</View>
		</Modal>
	)
}

const styles = StyleSheet.create({
	overlay: {
		flex: 1,
		backgroundColor: 'rgba(8, 10, 14, 0.92)',
		alignItems: 'center',
		justifyContent: 'center',
	},
	logo: {
		fontSize: typography.size['3xl'],
		fontWeight: typography.weight.black,
		color: colors.brand.orange,
		letterSpacing: typography.tracking.widest,
	},
	message: {
		fontSize: typography.size.base,
		color: colors.text.secondary,
		marginTop: spacing[4],
	},
})
