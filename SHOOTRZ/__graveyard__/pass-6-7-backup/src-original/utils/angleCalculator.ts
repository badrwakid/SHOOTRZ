// Angle calculation utilities for basketball pose analysis
export interface Point {
  x: number;
  y: number;
  z?: number;
}

export interface PoseLandmark {
  x: number;
  y: number;
  z?: number;
  visibility?: number;
}

// Calculate angle between three points
export function calculateAngle(point1: Point, point2: Point, point3: Point): number {
  const vector1 = {
    x: point1.x - point2.x,
    y: point1.y - point2.y,
  };
  
  const vector2 = {
    x: point3.x - point2.x,
    y: point3.y - point2.y,
  };
  
  const dot = vector1.x * vector2.x + vector1.y * vector2.y;
  const mag1 = Math.sqrt(vector1.x * vector1.x + vector1.y * vector1.y);
  const mag2 = Math.sqrt(vector2.x * vector2.x + vector2.y * vector2.y);
  
  const angle = Math.acos(dot / (mag1 * mag2)) * (180 / Math.PI);
  return Math.round(angle);
}

// Calculate elbow angle (shoulder-elbow-wrist)
export function calculateElbowAngle(shoulder: PoseLandmark, elbow: PoseLandmark, wrist: PoseLandmark): number {
  return calculateAngle(shoulder, elbow, wrist);
}

// Calculate knee angle (hip-knee-ankle)
export function calculateKneeAngle(hip: PoseLandmark, knee: PoseLandmark, ankle: PoseLandmark): number {
  return calculateAngle(hip, knee, ankle);
}

// Calculate release angle (wrist trajectory)
export function calculateReleaseAngle(wrist: PoseLandmark, shoulder: PoseLandmark): number {
  const dx = wrist.x - shoulder.x;
  const dy = shoulder.y - wrist.y; // Inverted Y for screen coordinates
  const angle = Math.atan2(dy, dx) * (180 / Math.PI);
  return Math.round(angle);
}

// Calculate body alignment (shoulder-hip-ankle alignment)
export function calculateBodyAlignment(leftShoulder: PoseLandmark, rightShoulder: PoseLandmark, leftHip: PoseLandmark, rightHip: PoseLandmark): number {
  const shoulderCenter = {
    x: (leftShoulder.x + rightShoulder.x) / 2,
    y: (leftShoulder.y + rightShoulder.y) / 2,
  };
  
  const hipCenter = {
    x: (leftHip.x + rightHip.x) / 2,
    y: (leftHip.y + rightHip.y) / 2,
  };
  
  const alignment = Math.abs(shoulderCenter.x - hipCenter.x);
  return Math.round(alignment * 100); // Convert to percentage
}
