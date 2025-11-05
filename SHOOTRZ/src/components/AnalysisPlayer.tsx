import React, { useState, useRef, useEffect, useCallback } from 'react'
import {
	View,
	Text,
	StyleSheet,
	TouchableOpacity,
	Dimensions,
	Animated,
	ActivityIndicator,
} from 'react-native'
import { Video, ResizeMode, AVPlaybackStatus } from 'expo-av'
import { LinearGradient } from 'expo-linear-gradient'
import { Ionicons } from '@expo/vector-icons'
import { SHOOTRZ_THEME } from '../constants/theme'
import { Svg, Circle, Line, Path } from 'react-native-svg'

interface PoseLandmark {
	x: number
	y: number
	z?: number
	confidence?: number
}

interface BallPosition {
	x: number
	y: number
	z?: number
	frame?: number
}

interface Phase {
	phase: string
	start_frame: number
	end_frame: number
	confidence: number
}

interface AnalysisPlayerProps {
	videoUri: string
	poseResults?: Array<{
		frame_idx: number
		landmarks: PoseLandmark[]
		confidence: number[]
		timestamp_ms: number
	}>
	ballTrajectory?: BallPosition[]
	phases?: Phase[]
	onFrameChange?: (frameIdx: number) => void
}

export function AnalysisPlayer({
	videoUri,
	poseResults = [],
	ballTrajectory = [],
	phases = [],
	onFrameChange,
}: AnalysisPlayerProps) {
	const videoRef = useRef<Video>(null)
	const [isPlaying, setIsPlaying] = useState(false)
	const [currentTime, setCurrentTime] = useState(0)
	const [duration, setDuration] = useState(0)
	const [showSkeleton, setShowSkeleton] = useState(true)
	const [showTrajectory, setShowTrajectory] = useState(true)
	const [showPhases, setShowPhases] = useState(true)
	const [videoDimensions, setVideoDimensions] = useState({ width: 0, height: 0 })
	const [isLoading, setIsLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)
	const playbackStatusRef = useRef<AVPlaybackStatus | null>(null)

	// Get current frame index based on time
	const getCurrentFrame = (timeMs: number): number => {
		if (!poseResults.length) return 0
		const fps = 30 // Assume 30fps, could be dynamic
		return Math.floor((timeMs / 1000) * fps)
	}

	const currentFrame = getCurrentFrame(currentTime)
	const currentPose = poseResults.find((p) => p.frame_idx === currentFrame)
	const currentPhase = phases.find(
		(p) => currentFrame >= p.start_frame && currentFrame <= p.end_frame
	)

	// MediaPipe Pose skeleton connections
	const POSE_CONNECTIONS = [
		// Torso
		[11, 12], // Left shoulder - Right shoulder
		[11, 23], // Left shoulder - Left hip
		[12, 24], // Right shoulder - Right hip
		[23, 24], // Left hip - Right hip
		// Left arm
		[11, 13], // Left shoulder - Left elbow
		[13, 15], // Left elbow - Left wrist
		// Right arm (shooting arm)
		[12, 14], // Right shoulder - Right elbow
		[14, 16], // Right elbow - Right wrist
		// Left leg
		[23, 25], // Left hip - Left knee
		[25, 27], // Left knee - Left ankle
		// Right leg
		[24, 26], // Right hip - Right knee
		[26, 28], // Right knee - Right ankle
	]

	const renderSkeleton = () => {
		if (!currentPose || !showSkeleton) return null

		const landmarks = currentPose.landmarks
		const screenWidth = Dimensions.get('window').width
		const aspectRatio = videoDimensions.width / videoDimensions.height || 16 / 9
		const displayWidth = screenWidth
		const displayHeight = screenWidth / aspectRatio

		return (
			<Svg
				style={StyleSheet.absoluteFill}
				width={displayWidth}
				height={displayHeight}
			>
				{/* Draw connections */}
				{POSE_CONNECTIONS.map(([start, end], idx) => {
					const startLandmark = landmarks[start]
					const endLandmark = landmarks[end]
					if (!startLandmark || !endLandmark) return null

					return (
						<Line
							key={idx}
							x1={startLandmark.x * displayWidth}
							y1={startLandmark.y * displayHeight}
							x2={endLandmark.x * displayWidth}
							y2={endLandmark.y * displayHeight}
							stroke={SHOOTRZ_THEME.colors.primary}
							strokeWidth="2"
						/>
					)
				})}

				{/* Draw keypoints */}
				{landmarks.map((landmark, idx) => {
					// Highlight shooting arm (right side)
					const isShootingArm = idx === 14 || idx === 16 // Right elbow, right wrist
					return (
						<Circle
							key={idx}
							cx={landmark.x * displayWidth}
							cy={landmark.y * displayHeight}
							r={isShootingArm ? 6 : 4}
							fill={isShootingArm ? SHOOTRZ_THEME.colors.accent : SHOOTRZ_THEME.colors.primary}
						/>
					)
				})}
			</Svg>
		)
	}

	const renderBallTrajectory = () => {
		if (!ballTrajectory.length || !showTrajectory) return null

		const screenWidth = Dimensions.get('window').width
		const aspectRatio = videoDimensions.width / videoDimensions.height || 16 / 9
		const displayWidth = screenWidth
		const displayHeight = screenWidth / aspectRatio

		// Filter trajectory up to current frame
		const trajectoryUntilCurrent = ballTrajectory.filter(
			(pos) => !pos.frame || pos.frame <= currentFrame
		)

		if (trajectoryUntilCurrent.length < 2) return null

		const pathData = trajectoryUntilCurrent
			.map((pos, idx) => `${idx === 0 ? 'M' : 'L'} ${pos.x * displayWidth} ${pos.y * displayHeight}`)
			.join(' ')

		return (
			<Svg style={StyleSheet.absoluteFill} width={displayWidth} height={displayHeight}>
				<Path
					d={pathData}
					stroke={SHOOTRZ_THEME.colors.accent}
					strokeWidth="3"
					fill="none"
					strokeDasharray="5,5"
				/>
				{/* Current ball position */}
				{trajectoryUntilCurrent.length > 0 && (
					<Circle
						cx={trajectoryUntilCurrent[trajectoryUntilCurrent.length - 1].x * displayWidth}
						cy={trajectoryUntilCurrent[trajectoryUntilCurrent.length - 1].y * displayHeight}
						r="8"
						fill={SHOOTRZ_THEME.colors.accent}
					/>
				)}
			</Svg>
		)
	}

	const renderPhaseMarker = () => {
		if (!currentPhase || !showPhases) return null

		const phaseColors: Record<string, string> = {
			stance: SHOOTRZ_THEME.colors.textSecondary,
			crouch: SHOOTRZ_THEME.colors.primary,
			release: SHOOTRZ_THEME.colors.accent,
			landing: SHOOTRZ_THEME.colors.success,
		}

		return (
			<View style={styles.phaseMarker}>
				<View
					style={[
						styles.phaseBadge,
						{ backgroundColor: phaseColors[currentPhase.phase] || SHOOTRZ_THEME.colors.primary },
					]}
				>
					<Text style={styles.phaseText}>
						{currentPhase.phase.charAt(0).toUpperCase() + currentPhase.phase.slice(1)}
					</Text>
				</View>
			</View>
		)
	}

	const handlePlayPause = async () => {
		if (videoRef.current) {
			if (isPlaying) {
				await videoRef.current.pauseAsync()
			} else {
				await videoRef.current.playAsync()
			}
			setIsPlaying(!isPlaying)
		}
	}

	const formatTime = (ms: number): string => {
		const seconds = Math.floor(ms / 1000)
		const minutes = Math.floor(seconds / 60)
		const remainingSeconds = seconds % 60
		return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
	}

	const seekToFrame = async (frameIdx: number) => {
		if (videoRef.current && duration > 0) {
			const fps = 30
			const timeMs = (frameIdx / fps) * 1000
			await videoRef.current.setPositionAsync(timeMs)
			onFrameChange?.(frameIdx)
		}
	}

	return (
		<View style={styles.container}>
			{/* Video Player */}
			<View style={styles.videoContainer}>
				<Video
					ref={videoRef}
					source={{ uri: videoUri }}
					style={styles.video}
					resizeMode={ResizeMode.CONTAIN}
					useNativeControls={false}
					onLoad={(data) => {
						setDuration(data.durationMillis || 0)
						if (data.naturalSize) {
							setVideoDimensions({
								width: data.naturalSize.width,
								height: data.naturalSize.height,
							})
						}
					}}
					onLoadStart={() => setIsLoading(true)}
					onLoad={(data) => {
						setIsLoading(false)
						setDuration(data.durationMillis || 0)
						if (data.naturalSize) {
							setVideoDimensions({
								width: data.naturalSize.width,
								height: data.naturalSize.height,
							})
						}
					}}
					onError={(error) => {
						setIsLoading(false)
						setError(error?.message || 'Failed to load video')
						console.error('Video playback error:', error)
					}}
					onPlaybackStatusUpdate={(status) => {
						playbackStatusRef.current = status
						if (status.isLoaded) {
							setCurrentTime(status.positionMillis || 0)
							setIsPlaying(status.isPlaying)
							if (status.positionMillis) {
								const frame = getCurrentFrame(status.positionMillis)
								onFrameChange?.(frame)
							}
						}
					}}
				/>

				{/* Overlays */}
				{renderSkeleton()}
				{renderBallTrajectory()}
				{renderPhaseMarker()}

				{/* Loading Indicator */}
				{isLoading && (
					<View style={styles.loadingOverlay}>
						<ActivityIndicator size="large" color={SHOOTRZ_THEME.colors.primary} />
						<Text style={styles.loadingText}>Loading video...</Text>
					</View>
				)}

				{/* Error Message */}
				{error && (
					<View style={styles.errorOverlay}>
						<Ionicons name="alert-circle" size={32} color={SHOOTRZ_THEME.colors.error} />
						<Text style={styles.errorText}>{error}</Text>
					</View>
				)}

				{/* Play/Pause Overlay */}
				{!isLoading && !error && (
					<TouchableOpacity
						style={styles.playButton}
						onPress={handlePlayPause}
						activeOpacity={0.7}
					>
						<LinearGradient
							colors={[SHOOTRZ_THEME.colors.primary + 'CC', SHOOTRZ_THEME.colors.secondary + 'CC']}
							style={styles.playButtonGradient}
						>
							<Ionicons
								name={isPlaying ? 'pause' : 'play'}
								size={32}
								color="#fff"
							/>
						</LinearGradient>
					</TouchableOpacity>
				)}
			</View>

			{/* Controls */}
			<View style={styles.controls}>
				{/* Timeline */}
				<View style={styles.timelineContainer}>
					<Text style={styles.timeText}>{formatTime(currentTime)}</Text>
					<View style={styles.timeline}>
						{phases.map((phase, idx) => {
							const phaseStart = (phase.start_frame / (duration / 1000 / (1/30))) * 100
							const phaseEnd = (phase.end_frame / (duration / 1000 / (1/30))) * 100
							const phaseColors: Record<string, string> = {
								stance: SHOOTRZ_THEME.colors.textSecondary,
								crouch: SHOOTRZ_THEME.colors.primary,
								release: SHOOTRZ_THEME.colors.accent,
								landing: SHOOTRZ_THEME.colors.success,
							}
							return (
								<View
									key={idx}
									style={[
										styles.timelinePhase,
										{
											left: `${phaseStart}%`,
											width: `${phaseEnd - phaseStart}%`,
											backgroundColor: phaseColors[phase.phase] || SHOOTRZ_THEME.colors.primary,
										},
									]}
								/>
							)
						})}
						<View
							style={[
								styles.timelineProgress,
								{ width: `${(currentTime / duration) * 100}%` },
							]}
						/>
					</View>
					<Text style={styles.timeText}>{formatTime(duration)}</Text>
				</View>

				{/* Toggle Buttons */}
				<View style={styles.toggleContainer}>
					<TouchableOpacity
						style={[styles.toggleButton, showSkeleton && styles.toggleButtonActive]}
						onPress={() => setShowSkeleton(!showSkeleton)}
					>
						<Ionicons
							name="body-outline"
							size={20}
							color={showSkeleton ? '#fff' : SHOOTRZ_THEME.colors.textSecondary}
						/>
						<Text style={[styles.toggleText, showSkeleton && styles.toggleTextActive]}>
							Skeleton
						</Text>
					</TouchableOpacity>

					<TouchableOpacity
						style={[styles.toggleButton, showTrajectory && styles.toggleButtonActive]}
						onPress={() => setShowTrajectory(!showTrajectory)}
					>
						<Ionicons
							name="basketball-outline"
							size={20}
							color={showTrajectory ? '#fff' : SHOOTRZ_THEME.colors.textSecondary}
						/>
						<Text style={[styles.toggleText, showTrajectory && styles.toggleTextActive]}>
							Trajectory
						</Text>
					</TouchableOpacity>

					<TouchableOpacity
						style={[styles.toggleButton, showPhases && styles.toggleButtonActive]}
						onPress={() => setShowPhases(!showPhases)}
					>
						<Ionicons
							name="list-outline"
							size={20}
							color={showPhases ? '#fff' : SHOOTRZ_THEME.colors.textSecondary}
						/>
						<Text style={[styles.toggleText, showPhases && styles.toggleTextActive]}>
							Phases
						</Text>
					</TouchableOpacity>
				</View>
			</View>
		</View>
	)
}

