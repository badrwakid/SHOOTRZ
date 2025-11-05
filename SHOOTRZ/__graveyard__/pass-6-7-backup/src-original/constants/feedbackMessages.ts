// Comprehensive feedback messages for basketball shooting analysis

export const FEEDBACK_MESSAGES = {
  elbow: {
    excellent: [
      "Perfect elbow alignment! Your 90-degree angle is textbook form.",
      "Excellent elbow positioning. This creates a consistent release point.",
      "Your elbow alignment is spot-on. Keep this consistency!",
    ],
    good: [
      "Good elbow angle. Try to maintain this position throughout your shot.",
      "Solid elbow form. A little more consistency and you'll be perfect.",
    ],
    needsWork: [
      "Keep your elbow closer to 90 degrees for better shooting accuracy.",
      "Your elbow is flaring out. Practice shooting with your elbow tucked in.",
      "Focus on keeping your shooting elbow directly under the ball.",
    ],
    poor: [
      "Your elbow angle needs significant adjustment. Practice form shooting close to the basket.",
      "Work on your elbow positioning. Watch professional shooters and mirror their form.",
    ],
  },
  
  balance: {
    excellent: [
      "Outstanding balance! Your base is solid and stable.",
      "Perfect knee bend. This gives you power and control.",
      "Excellent lower body foundation. This is championship form!",
    ],
    good: [
      "Good balance overall. Keep your weight centered over your feet.",
      "Solid stance. A bit more knee bend could add power.",
    ],
    needsWork: [
      "Bend your knees slightly more for better balance and power.",
      "Your stance needs adjustment. Keep your feet shoulder-width apart.",
      "Work on your base. More knee bend will improve your shot power.",
    ],
    poor: [
      "Your balance needs significant improvement. Practice your stance in front of a mirror.",
      "Focus on your lower body positioning before worrying about your shot.",
    ],
  },
  
  release: {
    excellent: [
      "Perfect release angle! This creates optimal arc on your shot.",
      "Excellent trajectory. Your shot has great lift.",
      "Ideal release point. This is NBA-level form!",
    ],
    good: [
      "Good release angle. Consistency is key.",
      "Solid release. Keep practicing this angle.",
    ],
    needsWork: [
      "Adjust your release angle - aim for around 45 degrees.",
      "Your release is a bit flat. Focus on getting more arc on your shot.",
      "Work on your follow-through to improve your release angle.",
    ],
    poor: [
      "Your release angle needs major adjustment. Practice shooting with a higher arc.",
      "Focus on releasing the ball at the peak of your jump with proper arc.",
    ],
  },
  
  alignment: {
    excellent: [
      "Perfect body alignment! Shoulders and hips are in sync.",
      "Excellent posture. Your body forms a straight line to the basket.",
      "Outstanding alignment. This is textbook basketball form!",
    ],
    good: [
      "Good alignment overall. Stay centered on your shot.",
      "Solid body positioning. Minor tweaks will make it perfect.",
    ],
    needsWork: [
      "Keep your shoulders aligned with your hips for better stability.",
      "Your body is leaning. Focus on staying balanced and centered.",
      "Work on your core strength to maintain better alignment.",
    ],
    poor: [
      "Your body alignment needs significant work. Practice shooting in front of a mirror.",
      "Focus on keeping your body straight from feet to fingertips.",
    ],
  },
  
  overall: {
    excellent: [
      "Incredible shooting form! You're ready to compete at the highest level!",
      "This is champion-level technique. Keep this consistency!",
      "Outstanding performance! Your dedication to perfect form is paying off!",
    ],
    good: [
      "Great shooting form! A few minor adjustments and you'll be perfect.",
      "Solid technique overall. Keep working on the fundamentals.",
      "Good work! You're on the right track to mastery.",
    ],
    average: [
      "Decent form, but there's room for improvement. Focus on the key areas highlighted.",
      "You're making progress. Keep practicing and focus on consistency.",
      "Not bad! Work on the areas that need improvement and you'll see results.",
    ],
    needsWork: [
      "Your form needs work, but don't get discouraged. Everyone starts somewhere!",
      "Focus on the basics: balance, elbow, eyes, follow-through (BEEF).",
      "Practice makes perfect. Start with form shooting close to the basket.",
    ],
  },
};

export function getFeedbackMessage(category: keyof typeof FEEDBACK_MESSAGES, score: number): string {
  const messages = FEEDBACK_MESSAGES[category];
  
  if (score >= 23) return messages.excellent[Math.floor(Math.random() * messages.excellent.length)];
  if (score >= 18) return messages.good[Math.floor(Math.random() * messages.good.length)];
  if (score >= 12) return messages.needsWork[Math.floor(Math.random() * messages.needsWork.length)];
  return messages.poor[Math.floor(Math.random() * messages.poor.length)];
}

export function getOverallFeedback(totalScore: number): string {
  const messages = FEEDBACK_MESSAGES.overall;
  
  if (totalScore >= 90) return messages.excellent[Math.floor(Math.random() * messages.excellent.length)];
  if (totalScore >= 75) return messages.good[Math.floor(Math.random() * messages.good.length)];
  if (totalScore >= 60) return messages.average[Math.floor(Math.random() * messages.average.length)];
  return messages.needsWork[Math.floor(Math.random() * messages.needsWork.length)];
}
