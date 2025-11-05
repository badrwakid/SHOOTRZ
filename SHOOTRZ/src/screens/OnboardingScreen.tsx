import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Dimensions, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { ShootrzLogo } from '../components/ShootrzLogo';
import { useAuth } from '../context/AuthContext';

const { width } = Dimensions.get('window');

interface OnboardingScreenProps {
  onComplete: () => void;
}

export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onComplete }) => {
  const { updateProfile } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedSkillLevel, setSelectedSkillLevel] = useState<
    'beginner' | 'intermediate' | 'advanced'
  >('beginner');
  const [selectedPosition, setSelectedPosition] = useState('Guard');
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);

  const steps = [
    {
      title: 'Welcome to SHOOTRZ',
      subtitle: 'Your AI-powered basketball training assistant',
      icon: 'basketball',
      description: 'Perfect your shooting form with AI analysis and personalized coaching',
    },
    {
      title: 'Select Your Skill Level',
      subtitle: 'This helps us personalize your training',
      icon: 'stats-chart',
      description: 'Choose the level that best describes your current basketball skills',
    },
    {
      title: 'Choose Your Position',
      subtitle: 'What position do you play?',
      icon: 'people',
      description: "We'll tailor drills and workouts to your position",
    },
    {
      title: 'Set Your Goals',
      subtitle: 'What do you want to improve?',
      icon: 'trophy',
      description: 'Select areas you want to focus on',
    },
  ];

  const positions = ['Guard', 'Forward', 'Center', 'All-Around'];
  const goalOptions = [
    'Improve shooting accuracy',
    'Perfect my form',
    'Increase consistency',
    'Better balance',
    'Faster release',
    'Stronger follow-through',
  ];

  const handleNext = async () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Complete onboarding
      await completeOnboarding();
    }
  };

  const handleSkip = () => {
    onComplete();
  };

  const completeOnboarding = async () => {
    try {
      await updateProfile({
        skillLevel: selectedSkillLevel,
        position: selectedPosition,
      });
      onComplete();
    } catch (error) {
      console.error('Error completing onboarding:', error);
      onComplete(); // Continue anyway
    }
  };

  const toggleGoal = (goal: string) => {
    if (selectedGoals.includes(goal)) {
      setSelectedGoals(selectedGoals.filter((g) => g !== goal));
    } else {
      setSelectedGoals([...selectedGoals, goal]);
    }
  };

  const renderStep = () => {
    const step = steps[currentStep];

    return (
      <View style={styles.stepContainer}>
        <Ionicons
          name={step.icon as any}
          size={64}
          color={SHOOTRZ_THEME.colors.primary}
          style={{ marginBottom: SHOOTRZ_THEME.spacing.lg }}
        />
        <Text style={styles.stepTitle}>{step.title}</Text>
        <Text style={styles.stepSubtitle}>{step.subtitle}</Text>
        <Text style={styles.stepDescription}>{step.description}</Text>

        {currentStep === 1 && (
          <View style={styles.optionsContainer}>
            {(['beginner', 'intermediate', 'advanced'] as const).map((level) => (
              <TouchableOpacity
                key={level}
                style={[
                  styles.optionButton,
                  selectedSkillLevel === level && styles.optionButtonActive,
                ]}
                onPress={() => setSelectedSkillLevel(level)}
              >
                <Text
                  style={[
                    styles.optionText,
                    selectedSkillLevel === level && styles.optionTextActive,
                  ]}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </Text>
                <Text style={styles.optionDescription}>
                  {level === 'beginner'
                    ? 'Learning fundamentals'
                    : level === 'intermediate'
                      ? 'Improving consistency'
                      : 'Perfecting technique'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {currentStep === 2 && (
          <View style={styles.optionsContainer}>
            {positions.map((position) => (
              <TouchableOpacity
                key={position}
                style={[
                  styles.positionButton,
                  selectedPosition === position && styles.positionButtonActive,
                ]}
                onPress={() => setSelectedPosition(position)}
              >
                <Text
                  style={[
                    styles.positionText,
                    selectedPosition === position && styles.positionTextActive,
                  ]}
                >
                  {position}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {currentStep === 3 && (
          <View style={styles.optionsContainer}>
            {goalOptions.map((goal, index) => (
              <TouchableOpacity
                key={index}
                style={[styles.goalButton, selectedGoals.includes(goal) && styles.goalButtonActive]}
                onPress={() => toggleGoal(goal)}
              >
                <Text
                  style={[styles.goalText, selectedGoals.includes(goal) && styles.goalTextActive]}
                >
                  {selectedGoals.includes(goal) ? '✓ ' : ''}
                  {goal}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
      {/* Logo */}
      <View style={styles.logoContainer}>
        <ShootrzLogo size="medium" showTagline={false} />
      </View>

      {/* Progress Indicator */}
      <View style={styles.progressContainer}>
        {steps.map((_, index) => (
          <View
            key={index}
            style={[styles.progressDot, index <= currentStep && styles.progressDotActive]}
          />
        ))}
      </View>

      {/* Step Content */}
      <ScrollView style={styles.contentContainer}>{renderStep()}</ScrollView>

      {/* Navigation */}
      <View style={styles.navigationContainer}>
        {currentStep > 0 && (
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => setCurrentStep(currentStep - 1)}
          >
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
          <Text style={styles.skipButtonText}>Skip</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.nextButton} onPress={handleNext}>
          <Text style={styles.nextButtonText}>
            {currentStep === steps.length - 1 ? 'Get Started' : 'Next →'}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
  },
  logoContainer: {
    alignItems: 'center',
    paddingTop: SHOOTRZ_THEME.spacing.xxl,
    paddingBottom: SHOOTRZ_THEME.spacing.lg,
  },
  progressContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingVertical: SHOOTRZ_THEME.spacing.lg,
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    marginHorizontal: SHOOTRZ_THEME.spacing.xs,
  },
  progressDotActive: {
    backgroundColor: SHOOTRZ_THEME.colors.primary,
    width: 24,
  },
  contentContainer: {
    flex: 1,
  },
  stepContainer: {
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.xl,
  },
  stepTitle: {
    ...SHOOTRZ_THEME.typography.heading1,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  stepSubtitle: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  stepDescription: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textMuted,
    textAlign: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.xl,
  },
  optionsContainer: {
    width: '100%',
    paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
  },
  optionButton: {
    ...COMPONENT_STYLES.card,
    marginBottom: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.lg,
    alignItems: 'center',
  },
  optionButtonActive: {
    borderWidth: 2,
    borderColor: SHOOTRZ_THEME.colors.primary,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  optionText: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  optionTextActive: {
    color: SHOOTRZ_THEME.colors.primary,
  },
  optionDescription: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.textMuted,
  },
  positionButton: {
    ...COMPONENT_STYLES.card,
    marginBottom: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.lg,
    alignItems: 'center',
  },
  positionButtonActive: {
    borderWidth: 2,
    borderColor: SHOOTRZ_THEME.colors.secondary,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  positionText: {
    ...SHOOTRZ_THEME.typography.body,
    fontWeight: '600',
  },
  positionTextActive: {
    color: SHOOTRZ_THEME.colors.secondary,
  },
  goalButton: {
    ...COMPONENT_STYLES.card,
    marginBottom: SHOOTRZ_THEME.spacing.sm,
    paddingVertical: SHOOTRZ_THEME.spacing.md,
  },
  goalButtonActive: {
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderWidth: 1,
    borderColor: SHOOTRZ_THEME.colors.accent,
  },
  goalText: {
    ...SHOOTRZ_THEME.typography.body,
  },
  goalTextActive: {
    color: SHOOTRZ_THEME.colors.accent,
    fontWeight: '600',
  },
  navigationContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderTopWidth: 1,
    borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  backButton: {
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
  },
  backButtonText: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  skipButton: {
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
  },
  skipButtonText: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textMuted,
  },
  nextButton: {
    ...COMPONENT_STYLES.button.primary,
    paddingHorizontal: SHOOTRZ_THEME.spacing.xl,
  },
  nextButtonText: {
    ...SHOOTRZ_THEME.typography.button,
  },
});
