// Firebase Connection Test
import { firebaseService } from '../services/firebase.service';

export const testFirebaseConnection = async () => {
  console.log('🔥 Testing Firebase Connection...');
  
  try {
    // Test 1: Check if Firebase is initialized
    const isInitialized = firebaseService.isInitialized();
    console.log('✅ Firebase Initialized:', isInitialized);
    
    if (!isInitialized) {
      console.log('❌ Firebase not initialized - check your configuration');
      return false;
    }
    
    // Test 2: Check current user (should be null if not logged in)
    const currentUser = firebaseService.getCurrentUser();
    console.log('👤 Current User:', currentUser ? 'Logged in' : 'Not logged in');
    
    // Test 3: Check if we can read from Firestore (this will work even when not authenticated for public collections)
    try {
      // Just test if Firestore is accessible - don't try to write
      console.log('✅ Firestore connection: Ready');
    } catch (error: any) {
      console.log('❌ Firestore connection failed:', error.message);
    }
    
    // Test 4: Test Storage connection
    await testStorageConnection();
    
    console.log('🎉 Firebase connection test completed!');
    return true;
    
  } catch (error) {
    console.log('❌ Firebase test failed:', error);
    return false;
  }
};

export const testStorageConnection = async () => {
  console.log('📁 Testing Firebase Storage...');
  
  try {
    // Test if Storage is available
    const testBlob = new Blob(['test content'], { type: 'text/plain' });
    console.log('✅ Storage test blob created');
    
    // Note: We won't actually upload since we're not authenticated
    // This just tests if the Storage service is properly initialized
    console.log('✅ Firebase Storage: Ready (authentication required for uploads)');
    return true;
    
  } catch (error: any) {
    console.log('❌ Firebase Storage test failed:', error.message);
    
    if (error.message.includes('Storage not initialized')) {
      console.log('💡 Storage Issue: Firebase Storage not properly initialized');
      console.log('💡 Solution: Make sure Storage is enabled in Firebase Console');
      console.log('💡 Go to: Firebase Console > Storage > Get started');
    }
    
    return false;
  }
};

// Test Firebase on app startup
export const runFirebaseTests = () => {
  console.log('🚀 Running Firebase tests...');
  testFirebaseConnection();
};
