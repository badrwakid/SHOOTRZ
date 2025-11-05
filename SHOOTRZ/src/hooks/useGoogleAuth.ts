// Custom hook for Google Authentication
import { supabase } from '../services/supabase.client';

export const useGoogleAuth = () => {
  const signIn = async () => {
    const { error } = await supabase.auth.signInWithOAuth({ provider: 'google' });
    if (error) throw error
  }
  return { signIn }
}
