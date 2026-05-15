import { useEffect, useState } from 'react'
import { AccessibilityInfo } from 'react-native'

/**
 * Subscribes to the system "reduce motion" / "remove animations" preference.
 * When `true`, prefer instant or static UI instead of looping or decorative motion.
 */
export function useReduceMotion(): boolean {
	const [reduced, setReduced] = useState(false)

	useEffect(() => {
		let cancelled = false
		AccessibilityInfo.isReduceMotionEnabled()
			.then(value => {
				if (!cancelled) setReduced(value)
			})
			.catch(() => {
				if (!cancelled) setReduced(false)
			})

		const sub = AccessibilityInfo.addEventListener('reduceMotionChanged', (value: boolean) => {
			setReduced(value)
		})

		return () => {
			cancelled = true
			sub.remove()
		}
	}, [])

	return reduced
}
