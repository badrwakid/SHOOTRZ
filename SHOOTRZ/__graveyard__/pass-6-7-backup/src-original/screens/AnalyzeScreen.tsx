import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator, Animated, ColorValue } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Video, ResizeMode } from 'expo-av';
import * as ImagePicker from 'expo-image-picker';
import { AnimatedScoreCard } from '../components/AnimatedScoreCard';
import { ProgressRing } from '../components/ProgressRing';
import { LoadingBasketball } from '../components/LoadingBasketball';
import { GradientCard } from '../components/GradientCard';
import { apiService, AnalysisResponse } from '../services/api.service';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { storageService, AnalysisResult } from '../services/storage.service';
import { useAuth } from '../context/AuthContext';
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
  const [videoOrientation, setVideoOrientation] = useState<'landscape' | 'portrait' | 'square'>('landscape');

  // Check API health on component mount
  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        const isHealthy = await apiService.checkHealth();
        setApiHealth(isHealthy);
      } catch (error) {
        console.error('API health check failed:', error);
        setApiHealth(false);
      }
    };
    
    checkApiHealth();
  }, []);

  // Log analysis result for debugging if needed
  useEffect(() => {
    if (analysisResult && __DEV__) {
      console.log('Analysis completed:', {
        score: analysisResult.scores?.total,
        metrics: analysisResult.metrics
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
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        allowsEditing: true,
        quality: 1,
        videoMaxDuration: 30,
        aspect: [16, 9],
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

  const handleAnalyzeVideo = async (videoUri: string) => {
    setIsAnalyzing(true);
    
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

      // Call backend API for analysis
      const response: AnalysisResponse = await apiService.analyzeVideo(videoUri);
      
      if (response.success) {
        // Set analysis results
        
        setAnalysisResult({
          scores: {
            elbow: response.scores?.elbow || 0,
            balance: response.scores?.balance || 0,
            release: response.scores?.release || 0,
            alignment: response.scores?.alignment || 0,
            total: response.scores?.total || 0,
          },
          feedback: Array.isArray(response.tips) ? response.tips : [],
          elbowAngle: response.metrics?.elbow_angle || 0,
          kneeAngle: response.metrics?.knee_angle || 0,
          releaseAngle: response.metrics?.release_angle || 0,
          bodyAlignment: response.metrics?.body_alignment || 0,
          performanceLevel: response.performance_level || 'Unknown',
          processingStats: response.processing_stats || {},
        });
        
        setAnnotatedVideoId(response.video_id);
        
        // Save to storage
        await saveAnalysisResult({
          ...response,
          id: Date.now().toString(),
          userId: user?.id || 'guest',
          timestamp: response.timestamp,
          angles: {
            elbow: response.metrics.elbow_angle,
            knee: response.metrics.knee_angle,
            release: response.metrics.release_angle,
            bodyAlignment: response.metrics.body_alignment,
          },
        });
        
        hapticFeedback.success();
      } else {
        throw new Error('Analysis failed');
      }
    } catch (error: any) {
      console.error('Analysis error:', error);
      hapticFeedback.error();
      Alert.alert(
        'Analysis Failed', 
        error.message || 'Failed to analyze video. Please try again.'
      );
    } finally {
      setIsAnalyzing(false);
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

  const handleRecordVideo = () => {
    Alert.alert(
      'Record or Upload Video',
      'Choose a video from your library to analyze your shooting form.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Choose Video', onPress: pickVideo },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <ScrollView style={styles.scrollView}>
      <View style={styles.header}>
        <Text style={styles.title}>Shot Analysis</Text>
        <Text style={styles.subtitle}>Record your shot and get instant feedback</Text>
      </View>

      {!analysisResult ? (
        <View style={styles.recordingSection}>
          <View style={styles.placeholder}>
            <Ionicons name="videocam" size={64} color={SHOOTRZ_THEME.colors.primary} />
            <Text style={styles.placeholderTitle}>Record Your Shot</Text>
            <Text style={styles.placeholderText}>
              Position yourself in front of the camera and record your shooting form
            </Text>
            
            {isAnalyzing ? (
              <LoadingBasketball message="Analyzing your form..." size="large" />
            ) : (
              <LinearGradient
                colors={SHOOTRZ_THEME.gradients.primary as [ColorValue, ColorValue, ...ColorValue[]]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.recordButton}
              >
                <TouchableOpacity onPress={handleRecordVideo} style={styles.recordButtonInner}>
                  <Ionicons name="videocam" size={20} color={SHOOTRZ_THEME.colors.textPrimary} style={{ marginRight: 8 }} />
                  <Text style={styles.recordButtonText}>Record Video</Text>
                </TouchableOpacity>
              </LinearGradient>
            )}
          </View>
        </View>
      ) : (
        <View style={styles.resultsSection}>
          {/* Overall Score with Progress Ring */}
          <LinearGradient
            colors={[SHOOTRZ_THEME.colors.surface, SHOOTRZ_THEME.colors.surfaceElevated]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.totalScoreCard}
          >
            <Text style={styles.totalScoreLabel}>Overall Performance</Text>
            <ProgressRing
              progress={analysisResult.scores.total}
              size={140}
              strokeWidth={12}
              color={
                analysisResult.scores.total >= 80 ? SHOOTRZ_THEME.colors.secondary : 
                analysisResult.scores.total >= 60 ? SHOOTRZ_THEME.colors.primary : 
                SHOOTRZ_THEME.colors.warning
              }
              showPercentage={true}
            />
            <Text style={styles.scoreRating}>
              {analysisResult.scores.total >= 90 ? 'Excellent!' :
               analysisResult.scores.total >= 75 ? 'Great Form!' :
               analysisResult.scores.total >= 60 ? 'Good Work!' :
               'Keep Practicing!'}
            </Text>
          </LinearGradient>

          <Text style={styles.sectionTitle}>Detailed Analysis</Text>
          
          <AnimatedScoreCard
            title="Elbow Alignment"
            score={analysisResult.scores?.elbow || 0}
            maxScore={25}
            color={SHOOTRZ_THEME.colors.primary}
            delay={0}
          />
          
          <AnimatedScoreCard
            title="Balance & Stability"
            score={analysisResult.scores?.balance || 0}
            maxScore={25}
            color={SHOOTRZ_THEME.colors.secondary}
            delay={100}
          />
          
          <AnimatedScoreCard
            title="Release Angle"
            score={analysisResult.scores?.release || 0}
            maxScore={25}
            color={SHOOTRZ_THEME.colors.accent}
            delay={200}
          />
          
          <AnimatedScoreCard
            title="Body Alignment"
            score={analysisResult.scores?.alignment || 0}
            maxScore={25}
            color={SHOOTRZ_THEME.colors.primaryLight}
            delay={300}
          />

          <View style={styles.feedbackSection}>
            <View style={styles.sectionTitleContainer}>
              <Ionicons name="trophy" size={24} color={SHOOTRZ_THEME.colors.primary} style={{ marginRight: 8 }} />
              <Text style={styles.sectionTitle}>Coaching Feedback</Text>
            </View>
            {analysisResult.feedback.map((tip: string, index: number) => (
              <GradientCard key={index} style={styles.feedbackItem}>
                <View style={styles.feedbackIconContainer}>
                  <Ionicons name="bulb" size={20} color={SHOOTRZ_THEME.colors.accent} />
                </View>
                <Text style={styles.feedbackText}>{tip}</Text>
              </GradientCard>
            ))}
          </View>

          <View style={styles.angleDetails}>
            <View style={styles.sectionTitleContainer}>
              <Ionicons name="analytics" size={24} color={SHOOTRZ_THEME.colors.primary} style={{ marginRight: 8 }} />
              <Text style={styles.sectionTitle}>Measured Angles</Text>
            </View>
            <View style={styles.angleGrid}>
              <View style={styles.angleRow}>
                <GradientCard style={styles.angleItem}>
                  <Text style={styles.angleLabel}>Elbow Angle</Text>
                  <Text style={[styles.angleValue, { color: SHOOTRZ_THEME.colors.primary }]}>
                    {analysisResult.elbowAngle}°
                  </Text>
                </GradientCard>
                
                <GradientCard style={styles.angleItem}>
                  <Text style={styles.angleLabel}>Knee Angle</Text>
                  <Text style={[styles.angleValue, { color: SHOOTRZ_THEME.colors.secondary }]}>
                    {analysisResult.kneeAngle}°
                  </Text>
                </GradientCard>
              </View>
              
              <View style={styles.angleRow}>
                <GradientCard style={styles.angleItem}>
                  <Text style={styles.angleLabel}>Release Angle</Text>
                  <Text style={[styles.angleValue, { color: SHOOTRZ_THEME.colors.accent }]}>
                    {analysisResult.releaseAngle}°
                  </Text>
                </GradientCard>
                
                <GradientCard style={styles.angleItem}>
                  <Text style={styles.angleLabel}>Body Alignment</Text>
                  <Text style={[styles.angleValue, { color: SHOOTRZ_THEME.colors.primaryLight }]}>
                    {analysisResult.bodyAlignment}%
                  </Text>
                </GradientCard>
              </View>
            </View>
          </View>

          {/* Annotated Video Display */}
          {annotatedVideoId && (
            <View style={styles.videoSection}>
              <View style={styles.sectionTitleContainer}>
                <Ionicons name="videocam" size={24} color={SHOOTRZ_THEME.colors.primary} style={{ marginRight: 8 }} />
                <Text style={styles.sectionTitle}>Annotated Analysis</Text>
              </View>
              <View style={styles.videoContainer}>
                <Video
                  source={{ uri: apiService.getAnnotatedVideoUrl(annotatedVideoId) }}
                  style={[
                    styles.video, 
                    { 
                      aspectRatio: videoAspectRatio
                    }
                  ]}
                  useNativeControls
                  resizeMode={videoOrientation === 'portrait' ? ResizeMode.COVER : ResizeMode.CONTAIN}
                  shouldPlay={false}
                  isLooping
                  onLoad={(status) => {
                    // Detect video orientation and set aspect ratio
                    if (status.isLoaded && 'naturalSize' in status && status.naturalSize) {
                      const naturalSize = status.naturalSize as { width: number; height: number };
                      const { width, height } = naturalSize;
                      
                      // Determine orientation
                      let orientation: 'landscape' | 'portrait' | 'square';
                      let aspectRatio: number;
                      
                      if (width > height) {
                        orientation = 'landscape';
                        aspectRatio = width / height;
                      } else if (height > width) {
                        orientation = 'portrait';
                        aspectRatio = height / width; // Invert for portrait videos
                      } else {
                        orientation = 'square';
                        aspectRatio = 1;
                      }
                      
                      setVideoOrientation(orientation);
                      setVideoAspectRatio(aspectRatio);
                    }
                  }}
                />
              </View>
            </View>
          )}

          <LinearGradient
            colors={SHOOTRZ_THEME.gradients.primary as unknown as [ColorValue, ColorValue, ...ColorValue[]]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.analyzeAgainButton}
          >
            <TouchableOpacity
              onPress={() => setAnalysisResult(null)}
              style={styles.analyzeAgainButtonInner}
            >
              <Ionicons name="refresh" size={20} color={SHOOTRZ_THEME.colors.textPrimary} style={{ marginRight: 8 }} />
              <Text style={styles.analyzeAgainText}>Analyze Another Shot</Text>
            </TouchableOpacity>
          </LinearGradient>
        </View>
      )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  title: {
    ...SHOOTRZ_THEME.typography.heading2,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  subtitle: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
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
  placeholderTitle: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  placeholderText: {
    ...SHOOTRZ_THEME.typography.body,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xl,
  },
  recordButton: {
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
    overflow: 'hidden',
    minWidth: 220,
  },
  recordButtonInner: {
    flexDirection: 'row',
    paddingHorizontal: SHOOTRZ_THEME.spacing.xl,
    paddingVertical: SHOOTRZ_THEME.spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    fontSize: 18,
    textAlign: 'center',
  },
  resultsSection: {
    padding: SHOOTRZ_THEME.spacing.lg,
  },
  totalScoreCard: {
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xl,
    padding: SHOOTRZ_THEME.spacing.xl,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  totalScoreLabel: {
    ...SHOOTRZ_THEME.typography.heading3,
    color: SHOOTRZ_THEME.colors.textPrimary,
    marginBottom: SHOOTRZ_THEME.spacing.lg,
  },
  scoreRating: {
    ...SHOOTRZ_THEME.typography.heading3,
    fontSize: 18,
    color: SHOOTRZ_THEME.colors.textPrimary,
    marginTop: SHOOTRZ_THEME.spacing.lg,
    textAlign: 'center',
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
