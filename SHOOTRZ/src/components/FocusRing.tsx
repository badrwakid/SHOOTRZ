import React from 'react'
import { View, ViewStyle, StyleProp } from 'react-native'
import { semanticTokens } from '../theme/tokens'

/**
 * Structured focus ring (not a CSS box-shadow string). Use semantic focus tokens.
 */
export type FocusRingToken = {
	/** Visible ring stroke color (AA contrast on dark UI). */
	ring: string
	/** Optional soft fill behind the control (e.g. selection halo). */
	ringSoft: string
	/** Border width in logical pixels. */
	width: number
	/** Space between the control edge and the focus ring. */
	offset: number
}

export const defaultFocusRing: FocusRingToken = {
	ring: semanticTokens.focus.ring,
	ringSoft: semanticTokens.focus.ringSoft,
	width: semanticTokens.focus.ringWidth,
	offset: 2,
}

type FocusRingProps = {
	children: React.ReactNode
	/** When true, draws the focus ring around the child. */
	visible: boolean
	/** The inner control’s border radius; outer radius is derived. */
	innerBorderRadius: number
	token?: FocusRingToken
	/** Merged with the outer wrapper. */
	style?: StyleProp<ViewStyle>
}

/**
 * Wrapper-based focus ring: padding + border using token fields only.
 */
export function FocusRing({
	children,
	visible,
	innerBorderRadius,
	token = defaultFocusRing,
	style,
}: FocusRingProps) {
	if (!visible) {
		return <>{children}</>
	}
	const { width, offset, ring, ringSoft } = token
	const outerRadius = innerBorderRadius + offset + width
	return (
		<View
			style={[
				{
					borderRadius: outerRadius,
					borderWidth: width,
					borderColor: ring,
					backgroundColor: ringSoft,
					padding: offset,
				},
				style,
			]}
		>
			{children}
		</View>
	)
}
