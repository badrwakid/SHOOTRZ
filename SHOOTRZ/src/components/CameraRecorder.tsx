import React, { useState, useRef, useEffect } from 'react'
import {
	View,
	Text,
	StyleSheet,
	TouchableOpacity,
	Alert,
	Dimensions,
	ActivityIndicator,
} from 'react-native'
import { CameraView, useCameraPermissions, useMicrophonePermissions } from 'expo-camera'
import { Ionicons } from '@expo/vector-icons'
import { LinearGradient } from 'expo-linear-gradient'
import { SafeAreaView } from 'react-native-safe-area-context'
import { SHOOTRZ_THEME } from '../constants/theme'
import { hapticFeedback } from '../utils/hapticFeedback'

const { width, height } = Dimensions.get('window')

interface CameraRecorderProps {
	onVideoRecorded: (uri: string) => void
	onCancel: () => void
	maxDuration?: number // seconds
}

export function CameraRecorder({
	onVideoRecorded,
	onCancel,
	maxDuration = 30,
}: CameraRecorderProps) {
	const [cameraPermission, requestCameraPermission] = useCameraPermissions()
	const [microphonePermission, requestMicrophonePermission] = useMicrophonePermissions()
	const cameraRef = useRef<any>(null)
	const [isRecording, setIsRecording] = useState(false)
	const [recordingTime, setRecordingTime] = useState(0)
	const [facing, setFacing] = useState<'back' | 'front'>('back')
	const [timer, setTimer] = useState<NodeJS.Timeout | null>(null)
	const [isCameraReady, setIsCameraReady] = useState(false)

	useEffect(() => {
		requestPermissions()
	}, [])

	useEffect(() => {
		if (isRecording) {
			const interval = setInterval(() => {
				setRecordingTime((prev) => {
					const newTime = prev + 1
					if (newTime >= maxDuration) {
						stopRecording()
						return maxDuration
					}
					return newTime
				})
			}, 1000)
			setTimer(interval)

			return () => {
				if (interval) clearInterval(interval)
			}
		} else {
			if (timer) clearInterval(timer)
		}
	}, [isRecording, maxDuration])

	const requestPermissions = async () => {
		if (!cameraPermission?.granted) {
			const result = await requestCameraPermission()
			if (!result.granted) {
				Alert.alert(
					'Permission Required',
					'Camera permission is required to record videos.',
					[{ text: 'OK', onPress: onCancel }]
				)
				return
			}
		}

		if (!microphonePermission?.granted) {
			const result = await requestMicrophonePermission()
			if (!result.granted) {
				Alert.alert(
					'Permission Required',
					'Microphone permission is required to record videos.',
					[{ text: 'OK', onPress: onCancel }]
				)
				return
			}
		}
	}

	const startRecording = async () => {
		if (!isCameraReady) {
			if (__DEV__) {
				console.warn('⚠️ Camera not ready yet')
			}
			Alert.alert('Camera Not Ready', 'Please wait for the camera to initialize.')
			return
		}

		if (!cameraRef.current) {
			Alert.alert('Camera Error', 'Camera reference is not available.')
			return
		}

		// Verify the ref has the recordAsync method
		if (typeof cameraRef.current.recordAsync !== 'function') {
			console.error('❌ recordAsync method not found on camera ref')
			Alert.alert('Camera Error', 'Recording method not available.')
			return
		}

		try {
			hapticFeedback.medium()
			setIsRecording(true)
			setRecordingTime(0)

			if (__DEV__) {
				console.log('🎬 Starting video recording...')
			}

			// Start recording - recordAsync returns a promise that resolves when recording stops
			const recordingPromise = cameraRef.current.recordAsync({
				maxDuration: maxDuration,
				mute: false,
			})

			// Wait for recording to complete (resolves when stopped or max duration reached)
			recordingPromise.then((video: any) => {
				if (__DEV__) {
					console.log('✅ Recording completed:', video)
				}
				if (video && video.uri) {
					hapticFeedback.success()
					setIsRecording(false)
					onVideoRecorded(video.uri)
				} else {
					throw new Error('No video URI returned')
				}
			}).catch((error: any) => {
				console.error('❌ Recording error:', error)
				Alert.alert('Recording Error', error.message || 'Failed to record video. Please try again.')
				setIsRecording(false)
			})
		} catch (error: any) {
			console.error('❌ Error starting recording:', error)
			Alert.alert('Recording Error', error.message || 'Failed to start recording. Please try again.')
			setIsRecording(false)
		}
	}

	const stopRecording = async () => {
		if (cameraRef.current && isRecording) {
			cameraRef.current.stopRecording()
			setIsRecording(false)
		}
	}

	const toggleCameraType = () => {
		setFacing((prev) => (prev === 'back' ? 'front' : 'back'))
	}

	const formatTime = (seconds: number): string => {
		const mins = Math.floor(seconds / 60)
		const secs = seconds % 60
		return `${mins}:${secs.toString().padStart(2, '0')}`
	}

	if (!cameraPermission || !microphonePermission) {
		return (
			<View style={styles.container}>
				<ActivityIndicator size="large" color={SHOOTRZ_THEME.colors.primary} />
				<Text style={styles.loadingText}>Requesting camera permissions...</Text>
			</View>
		)
	}

	if (!cameraPermission.granted || !microphonePermission.granted) {
		return (
			<View style={styles.container}>
				<Text style={styles.errorText}>Camera or microphone permission denied</Text>
				<TouchableOpacity style={styles.button} onPress={onCancel}>
					<Text style={styles.buttonText}>Go Back</Text>
				</TouchableOpacity>
			</View>
		)
	}

	return (
		<SafeAreaView style={styles.container} edges={['top']}>
			<CameraView
				ref={cameraRef}
				style={styles.camera}
				facing={facing}
				mode="video"
				onCameraReady={() => {
					// Add small delay to ensure camera is fully initialized
					setTimeout(() => {
						setIsCameraReady(true)
						if (__DEV__) {
							console.log('📷 Camera is ready and initialized')
						}
					}, 300)
				}}
			/>
			
			{/* Overlays - positioned absolutely over CameraView */}
			{/* Top Controls */}
			<View style={styles.topControls}>
					<TouchableOpacity
						style={styles.controlButton}
						onPress={onCancel}
						activeOpacity={0.7}
					>
						<Ionicons name="close" size={28} color="#fff" />
					</TouchableOpacity>

					{/* Flash toggle removed for v17 API - can be added later if needed */}
				</View>

				{/* Recording Timer */}
				{isRecording && (
					<View style={styles.timerContainer}>
						<View style={styles.recordingIndicator} />
						<Text style={styles.timerText}>{formatTime(recordingTime)}</Text>
					</View>
				)}

				{/* Recording Guidelines Overlay */}
				{!isRecording && (
					<View style={styles.guidelinesOverlay}>
						<Text style={styles.guidelinesTitle}>Recording Tips</Text>
						<View style={styles.guidelineRow}>
							<Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
							<Text style={styles.guidelineText}>
								Position phone 4-6m away, at waist height
							</Text>
						</View>
						<View style={styles.guidelineRow}>
							<Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
							<Text style={styles.guidelineText}>
								Capture full body (head to feet)
							</Text>
						</View>
						<View style={styles.guidelineRow}>
							<Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
							<Text style={styles.guidelineText}>
								Record the full shooting motion
							</Text>
						</View>
					</View>
				)}

				{/* Bottom Controls */}
				<View style={styles.bottomControls}>
					<View style={styles.leftControls}>
						{!isRecording && (
							<TouchableOpacity
								style={styles.secondaryButton}
								onPress={toggleCameraType}
								activeOpacity={0.7}
							>
								<Ionicons name="camera-reverse" size={24} color="#fff" />
							</TouchableOpacity>
						)}
					</View>

					{/* Record Button */}
					<TouchableOpacity
						style={[styles.recordButton, isRecording && styles.recordButtonActive]}
						onPress={isRecording ? stopRecording : startRecording}
						activeOpacity={0.8}
						disabled={(isRecording && recordingTime >= maxDuration) || !isCameraReady}
					>
						<View style={styles.recordButtonInner} />
					</TouchableOpacity>

					<View style={styles.rightControls}>
						{/* Spacer for alignment */}
					</View>
				</View>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: '#000',
		justifyContent: 'center',
		alignItems: 'center',
	},
	camera: {
		flex: 1,
		width: width,
		height: height,
	},
	topControls: {
		position: 'absolute',
		top: 0,
		left: 0,
		right: 0,
		flexDirection: 'row',
		justifyContent: 'space-between',
		padding: 20,
		paddingTop: 40,
		zIndex: 10,
	},
	controlButton: {
		width: 44,
		height: 44,
		borderRadius: 22,
		backgroundColor: 'rgba(0, 0, 0, 0.5)',
		justifyContent: 'center',
		alignItems: 'center',
	},
	timerContainer: {
		position: 'absolute',
		top: 100,
		left: 0,
		right: 0,
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		paddingHorizontal: 16,
		paddingVertical: 8,
		backgroundColor: 'rgba(0, 0, 0, 0.6)',
		borderRadius: 20,
		alignSelf: 'center',
		zIndex: 10,
	},
	recordingIndicator: {
		width: 12,
		height: 12,
		borderRadius: 6,
		backgroundColor: '#FF0000',
		marginRight: 8,
	},
	timerText: {
		color: '#fff',
		fontSize: 16,
		fontWeight: 'bold',
	},
	guidelinesOverlay: {
		position: 'absolute',
		bottom: 200,
		left: 20,
		right: 20,
		backgroundColor: 'rgba(0, 0, 0, 0.7)',
		borderRadius: 12,
		padding: 16,
		zIndex: 10,
	},
	guidelinesTitle: {
		color: '#fff',
		fontSize: 16,
		fontWeight: 'bold',
		marginBottom: 12,
	},
	guidelineRow: {
		flexDirection: 'row',
		alignItems: 'center',
		marginBottom: 8,
	},
	guidelineText: {
		color: '#fff',
		fontSize: 14,
		marginLeft: 8,
	},
	bottomControls: {
		position: 'absolute',
		bottom: 40,
		left: 0,
		right: 0,
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		paddingHorizontal: 40,
		zIndex: 10,
	},
	leftControls: {
		width: 60,
		alignItems: 'flex-start',
	},
	rightControls: {
		width: 60,
	},
	secondaryButton: {
		width: 44,
		height: 44,
		borderRadius: 22,
		backgroundColor: 'rgba(0, 0, 0, 0.5)',
		justifyContent: 'center',
		alignItems: 'center',
	},
	recordButton: {
		width: 80,
		height: 80,
		borderRadius: 40,
		backgroundColor: 'rgba(255, 255, 255, 0.3)',
		justifyContent: 'center',
		alignItems: 'center',
		borderWidth: 4,
		borderColor: '#fff',
	},
	recordButtonActive: {
		borderColor: '#FF0000',
		backgroundColor: 'rgba(255, 0, 0, 0.3)',
	},
	recordButtonInner: {
		width: 64,
		height: 64,
		borderRadius: 32,
		backgroundColor: '#fff',
	},
	loadingText: {
		color: '#fff',
		marginTop: 16,
		fontSize: 16,
	},
	errorText: {
		color: '#fff',
		fontSize: 18,
		marginBottom: 20,
		textAlign: 'center',
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

