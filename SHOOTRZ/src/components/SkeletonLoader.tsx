import React, { useEffect, useRef } from 'react'
import { Animated, StyleSheet, ViewStyle } from 'react-native'
import { colors, radius as themeRadius } from '../constants/theme'

interface SkeletonLoaderProps {
	width: number | string
	height: number
	radius?: number
	style?: ViewStyle
}

export function SkeletonLoader({
	width,
	height,
	radius = themeRadius.md,
	style,
}: SkeletonLoaderProps) {
	const opacity = useRef(new Animated.Value(0.3)).current

	useEffect(() => {
		const anim = Animated.loop(
			Animated.sequence([
				Animated.timing(opacity, {
					toValue: 0.7,
					duration: 600,
					useNativeDriver: true,
				}),
				Animated.timing(opacity, {
					toValue: 0.3,
					duration: 600,
					useNativeDriver: true,
				}),
			]),
		)
		anim.start()
		return () => anim.stop()
	}, [opacity])

	return (
		<Animated.View
			style={[
				styles.skeleton,
				{ width: width as any, height, borderRadius: radius, opacity },
				style,
			]}
		/>
	)
}

const styles = StyleSheet.create({
	skeleton: {
		backgroundColor: colors.bg.elevated,
	},
})
