// Custom hook for Google Authentication
import { useEffect } from 'react';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import {
  GOOGLE_WEB_CLIENT_ID,
  GOOGLE_IOS_CLIENT_ID,
  GOOGLE_ANDROID_CLIENT_ID,
} from '../services/socialAuth.service';

// This is required for the WebBrowser to work properly
WebBrowser.maybeCompleteAuthSession();

/**
 * Custom hook for Google Sign-In using Expo Auth Session
 * Must be used inside a React component
 */
export const useGoogleAuth = () => {
  const [request, response, promptAsync] = Google.useAuthRequest({
    clientId: GOOGLE_WEB_CLIENT_ID,
    scopes: ['openid', 'profile', 'email'],
  });

  return {
    request,
    response,
    promptAsync,
  };
};

