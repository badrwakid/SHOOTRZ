// Pose analysis and scoring for basketball shooting form
import { calculateElbowAngle, calculateKneeAngle, calculateReleaseAngle, calculateBodyAlignment, PoseLandmark } from './angleCalculator';
import { POSE_LANDMARKS, IDEAL_FORM } from '../constants/poseLandmarks';
import { getFeedbackMessage, getOverallFeedback } from '../constants/feedbackMessages';

export interface ShootingAnalysis {
  elbowAngle: number;
  kneeAngle: number;
  releaseAngle: number;
  bodyAlignment: number;
  scores: {
    elbow: number;
    balance: number;
    release: number;
    alignment: number;
    total: number;
  };
  feedback: string[];
}

export interface PoseData {
  landmarks: PoseLandmark[];
}

// Analyze shooting pose and generate scores
export function analyzeShootingPose(poseData: PoseData): ShootingAnalysis {
  const landmarks = poseData.landmarks;
  
  // Get key landmarks
  const leftShoulder = landmarks[POSE_LANDMARKS.LEFT_SHOULDER];
  const rightShoulder = landmarks[POSE_LANDMARKS.RIGHT_SHOULDER];
  const leftElbow = landmarks[POSE_LANDMARKS.LEFT_ELBOW];
  const rightElbow = landmarks[POSE_LANDMARKS.RIGHT_ELBOW];
  const leftWrist = landmarks[POSE_LANDMARKS.LEFT_WRIST];
  const rightWrist = landmarks[POSE_LANDMARKS.RIGHT_WRIST];
  const leftHip = landmarks[POSE_LANDMARKS.LEFT_HIP];
  const rightHip = landmarks[POSE_LANDMARKS.RIGHT_HIP];
  const leftKnee = landmarks[POSE_LANDMARKS.LEFT_KNEE];
  const rightKnee = landmarks[POSE_LANDMARKS.RIGHT_KNEE];
  const leftAnkle = landmarks[POSE_LANDMARKS.LEFT_ANKLE];
  const rightAnkle = landmarks[POSE_LANDMARKS.RIGHT_ANKLE];

  // Calculate angles (use right side for shooting)
  const elbowAngle = calculateElbowAngle(rightShoulder, rightElbow, rightWrist);
  const kneeAngle = calculateKneeAngle(rightHip, rightKnee, rightAnkle);
  const releaseAngle = calculateReleaseAngle(rightWrist, rightShoulder);
  const bodyAlignment = calculateBodyAlignment(leftShoulder, rightShoulder, leftHip, rightHip);

  // Score each component (0-25 points each)
  const elbowScore = scoreElbowAngle(elbowAngle);
  const balanceScore = scoreKneeAngle(kneeAngle);
  const releaseScore = scoreReleaseAngle(releaseAngle);
  const alignmentScore = scoreBodyAlignment(bodyAlignment);

  const totalScore = elbowScore + balanceScore + releaseScore + alignmentScore;

  // Generate feedback
  const feedback = generateFeedback({
    elbow: { angle: elbowAngle, score: elbowScore },
    balance: { angle: kneeAngle, score: balanceScore },
    release: { angle: releaseAngle, score: releaseScore },
    alignment: { angle: bodyAlignment, score: alignmentScore },
  });

  return {
    elbowAngle,
    kneeAngle,
    releaseAngle,
    bodyAlignment,
    scores: {
      elbow: elbowScore,
      balance: balanceScore,
      release: releaseScore,
      alignment: alignmentScore,
      total: totalScore,
    },
    feedback,
  };
}

// Score elbow angle (0-25 points)
function scoreElbowAngle(angle: number): number {
  const ideal = IDEAL_FORM.ELBOW_ANGLE;
  const tolerance = IDEAL_FORM.ELBOW_TOLERANCE;
  const deviation = Math.abs(angle - ideal);
  
  if (deviation <= tolerance) return 25;
  if (deviation <= tolerance * 2) return 20;
  if (deviation <= tolerance * 3) return 15;
  if (deviation <= tolerance * 4) return 10;
  return 5;
}

// Score knee angle for balance (0-25 points)
function scoreKneeAngle(angle: number): number {
  const ideal = 160; // Slightly bent knees for balance
  const tolerance = 20;
  const deviation = Math.abs(angle - ideal);
  
  if (deviation <= tolerance) return 25;
  if (deviation <= tolerance * 1.5) return 20;
  if (deviation <= tolerance * 2) return 15;
  return 10;
}

// Score release angle (0-25 points)
function scoreReleaseAngle(angle: number): number {
  const ideal = IDEAL_FORM.RELEASE_ANGLE;
  const tolerance = IDEAL_FORM.RELEASE_TOLERANCE;
  const deviation = Math.abs(angle - ideal);
  
  if (deviation <= tolerance) return 25;
  if (deviation <= tolerance * 2) return 20;
  if (deviation <= tolerance * 3) return 15;
  return 10;
}

// Score body alignment (0-25 points)
function scoreBodyAlignment(alignment: number): number {
  if (alignment <= 5) return 25;
  if (alignment <= 10) return 20;
  if (alignment <= 15) return 15;
  if (alignment <= 20) return 10;
  return 5;
}

// Generate personalized feedback with enhanced messages
function generateFeedback(components: any): string[] {
  const feedback: string[] = [];
  const totalScore = components.elbow.score + components.balance.score + 
                     components.release.score + components.alignment.score;
  
  // Add overall feedback first
  feedback.push(getOverallFeedback(totalScore));
  
  // Add specific component feedback
  feedback.push(getFeedbackMessage('elbow', components.elbow.score));
  feedback.push(getFeedbackMessage('balance', components.balance.score));
  feedback.push(getFeedbackMessage('release', components.release.score));
  feedback.push(getFeedbackMessage('alignment', components.alignment.score));
  
  // Add actionable tips based on lowest scoring area
  const lowestComponent = Object.entries(components).reduce((lowest, [key, value]: [string, any]) => {
    return value.score < lowest.score ? { key, score: value.score } : lowest;
  }, { key: 'elbow', score: 25 });
  
  const actionableTips = {
    elbow: "💪 Practice Tip: Do 50 form shots close to the basket, focusing solely on elbow position.",
    balance: "💪 Practice Tip: Practice shooting off one leg to improve your balance and stability.",
    release: "💪 Practice Tip: Hold your follow-through for 3 seconds after each shot.",
    alignment: "💪 Practice Tip: Record yourself from the side to check your body alignment.",
  };
  
  if (lowestComponent.score < 20) {
    feedback.push(actionableTips[lowestComponent.key as keyof typeof actionableTips]);
  }
  
  return feedback;
}
