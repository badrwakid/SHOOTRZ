import { firebaseService } from '../services/firebase.service';

export const debugFirebaseAuth = async () => {
  console.log('=== FIREBASE AUTH DEBUG ===');
  
  if (!firebaseService.isInitialized()) {
    console.log('❌ Firebase not initialized');
    return;
  }

  const currentUser = firebaseService.getCurrentUser();
  
  if (currentUser) {
    console.log('✅ Current Firebase Auth User:');
    console.log('  - UID:', currentUser.uid);
    console.log('  - Email:', currentUser.email);
    console.log('  - Email Verified:', currentUser.emailVerified);
    console.log('  - Created:', currentUser.metadata.creationTime);
    console.log('  - Last Sign In:', currentUser.metadata.lastSignInTime);
    
    // Check if user has a Firestore profile
    try {
      const profile = await firebaseService.getUserProfile(currentUser.uid);
      if (profile) {
        console.log('✅ Firestore profile exists:', profile);
      } else {
        console.log('❌ No Firestore profile found - this is the problem!');
      }
    } catch (error) {
      console.log('❌ Error checking Firestore profile:', error);
    }
  } else {
    console.log('❌ No user currently signed in');
  }
  
  console.log('=========================');
};

export const listAllFirebaseUsers = () => {
  console.log('⚠️ NOTE: Listing all users requires Firebase Admin SDK (backend only)');
  console.log('To check users in Firebase Console:');
  console.log('1. Go to: https://console.firebase.google.com/');
  console.log('2. Select your project: shootrz-basketball');
  console.log('3. Go to Authentication > Users');
  console.log('4. Check if the email still exists there');
};

export const clearAllAuthData = async () => {
  console.log('🧹 Clearing all authentication data...');
  
  try {
    // Sign out from Firebase
    if (firebaseService.isInitialized()) {
      await firebaseService.signOut();
      console.log('✅ Signed out from Firebase');
    }
    
    // Clear local storage
    const { storageService } = await import('../services/storage.service');
    await storageService.clearAllData();
    console.log('✅ Cleared local storage');
    
    console.log('✅ All authentication data cleared');
    console.log('🔄 Please restart the app to see changes');
  } catch (error) {
    console.error('❌ Error clearing auth data:', error);
  }
};

export const testAuthFlow = async () => {
  console.log('🧪 Testing authentication flow...');
  
  try {
    // Test Firebase initialization
    console.log('1. Testing Firebase initialization...');
    if (firebaseService.isInitialized()) {
      console.log('✅ Firebase is initialized');
    } else {
      console.log('❌ Firebase not initialized');
      return;
    }
    
    // Test current user
    console.log('2. Testing current user...');
    const currentUser = firebaseService.getCurrentUser();
    if (currentUser) {
      console.log('✅ Current user found:', currentUser.email);
      
      // Test Firestore profile
      console.log('3. Testing Firestore profile...');
      const profile = await firebaseService.getUserProfile(currentUser.uid);
      if (profile) {
        console.log('✅ Firestore profile exists');
      } else {
        console.log('❌ No Firestore profile - this is the issue!');
      }
    } else {
      console.log('❌ No current user');
    }
    
    console.log('✅ Auth flow test completed');
  } catch (error) {
    console.error('❌ Auth flow test failed:', error);
  }
};

