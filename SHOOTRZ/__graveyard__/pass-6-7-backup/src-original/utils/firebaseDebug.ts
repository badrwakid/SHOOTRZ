// Firebase Debug Test - Minimal approach to isolate permission issues
import { firebaseService } from '../services/firebase.service';

export const testFirestorePermissions = async () => {
  console.log('🔍 Testing Firestore Permissions...');
  
  try {
    // Test 1: Check if we can read a simple document
    console.log('📋 Test 1: Basic Firestore read access');
    
    // Test 2: Try to read users collection (this is where the error occurs)
    console.log('📋 Test 2: Reading users collection');
    try {
      const result = await firebaseService.getUserByUsername('testuser');
      console.log('✅ Username lookup result:', result);
    } catch (error: any) {
      console.log('❌ Username lookup failed:', error.message);
      console.log('🔍 Error code:', error.code);
      console.log('🔍 Error details:', error);
    }
    
    // Test 3: Check current authentication state
    console.log('📋 Test 3: Current auth state');
    const currentUser = firebaseService.getCurrentUser();
    console.log('👤 Current user:', currentUser ? 'Authenticated' : 'Not authenticated');
    
    return true;
  } catch (error) {
    console.log('❌ Firestore permission test failed:', error);
    return false;
  }
};

// Run the test
export const runFirestoreDebug = () => {
  console.log('🚀 Running Firestore debug tests...');
  testFirestorePermissions();
};
