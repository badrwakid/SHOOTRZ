import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { AnalysisPlayer } from './AnalysisPlayer'
import { SHOOTRZ_THEME } from '../constants/theme'

interface AnnotatedVideoPlayerProps {
	videoUri: string
	annotatedVideoUri?: string | null
	poseResults?: Array<{
		frame_idx: number
		landmarks: Array<{ x: number; y: number; z?: number; confidence?: number }>
		confidence: number[]
		timestamp_ms: number
	}>
	ballTrajectory?: Array<{ x: number; y: number; z?: number; frame?: number }>
	phases?: Array<{
		phase: string
		start_frame: number
		end_frame: number
		confidence: number
	}>
	onFrameChange?: (frameIdx: number) => void
}

export const AnnotatedVideoPlayer: React.FC<AnnotatedVideoPlayerProps> = ({
	videoUri,
	annotatedVideoUri,
	poseResults,
	ballTrajectory,
	phases,
	onFrameChange,
}) => {
	// Use annotated video if available, otherwise fall back to original
	const displayUri = annotatedVideoUri || videoUri
	const isAnnotated = !!annotatedVideoUri

	return (
		<View style={styles.container}>
			{!isAnnotated && (
				<View style={styles.noteContainer}>
					<Text style={styles.noteText}>
						Note: Showing original video. Annotated video with skeleton overlay coming soon.
					</Text>
				</View>
			)}
			<AnalysisPlayer
				videoUri={displayUri}
				poseResults={poseResults}
				ballTrajectory={ballTrajectory}
				phases={phases}
				onFrameChange={onFrameChange}
			/>
		</View>
	)
}

const styles = StyleSheet.create({
	container: {
		width: '100%',
	},
	noteContainer: {
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		padding: SHOOTRZ_THEME.spacing.md,
		borderRadius: SHOOTRZ_THEME.borderRadius.md,
		marginBottom: SHOOTRZ_THEME.spacing.sm,
	},
	noteText: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		textAlign: 'center',
		fontStyle: 'italic',
	},
})



