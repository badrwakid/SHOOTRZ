import React, { useEffect, useRef } from 'react'
import { View, Text, StyleSheet, Animated } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { colors, typography, spacing, animation } from '../constants/theme'
import { ShootrzLogo } from '../components/ShootrzLogo'

interface SplashScreenProps {
	onFinish: () => void
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish }) => {
	const fadeAnim = useRef(new Animated.Value(0)).current
	const scaleAnim = useRef(new Animated.Value(0.85)).current
	const dots = useRef([
		new Animated.Value(0.3),
		new Animated.Value(0.3),
		new Animated.Value(0.3),
	]).current

	useEffect(() => {
		Animated.parallel([
			Animated.timing(fadeAnim, {
				toValue: 1,
				duration: 600,
				useNativeDriver: true,
			}),
			Animated.spring(scaleAnim, {
				toValue: 1,
				damping: animation.easing.spring.damping,
				stiffness: animation.easing.spring.stiffness,
				useNativeDriver: true,
			}),
		]).start()

		const dotAnims = dots.map((dot, i) =>
			Animated.loop(
				Animated.sequence([
					Animated.delay(i * 200),
					Animated.timing(dot, {
						toValue: 1,
						duration: 400,
						useNativeDriver: true,
					}),
					Animated.timing(dot, {
						toValue: 0.3,
						duration: 400,
						useNativeDriver: true,
					}),
				]),
			),
		)
		dotAnims.forEach(a => a.start())

		const timer = setTimeout(() => {
			Animated.timing(fadeAnim, {
				toValue: 0,
				duration: animation.duration.normal,
				useNativeDriver: true,
			}).start(() => onFinish())
		}, 2000)

		return () => {
			clearTimeout(timer)
			dotAnims.forEach(a => a.stop())
		}
	}, [onFinish])

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
			<Animated.View
				style={[
					styles.content,
					{
						opacity: fadeAnim,
						transform: [{ scale: scaleAnim }],
					},
				]}
			>
				<View style={styles.logoContainer}>
					<ShootrzLogo size="large" showTagline={false} />
				</View>

				<View style={styles.dotsRow}>
					{dots.map((opacity, i) => (
						<Animated.View
							key={i}
							style={[styles.dot, { opacity }]}
						/>
					))}
				</View>

				<Text style={styles.tagline}>PERFECT THE GAME</Text>
			</Animated.View>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: colors.bg.void,
		justifyContent: 'center',
		alignItems: 'center',
	},
	content: {
		alignItems: 'center',
	},
	logoContainer: {
		marginBottom: spacing[8],
	},
	dotsRow: {
		flexDirection: 'row',
		gap: spacing[2],
		marginBottom: spacing[6],
	},
	dot: {
		width: 8,
		height: 8,
		borderRadius: 4,
		backgroundColor: colors.brand.orange,
	},
	tagline: {
		...typography.roles.caption,
		fontSize: typography.size.xs,
		fontWeight: typography.weight.medium,
		fontFamily: 'DMSansMedium',
		color: colors.brand.cyan,
		letterSpacing: typography.tracking.widest,
	},
})
