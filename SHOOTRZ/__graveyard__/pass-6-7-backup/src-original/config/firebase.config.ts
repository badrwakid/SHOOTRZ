// Firebase Configuration
// Replace these values with your actual Firebase project credentials
// Get these from: Firebase Console > Project Settings > General

export const FIREBASE_CONFIG = {
  // Your web app's Firebase configuration
  apiKey: "AIzaSyC0-Ic1WAIbXgFWULrdVFeMHs9bCdTqnCw",
  authDomain: "shootrz-basketball.firebaseapp.com",
  projectId: "shootrz-basketball",
  storageBucket: "shootrz-basketball.firebasestorage.app",
  messagingSenderId: "1001189179471",
  appId: "1:1001189179471:web:09af37d73c056bd46a6a3a",
  measurementId: "G-S0B2V5XJ8S" // Optional: for Analytics
};

// To set up Firebase for your project:
// 
// 1. Go to https://console.firebase.google.com/
// 2. Create a new project named "SHOOTRZ Basketball"
// 3. Enable Authentication:
//    - Go to Authentication > Sign-in method
//    - Enable Email/Password
//    - Optional: Enable Google Sign-in
//    
// 4. Enable Firestore Database:
//    - Go to Firestore Database > Create database
//    - Start in production mode
//    - Choose your region
//    
// 5. Enable Storage:
//    - Go to Storage > Get started
//    - Start in production mode
//    
// 6. Get your configuration:
//    - Go to Project Settings > General
//    - Scroll to "Your apps" section
//    - Click the web icon (</>)
//    - Copy the configuration object
//    - Replace the values above
//    
// 7. Set up Firestore Security Rules:
//    ```
//    rules_version = '2';
//    service cloud.firestore {
//      match /databases/{database}/documents {
//        // Users collection
//        match /users/{userId} {
//          allow read, write: if request.auth != null && request.auth.uid == userId;
//        }
//        
//        // Analyses collection
//        match /analyses/{analysisId} {
//          allow read, write: if request.auth != null && 
//                              resource.data.userId == request.auth.uid;
//        }
//        
//        // Goals collection
//        match /goals/{goalId} {
//          allow read, write: if request.auth != null && 
//                              resource.data.userId == request.auth.uid;
//        }
//        
//        // Drills collection (public read, admin write)
//        match /drills/{drillId} {
//          allow read: if true;
//          allow write: if request.auth != null && 
//                       get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
//        }
//      }
//    }
//    ```
//
// 8. Set up Storage Security Rules:
//    ```
//    rules_version = '2';
//    service firebase.storage {
//      match /b/{bucket}/o {
//        match /videos/{userId}/{videoId} {
//          allow read, write: if request.auth != null && request.auth.uid == userId;
//        }
//      }
//    }
//    ```

export const USE_FIREBASE = true; // Set to true when Firebase is configured

// Firestore Collections
export const COLLECTIONS = {
  USERS: 'users',
  ANALYSES: 'analyses',
  GOALS: 'goals',
  WORKOUTS: 'workouts',
  DRILLS: 'drills',
  DRILL_COMPLETIONS: 'drill_completions',
};

// Firestore subcollections (optional)
export const SUBCOLLECTIONS = {
  USER_ANALYSES: 'analyses',
  USER_GOALS: 'goals',
  USER_WORKOUTS: 'workouts',
};
