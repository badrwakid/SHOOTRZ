// Basketball drill library data
export interface Drill {
  id: string;
  name: string;
  category: 'shooting' | 'dribbling' | 'defense' | 'conditioning';
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  description: string;
  duration: number; // minutes
  instructions: string[];
  focusAreas: string[];
  videoUrl?: string;
}

export const DRILLS: Drill[] = [
  {
    id: '1',
    name: 'Form Shooting',
    category: 'shooting',
    difficulty: 'beginner',
    description: 'Perfect your shooting form close to the basket',
    duration: 10,
    instructions: [
      'Stand 2 feet from the basket',
      'Focus on proper elbow alignment',
      'Follow through with your shooting hand',
      'Shoot 50 shots with perfect form',
    ],
    focusAreas: ['Elbow angle', 'Follow through', 'Release point'],
  },
  {
    id: '2',
    name: 'Free Throw Routine',
    category: 'shooting',
    difficulty: 'beginner',
    description: 'Develop a consistent free throw routine',
    duration: 15,
    instructions: [
      'Develop a consistent pre-shot routine',
      'Bounce the ball 3 times',
      'Take a deep breath before shooting',
      'Focus on the back of the rim',
      'Follow through and hold your form',
    ],
    focusAreas: ['Consistency', 'Mental focus', 'Routine'],
  },
  {
    id: '3',
    name: 'Spot Shooting',
    category: 'shooting',
    difficulty: 'intermediate',
    description: 'Improve shooting accuracy from different spots',
    duration: 20,
    instructions: [
      'Shoot from 5 different spots around the court',
      'Make 10 shots from each spot before moving',
      'Focus on quick release and accuracy',
      'Track your shooting percentage',
    ],
    focusAreas: ['Accuracy', 'Quick release', 'Shot selection'],
  },
  {
    id: '4',
    name: 'Ball Handling Basics',
    category: 'dribbling',
    difficulty: 'beginner',
    description: 'Master basic ball handling skills',
    duration: 15,
    instructions: [
      'Practice stationary dribbling',
      'Keep the ball low and controlled',
      'Use your fingertips, not your palm',
      'Practice with both hands equally',
    ],
    focusAreas: ['Ball control', 'Hand-eye coordination', 'Both hands'],
  },
  {
    id: '5',
    name: 'Defensive Slides',
    category: 'defense',
    difficulty: 'beginner',
    description: 'Improve defensive footwork and positioning',
    duration: 12,
    instructions: [
      'Start in defensive stance',
      'Slide laterally without crossing feet',
      'Keep your hands up and active',
      'Stay low and balanced',
    ],
    focusAreas: ['Footwork', 'Balance', 'Defensive stance'],
  },
  {
    id: '6',
    name: 'Conditioning Circuit',
    category: 'conditioning',
    difficulty: 'intermediate',
    description: 'Build basketball-specific endurance',
    duration: 25,
    instructions: [
      'Run suicides (baseline to half court and back)',
      'Do 20 push-ups',
      'Perform defensive slides',
      'Sprint the length of the court',
      'Repeat circuit 3 times',
    ],
    focusAreas: ['Endurance', 'Speed', 'Agility'],
  },
];

export const WORKOUTS = [
  {
    id: '1',
    name: 'Beginner Shooting Workout',
    duration: 30,
    drills: ['1', '2', '3'],
    description: 'Perfect for players learning shooting fundamentals',
  },
  {
    id: '2',
    name: 'Complete Skills Workout',
    duration: 45,
    drills: ['1', '4', '5', '6'],
    description: 'Comprehensive workout covering all basketball skills',
  },
  {
    id: '3',
    name: 'Advanced Training Session',
    duration: 60,
    drills: ['3', '6'],
    description: 'High-intensity training for advanced players',
  },
];