const styles = StyleSheet.create({
	container: {
		backgroundColor: SHOOTRZ_THEME.colors.background,
	},
	videoContainer: {
		width: '100%',
		aspectRatio: 16 / 9,
		backgroundColor: '#000',
		position: 'relative',
	},
	video: {
		width: '100%',
		height: '100%',
	},
	phaseMarker: {
		position: 'absolute',
		top: 16,
		left: 16,
	},
	phaseBadge: {
		paddingHorizontal: 12,
		paddingVertical: 6,
		borderRadius: 16,
	},
	phaseText: {
		color: '#fff',
		fontWeight: 'bold',
		fontSize: 12,
	},
	playButton: {
		position: 'absolute',
		top: '50%',
		left: '50%',
		transform: [{ translateX: -30 }, { translateY: -30 }],
		width: 60,
		height: 60,
		borderRadius: 30,
		overflow: 'hidden',
	},
	playButtonGradient: {
		width: '100%',
		height: '100%',
		alignItems: 'center',
		justifyContent: 'center',
	},
	controls: {
		padding: 16,
		backgroundColor: SHOOTRZ_THEME.colors.surface,
	},
	timelineContainer: {
		flexDirection: 'row',
		alignItems: 'center',
		marginBottom: 16,
	},
	timeText: {
		fontSize: 12,
		color: SHOOTRZ_THEME.colors.textSecondary,
		minWidth: 40,
	},
	timeline: {
		flex: 1,
		height: 6,
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		borderRadius: 3,
		marginHorizontal: 12,
		position: 'relative',
		overflow: 'hidden',
	},
	timelinePhase: {
		position: 'absolute',
		height: '100%',
		opacity: 0.5,
	},
	timelineProgress: {
		position: 'absolute',
		height: '100%',
		backgroundColor: SHOOTRZ_THEME.colors.primary,
		borderRadius: 3,
	},
	toggleContainer: {
		flexDirection: 'row',
		justifyContent: 'space-around',
		gap: 8,
	},
	toggleButton: {
		flex: 1,
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		padding: 10,
		borderRadius: 8,
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		gap: 6,
	},
	toggleButtonActive: {
		backgroundColor: SHOOTRZ_THEME.colors.primary,
	},
	toggleText: {
		fontSize: 12,
		color: SHOOTRZ_THEME.colors.textSecondary,
		fontWeight: '500',
	},
	toggleTextActive: {
		color: '#fff',
	},
	loadingOverlay: {
		...StyleSheet.absoluteFillObject,
		backgroundColor: 'rgba(0, 0, 0, 0.7)',
		alignItems: 'center',
		justifyContent: 'center',
	},
	loadingText: {
		color: '#fff',
		marginTop: 12,
		fontSize: 14,
	},
	errorOverlay: {
		...StyleSheet.absoluteFillObject,
		backgroundColor: 'rgba(0, 0, 0, 0.8)',
		alignItems: 'center',
		justifyContent: 'center',
		padding: 20,
	},
	errorText: {
		color: SHOOTRZ_THEME.colors.error,
		marginTop: 12,
		fontSize: 14,
		textAlign: 'center',
	},
})
