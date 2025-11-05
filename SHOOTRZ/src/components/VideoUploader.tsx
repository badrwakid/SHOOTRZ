import React, { useState } from 'react'
import {
	View,
	Text,
	StyleSheet,
	TouchableOpacity,
	Alert,
	ActivityIndicator,
	ScrollView,
} from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import * as ImagePicker from 'expo-image-picker'
import { Ionicons } from '@expo/vector-icons'
import { apiService } from '../services/api.service'
import { useAuth } from '../context/AuthContext'
import { SHOOTRZ_THEME } from '../constants/theme'
import { hapticFeedback } from '../utils/hapticFeedback'

interface VideoUploaderProps {
	onVideoSelected?: (uri: string) => void
	onAnalysisStarted?: (jobId: string) => void
	onRecordVideo?: () => void // Callback to show full camera recorder
}

export function VideoUploader({
	onVideoSelected,
	onAnalysisStarted,
	onRecordVideo,
}: VideoUploaderProps) {
	const { user } = useAuth()
	const [isUploading, setIsUploading] = useState(false)
	const [uploadProgress, setUploadProgress] = useState(0)
	const [selectedVideo, setSelectedVideo] = useState<string | null>(null)

	const requestPermissions = async () => {
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync()
		if (status !== 'granted') {
			Alert.alert(
				'Permission Required',
				'Please grant camera roll permissions to select videos.',
				[{ text: 'OK' }]
			)
			return false
		}
		return true
	}

	const validateVideoQuality = (videoUri: string): Promise<boolean> => {
		return new Promise((resolve) => {
			// For MVP, we'll do basic validation
			// In production, use expo-av to get video metadata
			resolve(true)
		})
	}

	const pickVideo = async () => {
		const hasPermission = await requestPermissions()
		if (!hasPermission) return

		try {
			const result = await ImagePicker.launchImageLibraryAsync({
				mediaTypes: 'videos', // Use lowercase string as required by new API
				allowsEditing: false,
				quality: 1,
				videoMaxDuration: 30, // Max 30 seconds
			})

			if (!result.canceled && result.assets[0]) {
				const videoUri = result.assets[0].uri
				setSelectedVideo(videoUri)

				if (onVideoSelected) {
					onVideoSelected(videoUri)
				}
			}
		} catch (error) {
			console.error('Error picking video:', error)
			Alert.alert('Error', 'Failed to select video. Please try again.')
		}
	}

	const recordVideo = async () => {
		// Option 1: Use full camera recorder (recommended)
		// This will be handled by parent component showing CameraRecorder
		// For now, fallback to ImagePicker for quick implementation
		
		const { status } = await ImagePicker.requestCameraPermissionsAsync()
		if (status !== 'granted') {
			Alert.alert(
				'Permission Required',
				'Please grant camera permissions to record videos.',
				[{ text: 'OK' }]
			)
			return
		}

		try {
			const result = await ImagePicker.launchCameraAsync({
				mediaTypes: 'videos', // Use lowercase string as required by new API
				allowsEditing: false,
				quality: 1,
				videoMaxDuration: 30,
			})

			if (!result.canceled && result.assets[0]) {
				const videoUri = result.assets[0].uri
				setSelectedVideo(videoUri)

				if (onVideoSelected) {
					onVideoSelected(videoUri)
				}
			}
		} catch (error) {
			console.error('Error recording video:', error)
			Alert.alert('Error', 'Failed to record video. Please try again.')
		}
	}

	// Enhanced record function that can use full camera screen
	const recordVideoWithFullCamera = async () => {
		// Trigger parent to show CameraRecorder component
		// This is a placeholder - parent component should handle showing CameraRecorder
		if (onVideoSelected) {
			// Signal parent to show camera recorder
			recordVideo() // Fallback to ImagePicker for now
		}
	}

	const uploadAndAnalyze = async () => {
		if (!selectedVideo) {
			Alert.alert('No Video', 'Please select or record a video first.')
			return
		}

		// Validate video quality
		const isValid = await validateVideoQuality(selectedVideo)
		if (!isValid) {
			Alert.alert(
				'Video Quality',
				'Please ensure your video is 1080p or higher at 30fps for best results.'
			)
			return
		}

		setIsUploading(true)
		setUploadProgress(0)
		hapticFeedback.medium()

		try {
			// Upload to backend for analysis
			const result = await apiService.analyzeVideo(selectedVideo)

			if (result && result.job_id) {
				if (onAnalysisStarted) {
					onAnalysisStarted(result.job_id)
				}
				Alert.alert(
					'Analysis Started',
					'Your video is being analyzed. Results will be available shortly.',
					[{ text: 'OK' }]
				)
			}
		} catch (error: any) {
			console.error('Error uploading video:', error)
			Alert.alert(
				'Upload Failed',
				error.message || 'Failed to upload video. Please check your connection and try again.'
			)
		} finally {
			setIsUploading(false)
			setUploadProgress(0)
		}
	}

	return (
		<ScrollView style={styles.container} contentContainerStyle={styles.content}>
			{/* Recording Guidelines */}
			<View style={styles.guidelinesContainer}>
				<Text style={styles.guidelinesTitle}>Recording Guidelines</Text>
				
				<View style={styles.guidelineItem}>
					<Ionicons name="videocam-outline" size={20} color={SHOOTRZ_THEME.colors.primary} />
					<Text style={styles.guidelineText}>
						Position phone at waist-to-chest height, 4-6m away
					</Text>
				</View>
				
				<View style={styles.guidelineItem}>
					<Ionicons name="angle" size={20} color={SHOOTRZ_THEME.colors.primary} />
					<Text style={styles.guidelineText}>
						Optimal angle: ~45° from shooter's front side
					</Text>
				</View>
				
				<View style={styles.guidelineItem}>
					<Ionicons name="sunny-outline" size={20} color={SHOOTRZ_THEME.colors.primary} />
					<Text style={styles.guidelineText}>
						Ensure good lighting and lock exposure/focus
					</Text>
				</View>
				
				<View style={styles.guidelineItem}>
					<Ionicons name="time-outline" size={20} color={SHOOTRZ_THEME.colors.primary} />
					<Text style={styles.guidelineText}>
						Record isolated shots (3-5 seconds each)
					</Text>
				</View>
				
				<View style={styles.guidelineItem}>
					<Ionicons name="tv-outline" size={20} color={SHOOTRZ_THEME.colors.primary} />
					<Text style={styles.guidelineText}>
						Recommended: 1080p at 30fps or higher
					</Text>
				</View>
			</View>

			{/* Video Selection Buttons */}
			<View style={styles.buttonContainer}>
				<TouchableOpacity
					style={styles.button}
					onPress={pickVideo}
					disabled={isUploading}
					activeOpacity={0.7}
				>
					<LinearGradient
						colors={[SHOOTRZ_THEME.colors.primary, SHOOTRZ_THEME.colors.secondary]}
						style={styles.buttonGradient}
					>
						<Ionicons name="film-outline" size={24} color="#fff" />
						<Text style={styles.buttonText}>Select Video</Text>
					</LinearGradient>
				</TouchableOpacity>

				<TouchableOpacity
					style={styles.button}
					onPress={() => {
						if (onRecordVideo) {
							onRecordVideo() // Use full camera recorder if available
						} else {
							recordVideo() // Fallback to ImagePicker
						}
					}}
					disabled={isUploading}
					activeOpacity={0.7}
				>
					<LinearGradient
						colors={[SHOOTRZ_THEME.colors.secondary, SHOOTRZ_THEME.colors.primary]}
						style={styles.buttonGradient}
					>
						<Ionicons name="videocam" size={24} color="#fff" />
						<Text style={styles.buttonText}>Record Video</Text>
					</LinearGradient>
				</TouchableOpacity>
			</View>

			{/* Selected Video Indicator */}
			{selectedVideo && (
				<View style={styles.selectedContainer}>
					<Ionicons name="checkmark-circle" size={20} color={SHOOTRZ_THEME.colors.success} />
					<Text style={styles.selectedText}>Video selected</Text>
				</View>
			)}

			{/* Upload Progress */}
			{isUploading && (
				<View style={styles.progressContainer}>
					<ActivityIndicator size="large" color={SHOOTRZ_THEME.colors.primary} />
					<Text style={styles.progressText}>
						Uploading and analyzing... {Math.round(uploadProgress * 100)}%
					</Text>
				</View>
			)}

			{/* Analyze Button */}
			{selectedVideo && !isUploading && (
				<TouchableOpacity
					style={styles.analyzeButton}
					onPress={uploadAndAnalyze}
					activeOpacity={0.7}
				>
					<LinearGradient
						colors={[SHOOTRZ_THEME.colors.accent, SHOOTRZ_THEME.colors.primary]}
						style={styles.analyzeButtonGradient}
					>
						<Ionicons name="analytics-outline" size={24} color="#fff" />
						<Text style={styles.analyzeButtonText}>Analyze Shot</Text>
					</LinearGradient>
				</TouchableOpacity>
			)}
		</ScrollView>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: SHOOTRZ_THEME.colors.background,
	},
	content: {
		padding: 20,
	},
	guidelinesContainer: {
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: 12,
		padding: 16,
		marginBottom: 24,
	},
	guidelinesTitle: {
		fontSize: 18,
		fontWeight: 'bold',
		color: SHOOTRZ_THEME.colors.text,
		marginBottom: 12,
	},
	guidelineItem: {
		flexDirection: 'row',
		alignItems: 'center',
		marginBottom: 8,
	},
	guidelineText: {
		fontSize: 14,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginLeft: 12,
		flex: 1,
	},
	buttonContainer: {
		gap: 16,
		marginBottom: 20,
	},
	button: {
		borderRadius: 12,
		overflow: 'hidden',
		shadowColor: '#000',
		shadowOffset: { width: 0, height: 2 },
		shadowOpacity: 0.1,
		shadowRadius: 4,
		elevation: 3,
	},
	buttonGradient: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		padding: 16,
		gap: 8,
	},
	buttonText: {
		fontSize: 16,
		fontWeight: '600',
		color: '#fff',
	},
	selectedContainer: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		padding: 12,
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: 8,
		marginBottom: 16,
	},
	selectedText: {
		fontSize: 14,
		color: SHOOTRZ_THEME.colors.success,
		marginLeft: 8,
		fontWeight: '500',
	},
	progressContainer: {
		alignItems: 'center',
		padding: 20,
	},
	progressText: {
		marginTop: 12,
		fontSize: 14,
		color: SHOOTRZ_THEME.colors.textSecondary,
	},
	analyzeButton: {
		borderRadius: 12,
		overflow: 'hidden',
		marginTop: 8,
		shadowColor: '#000',
		shadowOffset: { width: 0, height: 4 },
		shadowOpacity: 0.2,
		shadowRadius: 6,
		elevation: 5,
	},
	analyzeButtonGradient: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		padding: 18,
		gap: 8,
	},
	analyzeButtonText: {
		fontSize: 18,
		fontWeight: 'bold',
		color: '#fff',
	},
})
