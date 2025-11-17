import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Animated,
  ColorValue,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import { ProgressRing } from '../components/ProgressRing';
import { LoadingBasketball } from '../components/LoadingBasketball';
import { GradientCard } from '../components/GradientCard';
import { CameraRecorder } from '../components/CameraRecorder';
import { MetricCard } from '../components/MetricCard';
import { MetricSection } from '../components/MetricSection';
import { FeedbackCategoryPanel } from '../components/FeedbackCategoryPanel';
import { AnnotatedVideoPlayer } from '../components/AnnotatedVideoPlayer';
import { TechnicalDetailCard } from '../components/TechnicalDetailCard';
import { apiService, AnalysisResponse } from '../services/api.service';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { storageService, AnalysisResult } from '../services/storage.service';
import { useAuth } from '../context/AuthContext';
import * as ScoreCalculator from '../utils/scoreCalculator';
import { Ionicons } from '@expo/vector-icons';
import { hapticFeedback } from '../utils/hapticFeedback';

export const AnalyzeScreen: React.FC = () => {
  const { user } = useAuth();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedVideoUri, setSelectedVideoUri] = useState<string | null>(null);
  const [annotatedVideoId, setAnnotatedVideoId] = useState<string | null>(null);
  const [apiHealth, setApiHealth] = useState<boolean | null>(null);
  const [videoAspectRatio, setVideoAspectRatio] = useState<number>(16 / 9);
  const [videoOrientation, setVideoOrientation] = useState<'landscape' | 'portrait' | 'square'>(
    'landscape'
  );
  const [showCameraRecorder, setShowCameraRecorder] = useState(false);
  const [latestResultResponse, setLatestResultResponse] = useState<any>(null);
  
  // Add ref to track last request for deduplication
  const lastRequestRef = useRef<string | null>(null);

  // Check API health on component mount
  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const isHealthy = await apiService.checkHealth();
        setApiHealth(isHealthy);
        // Health check is optional - don't log errors if backend is just not running
        if (!isHealthy && __DEV__) {
          console.log('⚠️ Backend health check failed (backend may not be running)');
        }
      } catch (error: any) {
        // Fail silently - health check is optional
        // Network errors are expected and already handled in the service
        setApiHealth(false);
        // Don't log network errors - they're expected if backend is unavailable
      }
    };

    checkApiHealth();
  }, []);

  // Log analysis result for debugging if needed
  useEffect(() => {
    if (analysisResult && __DEV__) {
      console.log('Analysis completed:', {
        score: analysisResult.scores?.total,
        metrics: analysisResult.metrics,
      });
    }
  }, [analysisResult]);

  const pickVideo = async () => {
    try {
      // Request permissions
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();

      if (status !== 'granted') {
        Alert.alert('Permission Required', 'Camera roll access is required to select videos');
        return;
      }

      // Launch image picker for videos
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: 'videos', // Use lowercase string as required by new API
        allowsEditing: false,  // CHANGED from true to prevent duplicate URIs
        quality: 1,
        videoMaxDuration: 30,
      });

      if (!result.canceled && result.assets[0]) {
        setSelectedVideoUri(result.assets[0].uri);
        await handleAnalyzeVideo(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Error picking video:', error);
      Alert.alert('Error', 'Failed to select video. Please try again.');
    }
  };

  const recordVideo = () => {
    // Show full camera recorder
    setShowCameraRecorder(true);
    hapticFeedback.medium();
  };

  const handleVideoRecorded = async (videoUri: string) => {
    setShowCameraRecorder(false);
    setSelectedVideoUri(videoUri);
    await handleAnalyzeVideo(videoUri);
  };

  const handleCameraCancel = () => {
    setShowCameraRecorder(false);
  };

  const handleAnalyzeVideo = async (videoUri: string) => {
    // Prevent duplicate requests for same video
    if (isAnalyzing || lastRequestRef.current === videoUri) {
      console.log('Duplicate request prevented:', videoUri);
      return;
    }
    
    lastRequestRef.current = videoUri;
    setIsAnalyzing(true);
    
    // Clear any cached analysis results
    setAnalysisResult(null);
    setAnnotatedVideoId(null);

    try {
      // Validate video file
      const validation = apiService.validateVideoFile(videoUri);
      if (!validation.valid) {
        Alert.alert('Invalid Video', validation.message);
        return;
      }

      // Check API health before processing
      if (apiHealth === false) {
        Alert.alert(
          'Service Unavailable',
          'The analysis service is currently unavailable. Please try again later.'
        );
        return;
      }

      // Call FastAPI backend for analysis
      const uploadResponse = await apiService.analyzeVideo(videoUri);

      if (uploadResponse.job_id) {
        // Poll for results using the job_id
        let pollCount = 0
        const maxPolls = 60 // 60 seconds timeout
        
        while (pollCount < maxPolls) {
          await new Promise(resolve => setTimeout(resolve, 1000)) // Wait 1 second
          
          const resultResponse = await apiService.getResult(uploadResponse.job_id)
          setLatestResultResponse(resultResponse)
          
          if (resultResponse.status === 'completed') {
            // Transform FastAPI response to AnalyzeScreen format
            const metrics = resultResponse.metrics || []
            const feedback = resultResponse.feedback || []
            
            // Calculate normalized scores using utility functions
            const {
              calculateElbowPositionScore,
              calculateReleaseHeightScore,
              calculateKneeAlignmentScore,
              calculateArcHeightScore,
              calculateEntryAngleScore,
              calculateGripScore,
              calculateFollowThroughScore,
              calculateElbowScore,
              calculateKneeScore,
              calculateReleaseScore,
              calculateAlignmentScore,
              calculateComprehensiveTotalScore,
            } = ScoreCalculator
            
            // Extract metric values for display
            const getMetricValue = (name: string, fallbackNames: string[] = []) => {
              let metric = metrics.find((m: any) => m.metric_name === name)
              if (!metric && fallbackNames.length > 0) {
                for (const fallback of fallbackNames) {
                  metric = metrics.find((m: any) => m.metric_name === fallback)
                  if (metric) break
                }
              }
              return metric
            }
            
            // Get shot distance for context-aware scoring
            const releaseAngleMetric = getMetricValue('release_angle')
            const shotDistance = releaseAngleMetric?.shot_distance
            
            // Calculate all scores
            const elbowPositionScore = calculateElbowPositionScore(metrics)
            const releaseHeightScore = calculateReleaseHeightScore(metrics)
            const kneeAlignmentScore = calculateKneeAlignmentScore(metrics)
            const arcHeightScore = calculateArcHeightScore(metrics, shotDistance)
            const entryAngleScore = calculateEntryAngleScore(metrics)
            const gripScore = calculateGripScore(metrics)
            const followThroughScore = calculateFollowThroughScore(metrics)
            
            // Legacy scores for backward compatibility
            const elbowScore = calculateElbowScore(metrics)
            const kneeScore = calculateKneeScore(metrics)
            const releaseScore = calculateReleaseScore(metrics)
            const alignmentScore = calculateAlignmentScore(metrics)
            
            // Calculate comprehensive total score
            const totalScore = calculateComprehensiveTotalScore(
              {
                elbowPosition: elbowPositionScore,
                releaseHeight: releaseHeightScore,
                kneeAlignment: kneeAlignmentScore,
                arcHeight: arcHeightScore,
                entryAngle: entryAngleScore,
              },
              {
                grip: gripScore,
                followThrough: followThroughScore,
              }
            )
            
            console.log('📊 Calculated scores:', {
              elbowPosition: elbowPositionScore,
              releaseHeight: releaseHeightScore,
              kneeAlignment: kneeAlignmentScore,
              arcHeight: arcHeightScore,
              entryAngle: entryAngleScore,
              grip: gripScore,
              followThrough: followThroughScore,
              total: totalScore,
            })
            
            // Organize feedback by category
            const formIssues: any[] = []
            const techniqueTips: any[] = []
            const strengths: any[] = []
            
            feedback.forEach((fb: any) => {
              const severity = fb.severity || 'info'
              const message = fb.message || fb
              
              if (severity === 'critical' || severity === 'warning') {
                formIssues.push({ ...fb, message, severity })
              } else if (severity === 'info') {
                techniqueTips.push({ ...fb, message, severity })
              } else {
                strengths.push({ ...fb, message, severity })
              }
            })
            
            setAnalysisResult({
              scores: {
                elbow: elbowScore,
                balance: kneeScore,
                release: releaseScore,
                alignment: alignmentScore,
                total: totalScore,
              },
              metrics: {
                elbowPosition: getMetricValue('forearm_verticality'),
                releaseHeight: getMetricValue('elbow_height'),
                kneeAlignment: getMetricValue('knee_flexion'),
                hipAlignment: getMetricValue('hip_flexion'),
                arcHeight: getMetricValue('arc_height'),
                entryAngle: getMetricValue('entry_angle'),
                gripQuality: getMetricValue('grip_quality'),
                followThrough: getMetricValue('wrist_angular_velocity'),
                releaseAngle: releaseAngleMetric,
                shotDistance: shotDistance,
              },
              scoresDetailed: {
                elbowPosition: elbowPositionScore,
                releaseHeight: releaseHeightScore,
                kneeAlignment: kneeAlignmentScore,
                arcHeight: arcHeightScore,
                entryAngle: entryAngleScore,
                grip: gripScore,
                followThrough: followThroughScore,
              },
              feedback: feedback.map((f: any) => f.message || f),
              feedbackCategorized: {
                formIssues,
                techniqueTips,
                strengths,
              },
              phases: resultResponse.phases || [],
              poseResults: resultResponse.pose_results || 0,
              performanceLevel: totalScore > 80 ? 'Advanced' : totalScore > 50 ? 'Intermediate' : 'Beginner',
              processingStats: {},
            })

            // Keep original video URI for playback (annotated video generation coming soon)
            // setAnnotatedVideoId(uploadResponse.job_id)

            // Save to storage
            await saveAnalysisResult({
              id: uploadResponse.job_id,
              userId: user?.id || 'guest',
              timestamp: new Date().toISOString(),
              scores: {
                elbow: elbowScore,
                balance: kneeScore,
                release: releaseScore,
                alignment: alignmentScore,
                total: totalScore,
              },
              feedback: feedback.map((f: any) => f.message || f),
              angles: {
                elbow: getMetricValue('elbow_flexion_release', ['elbow_flexion_crouch'])?.value || 0,
                knee: getMetricValue('knee_flexion')?.value || 0,
                release: getMetricValue('release_angle')?.value || 0,
                bodyAlignment: getMetricValue('body_alignment', ['shoulder_alignment'])?.value || 0,
              },
            })

            hapticFeedback.success()
            return // Success, exit polling loop
          }
          
          if (resultResponse.status === 'failed' || resultResponse.status === 'error') {
            throw new Error(resultResponse.error || 'Analysis failed')
          }
          
          pollCount++
        }
        
        // Timeout
        throw new Error('Analysis timed out. Please try again.')
      } else {
        throw new Error('Failed to start analysis')
      }
    } catch (error: any) {
      console.error('Analysis error:', error);
      hapticFeedback.error();
      Alert.alert('Analysis Failed', error.message || 'Failed to analyze video. Please try again.');
    } finally {
      setIsAnalyzing(false);
      // Clear after delay to allow re-analysis
      setTimeout(() => {
        lastRequestRef.current = null;
      }, 5000);
    }
  };

  const saveAnalysisResult = async (analysis: any) => {
    try {
      const result: AnalysisResult = {
        id: Date.now().toString(),
        userId: user?.id || 'guest',
        timestamp: new Date().toISOString(),
        scores: {
          elbow: analysis.scores.elbow,
          balance: analysis.scores.balance,
          release: analysis.scores.release,
          alignment: analysis.scores.alignment,
          total: analysis.scores.total,
        },
        feedback: analysis.feedback,
        angles: {
          elbow: analysis.elbowAngle,
          knee: analysis.kneeAngle,
          release: analysis.releaseAngle,
          bodyAlignment: analysis.bodyAlignment,
        },
      };

      await storageService.saveAnalysisResult(result);
    } catch (error) {
      console.error('Error saving analysis:', error);
      // Don't alert user - this is a background operation
    }
  };


  // Show camera recorder overlay
  if (showCameraRecorder) {
    return (
      <CameraRecorder
        onVideoRecorded={handleVideoRecorded}
        onCancel={handleCameraCancel}
        maxDuration={30}
      />
    )
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <LinearGradient
        colors={[
          SHOOTRZ_THEME.colors.background,
          SHOOTRZ_THEME.colors.surface,
          SHOOTRZ_THEME.colors.background,
        ]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.backgroundGradient}
      >
        <ScrollView 
          style={styles.scrollView}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
        >
          <View style={styles.header}>
          <View style={styles.headerContent}>
            <View style={styles.headerIconContainer}>
              <Ionicons name="analytics" size={28} color={SHOOTRZ_THEME.colors.primary} />
            </View>
            <View style={styles.headerTextContainer}>
              <Text style={styles.title}>Comprehensive Shot Analysis</Text>
              <Text style={styles.subtitle}>
                AI-powered biomechanics analysis with detailed metrics and feedback
              </Text>
            </View>
          </View>
        </View>

        {!analysisResult ? (
          <View style={styles.recordingSection}>
            <View style={styles.placeholder}>
              <View style={styles.placeholderIconContainer}>
                <Ionicons name="analytics" size={64} color={SHOOTRZ_THEME.colors.primary} />
                <View style={styles.iconGlow} />
              </View>
              <Text style={styles.placeholderTitle}>Comprehensive Shot Analysis</Text>
              <Text style={styles.placeholderText}>
                Record your shot to get AI-powered biomechanics analysis including:
              </Text>
              <View style={styles.featuresList}>
                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={18} color={SHOOTRZ_THEME.colors.success} />
                  <Text style={styles.featureText}>Elbow position & release height</Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={18} color={SHOOTRZ_THEME.colors.success} />
                  <Text style={styles.featureText}>Knee-to-toe alignment analysis</Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={18} color={SHOOTRZ_THEME.colors.success} />
                  <Text style={styles.featureText}>Ball trajectory & arc height</Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={18} color={SHOOTRZ_THEME.colors.success} />
                  <Text style={styles.featureText}>Grip & follow-through analysis</Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="checkmark-circle" size={18} color={SHOOTRZ_THEME.colors.success} />
                  <Text style={styles.featureText}>Personalized coaching feedback</Text>
                </View>
              </View>

              {isAnalyzing ? (
                <LoadingBasketball message="Analyzing your form..." size="large" />
              ) : (
                <View style={styles.actionButtonsContainer}>
                  <TouchableOpacity
                    onPress={recordVideo}
                    style={styles.actionButton}
                    activeOpacity={0.8}
                  >
                    <LinearGradient
                      colors={[SHOOTRZ_THEME.colors.primary, SHOOTRZ_THEME.colors.primaryDark]}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                      style={styles.actionButtonGradient}
                    >
                      <View style={styles.actionButtonContent}>
                        <View style={styles.actionButtonIconContainer}>
                          <Ionicons
                            name="videocam"
                            size={24}
                            color="#fff"
                          />
                        </View>
                        <View style={styles.actionButtonTextContainer}>
                          <Text style={styles.actionButtonTitle}>Record Video</Text>
                          <Text style={styles.actionButtonSubtitle}>Use camera to record</Text>
                        </View>
                        <Ionicons
                          name="chevron-forward"
                          size={20}
                          color="#fff"
                          style={{ opacity: 0.7 }}
                        />
                      </View>
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    onPress={pickVideo}
                    style={styles.actionButton}
                    activeOpacity={0.8}
                  >
                    <LinearGradient
                      colors={[SHOOTRZ_THEME.colors.secondary, SHOOTRZ_THEME.colors.secondaryDark]}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                      style={styles.actionButtonGradient}
                    >
                      <View style={styles.actionButtonContent}>
                        <View style={styles.actionButtonIconContainer}>
                          <Ionicons
                            name="cloud-upload"
                            size={24}
                            color="#fff"
                          />
                        </View>
                        <View style={styles.actionButtonTextContainer}>
                          <Text style={styles.actionButtonTitle}>Upload Video</Text>
                          <Text style={styles.actionButtonSubtitle}>Select from gallery</Text>
                        </View>
                        <Ionicons
                          name="chevron-forward"
                          size={20}
                          color="#fff"
                          style={{ opacity: 0.7 }}
                        />
                      </View>
                    </LinearGradient>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          </View>
        ) : (
          <View style={styles.resultsSection}>
            {/* Overall Score with Progress Ring */}
            <View style={styles.totalScoreCardWrapper}>
              <LinearGradient
                colors={[
                  SHOOTRZ_THEME.colors.surface,
                  SHOOTRZ_THEME.colors.surfaceElevated,
                  SHOOTRZ_THEME.colors.surface,
                ]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.totalScoreCard}
              >
                <View style={styles.scoreCardHeader}>
                  <Ionicons 
                    name="trophy" 
                    size={24} 
                    color={
                      analysisResult.scores.total >= 80
                        ? SHOOTRZ_THEME.colors.secondary
                        : analysisResult.scores.total >= 60
                          ? SHOOTRZ_THEME.colors.primary
                          : SHOOTRZ_THEME.colors.warning
                    } 
                  />
                  <Text style={styles.totalScoreLabel}>Overall Performance Score</Text>
                </View>
                <View style={styles.progressRingContainer}>
                  <ProgressRing
                    progress={analysisResult.scores.total}
                    size={160}
                    strokeWidth={14}
                    color={
                      analysisResult.scores.total >= 80
                        ? SHOOTRZ_THEME.colors.secondary
                        : analysisResult.scores.total >= 60
                          ? SHOOTRZ_THEME.colors.primary
                          : SHOOTRZ_THEME.colors.warning
                    }
                    showPercentage={true}
                  />
                </View>
                <View style={styles.scoreDetails}>
                  <Text style={styles.scoreRating}>
                    {analysisResult.scores.total >= 90
                      ? 'Excellent! 🏆'
                      : analysisResult.scores.total >= 80
                        ? 'Great Form! ⭐'
                        : analysisResult.scores.total >= 60
                          ? 'Good Work! 👍'
                          : 'Keep Practicing! 💪'}
                  </Text>
                  <Text style={styles.performanceLevel}>
                    {analysisResult.performanceLevel}
                  </Text>
                </View>
              </LinearGradient>
            </View>

            {/* Section 2: Annotated Video Display */}
            {latestResultResponse?.annotated_video_url && (
              <View style={styles.videoSection}>
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionHeaderLeft}>
                    <View style={styles.sectionIconContainer}>
                      <Ionicons name="videocam" size={20} color={SHOOTRZ_THEME.colors.primary} />
                    </View>
                    <Text style={styles.sectionHeaderTitle}>Annotated Video Analysis</Text>
                  </View>
                </View>
                <AnnotatedVideoPlayer
                  videoUri={latestResultResponse.annotated_video_url}
                  annotatedVideoUri={latestResultResponse.annotated_video_url}
                  poseResults={undefined} // Will be populated when backend returns full pose data
                  ballTrajectory={undefined} // Will be populated when backend returns trajectory data
                  phases={analysisResult.phases}
                />
              </View>
            )}

            {/* Section 3: Core Shooting Metrics */}
            <View style={styles.metricsSectionWrapper}>
              <View style={styles.sectionHeader}>
                <View style={styles.sectionHeaderLeft}>
                  <View style={styles.sectionIconContainer}>
                    <Ionicons name="analytics" size={20} color={SHOOTRZ_THEME.colors.secondary} />
                  </View>
                  <Text style={styles.sectionHeaderTitle}>Core Shooting Metrics</Text>
                </View>
              </View>
              <MetricSection
              title=""
              metrics={[
                {
                  title: 'Elbow Position',
                  description: 'Vertical alignment of forearm at release',
                  value: analysisResult.metrics?.elbowPosition?.value || 0,
                  unit: analysisResult.metrics?.elbowPosition?.unit || 'degrees',
                  optimalRange: [0, 8] as [number, number],
                  score: analysisResult.scoresDetailed?.elbowPosition,
                  confidence: analysisResult.metrics?.elbowPosition?.confidence,
                  color: SHOOTRZ_THEME.colors.primary,
                  icon: 'body',
                },
                {
                  title: 'Release Height',
                  description: 'Elbow height relative to eyes at release',
                  value: analysisResult.metrics?.releaseHeight?.value || 0,
                  unit: analysisResult.metrics?.releaseHeight?.unit || 'cm',
                  optimalRange: [147, 153] as [number, number],
                  score: analysisResult.scoresDetailed?.releaseHeight,
                  confidence: analysisResult.metrics?.releaseHeight?.confidence,
                  color: SHOOTRZ_THEME.colors.secondary,
                  icon: 'arrow-up',
                },
                {
                  title: 'Knee-to-Toe Alignment',
                  description: 'Lower body alignment and load posture',
                  value: analysisResult.metrics?.kneeAlignment?.value || 0,
                  unit: analysisResult.metrics?.kneeAlignment?.unit || 'degrees',
                  optimalRange: [105, 115] as [number, number],
                  score: analysisResult.scoresDetailed?.kneeAlignment,
                  confidence: analysisResult.metrics?.kneeAlignment?.confidence,
                  color: SHOOTRZ_THEME.colors.accent,
                  icon: 'footsteps',
                },
                {
                  title: 'Arc Height',
                  description: 'Maximum height of ball trajectory',
                  value: analysisResult.metrics?.arcHeight?.value || 0,
                  unit: analysisResult.metrics?.arcHeight?.unit || 'meters',
                  optimalRange: [3.8, 4.0] as [number, number],
                  score: analysisResult.scoresDetailed?.arcHeight,
                  confidence: analysisResult.metrics?.arcHeight?.confidence,
                  color: SHOOTRZ_THEME.colors.primaryLight,
                  icon: 'trending-up',
                },
                {
                  title: 'Entry Angle',
                  description: 'Angle at which ball enters the basket',
                  value: analysisResult.metrics?.entryAngle?.value || 0,
                  unit: analysisResult.metrics?.entryAngle?.unit || 'degrees',
                  optimalRange: [48, 52] as [number, number],
                  score: analysisResult.scoresDetailed?.entryAngle,
                  confidence: analysisResult.metrics?.entryAngle?.confidence,
                  color: SHOOTRZ_THEME.colors.secondaryLight,
                  icon: 'analytics',
                },
                {
                  title: 'Player Location',
                  description: 'Position on court (coming soon)',
                  value: 0,
                  unit: 'N/A',
                  optimalRange: undefined,
                  score: undefined,
                  confidence: undefined,
                  color: SHOOTRZ_THEME.colors.textSecondary,
                  icon: 'location',
                  showScore: false,
                },
              ]}
                layout="grid"
                numColumns={2}
              />
            </View>

            {/* Section 4: Technical Details */}
            <View style={styles.technicalSection}>
              <View style={styles.sectionHeader}>
                <View style={styles.sectionHeaderLeft}>
                  <View style={styles.sectionIconContainer}>
                    <Ionicons name="construct" size={20} color={SHOOTRZ_THEME.colors.accent} />
                  </View>
                  <Text style={styles.sectionHeaderTitle}>Technical Details</Text>
                </View>
              </View>
              
              {analysisResult.metrics?.gripQuality && (
                <TechnicalDetailCard
                  title="Grip Analysis"
                  icon="hand-left"
                  color={SHOOTRZ_THEME.colors.primary}
                  score={analysisResult.scoresDetailed?.grip ? (analysisResult.scoresDetailed.grip / 25) * 100 : undefined}
                  description="Ball position and grip quality"
                  details={[
                    {
                      label: 'Grip Quality Score',
                      value: analysisResult.metrics.gripQuality.value || 0,
                      unit: 'score',
                    },
                    {
                      label: 'Thumb-Index Distance',
                      value: 'Optimal',
                      unit: '',
                    },
                    {
                      label: 'Ball Position',
                      value: 'Centered',
                      unit: '',
                    },
                  ]}
                />
              )}

              {analysisResult.metrics?.followThrough && (
                <TechnicalDetailCard
                  title="Follow-Through Analysis"
                  icon="flash"
                  color={SHOOTRZ_THEME.colors.accent}
                  score={analysisResult.scoresDetailed?.followThrough ? (analysisResult.scoresDetailed.followThrough / 25) * 100 : undefined}
                  description="Wrist velocity and consistency"
                  details={[
                    {
                      label: 'Wrist Angular Velocity',
                      value: analysisResult.metrics.followThrough.value || 0,
                      unit: analysisResult.metrics.followThrough.unit || 'rad/s',
                    },
                    {
                      label: 'Duration',
                      value: 'Optimal',
                      unit: '',
                    },
                    {
                      label: 'Consistency',
                      value: 'Good',
                      unit: '',
                    },
                  ]}
                />
              )}
            </View>

            {/* Section 5: Detailed Feedback Panel */}
            <View style={styles.feedbackSection}>
              <View style={styles.sectionHeader}>
                <View style={styles.sectionHeaderLeft}>
                  <View style={styles.sectionIconContainer}>
                    <Ionicons name="bulb" size={20} color={SHOOTRZ_THEME.colors.warning} />
                  </View>
                  <Text style={styles.sectionHeaderTitle}>Coaching Feedback</Text>
                </View>
              </View>
              
              {analysisResult.feedbackCategorized?.formIssues &&
                analysisResult.feedbackCategorized.formIssues.length > 0 && (
                  <FeedbackCategoryPanel
                    category="Form Issues"
                    feedbackItems={analysisResult.feedbackCategorized.formIssues}
                    icon="warning"
                    color={SHOOTRZ_THEME.colors.error}
                  />
                )}
              
              {analysisResult.feedbackCategorized?.techniqueTips &&
                analysisResult.feedbackCategorized.techniqueTips.length > 0 && (
                  <FeedbackCategoryPanel
                    category="Technique Tips"
                    feedbackItems={analysisResult.feedbackCategorized.techniqueTips}
                    icon="bulb"
                    color={SHOOTRZ_THEME.colors.accent}
                  />
                )}
              
              {analysisResult.feedbackCategorized?.strengths &&
                analysisResult.feedbackCategorized.strengths.length > 0 && (
                  <FeedbackCategoryPanel
                    category="Strengths"
                    feedbackItems={analysisResult.feedbackCategorized.strengths}
                    icon="trophy"
                    color={SHOOTRZ_THEME.colors.success}
                  />
                )}
            </View>

            <LinearGradient
              colors={
                SHOOTRZ_THEME.gradients.primary as unknown as [
                  ColorValue,
                  ColorValue,
                  ...ColorValue[],
                ]
              }
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.analyzeAgainButton}
            >
              <TouchableOpacity
                onPress={() => setAnalysisResult(null)}
                style={styles.analyzeAgainButtonInner}
              >
                <Ionicons
                  name="refresh"
                  size={20}
                  color={SHOOTRZ_THEME.colors.textPrimary}
                  style={{ marginRight: 8 }}
                />
                <Text style={styles.analyzeAgainText}>Analyze Another Shot</Text>
              </TouchableOpacity>
            </LinearGradient>
          </View>
        )}
        </ScrollView>
      </LinearGradient>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
  },
  backgroundGradient: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: SHOOTRZ_THEME.spacing.xxl,
  },
  header: {
    padding: SHOOTRZ_THEME.spacing.lg,
    paddingTop: SHOOTRZ_THEME.spacing.xl,
    paddingBottom: SHOOTRZ_THEME.spacing.xl,
    backgroundColor: SHOOTRZ_THEME.colors.surface + 'F0',
    borderBottomWidth: 2,
    borderBottomColor: SHOOTRZ_THEME.colors.primary + '30',
    shadowColor: SHOOTRZ_THEME.colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: SHOOTRZ_THEME.colors.primary + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  headerTextContainer: {
    flex: 1,
  },
  title: {
    ...SHOOTRZ_THEME.typography.heading2,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
    fontSize: 22,
  },
  subtitle: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
    fontSize: 13,
    lineHeight: 18,
  },
  recordingSection: {
    flex: 1,
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  placeholder: {
    flex: 1,
    ...COMPONENT_STYLES.card,
    padding: SHOOTRZ_THEME.spacing.xxl,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderIconContainer: {
    position: 'relative',
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  iconGlow: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -32 }, { translateY: -32 }],
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: SHOOTRZ_THEME.colors.primary,
    opacity: 0.2,
    shadowColor: SHOOTRZ_THEME.colors.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
  },
  placeholderTitle: {
    ...SHOOTRZ_THEME.typography.heading2,
    marginBottom: SHOOTRZ_THEME.spacing.md,
    textAlign: 'center',
  },
  placeholderText: {
    ...SHOOTRZ_THEME.typography.body,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.lg,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  featuresList: {
    width: '100%',
    marginTop: SHOOTRZ_THEME.spacing.md,
    alignItems: 'flex-start',
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
    width: '100%',
  },
  featureText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    marginLeft: SHOOTRZ_THEME.spacing.sm,
    color: SHOOTRZ_THEME.colors.textPrimary,
    flex: 1,
  },
  actionButtonsContainer: {
    width: '100%',
    gap: SHOOTRZ_THEME.spacing.md,
    marginTop: SHOOTRZ_THEME.spacing.xl,
  },
  actionButton: {
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 6,
  },
  actionButtonGradient: {
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  actionButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  actionButtonIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  actionButtonTextContainer: {
    flex: 1,
  },
  actionButtonTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  actionButtonSubtitle: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 13,
  },
  resultsSection: {
    padding: SHOOTRZ_THEME.spacing.lg,
    paddingTop: SHOOTRZ_THEME.spacing.xl,
  },
  totalScoreCardWrapper: {
    marginBottom: SHOOTRZ_THEME.spacing.xl,
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  totalScoreCard: {
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.xxl,
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
    borderWidth: 2,
    borderColor: SHOOTRZ_THEME.colors.primary + '40',
  },
  scoreCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  totalScoreLabel: {
    ...SHOOTRZ_THEME.typography.heading3,
    color: SHOOTRZ_THEME.colors.textPrimary,
    marginLeft: SHOOTRZ_THEME.spacing.sm,
    fontWeight: '700',
  },
  progressRingContainer: {
    marginVertical: SHOOTRZ_THEME.spacing.lg,
  },
  scoreDetails: {
    alignItems: 'center',
    marginTop: SHOOTRZ_THEME.spacing.md,
  },
  scoreRating: {
    ...SHOOTRZ_THEME.typography.heading2,
    fontSize: 22,
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontWeight: '700',
    marginBottom: SHOOTRZ_THEME.spacing.xs,
    textAlign: 'center',
  },
  performanceLevel: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    fontSize: 14,
    textTransform: 'uppercase',
    letterSpacing: 1,
    fontWeight: '600',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
    marginTop: SHOOTRZ_THEME.spacing.lg,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  sectionIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: SHOOTRZ_THEME.colors.primary + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SHOOTRZ_THEME.spacing.sm,
  },
  sectionHeaderTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    fontSize: 20,
    fontWeight: '700',
  },
  metricsSectionWrapper: {
    marginTop: SHOOTRZ_THEME.spacing.md,
    marginBottom: SHOOTRZ_THEME.spacing.lg,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
  },
  sectionTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
    marginTop: SHOOTRZ_THEME.spacing.sm,
  },
  sectionTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
  },
  feedbackSection: {
    marginTop: SHOOTRZ_THEME.spacing.xl,
    marginBottom: SHOOTRZ_THEME.spacing.lg,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
  },
  technicalSection: {
    marginTop: SHOOTRZ_THEME.spacing.xl,
    marginBottom: SHOOTRZ_THEME.spacing.lg,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
  },
  feedbackItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  feedbackIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: SHOOTRZ_THEME.colors.secondary + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: SHOOTRZ_THEME.spacing.md,
  },
  feedbackText: {
    flex: 1,
    ...SHOOTRZ_THEME.typography.body,
    lineHeight: 22,
  },
  angleDetails: {
    marginTop: SHOOTRZ_THEME.spacing.lg,
  },
  angleGrid: {
    flexDirection: 'column',
    gap: SHOOTRZ_THEME.spacing.md,
    alignItems: 'center',
  },
  angleRow: {
    flexDirection: 'row',
    gap: SHOOTRZ_THEME.spacing.md,
    width: '100%',
    justifyContent: 'center',
  },
  angleItem: {
    flex: 1,
    aspectRatio: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.lg,
    maxWidth: 160,
    minWidth: 160,
  },
  angleLabel: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
    textAlign: 'center',
    fontSize: 16,
    lineHeight: 20,
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  angleValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: SHOOTRZ_THEME.colors.primary,
  },
  analyzeAgainButton: {
    marginTop: SHOOTRZ_THEME.spacing.xl,
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
    overflow: 'hidden',
  },
  analyzeAgainButtonInner: {
    flexDirection: 'row',
    paddingHorizontal: SHOOTRZ_THEME.spacing.xl,
    paddingVertical: SHOOTRZ_THEME.spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  analyzeAgainText: {
    ...SHOOTRZ_THEME.typography.button,
    fontSize: 16,
  },
  videoSection: {
    marginTop: SHOOTRZ_THEME.spacing.lg,
    marginBottom: SHOOTRZ_THEME.spacing.xl,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
  },
  videoContainer: {
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
  },
  video: {
    width: '100%',
    // aspectRatio is set dynamically based on video orientation
  },
});
