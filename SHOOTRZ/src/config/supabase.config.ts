// Supabase Configuration
// Supabase client is initialized in src/services/supabase.client.ts
// Environment variables are loaded from .env file:
//   EXPO_PUBLIC_SUPABASE_URL
//   EXPO_PUBLIC_SUPABASE_ANON_KEY

export const USE_SUPABASE = true; // Set to true when Supabase is configured

// Supabase Database Tables (PostgreSQL)
export const TABLES = {
  USERS: 'users',
  VIDEOS: 'videos',
  METRICS: 'metrics',
  FEEDBACK: 'feedback',
  SESSIONS: 'sessions',
  MODELS: 'models',
};

// Supabase Storage Buckets
export const STORAGE_BUCKETS = {
  VIDEOS: 'videos',
};

// To set up Supabase for your project:
//
// 1. Go to https://supabase.com/
// 2. Create a new project
// 3. Get your project URL and anon key:
//    - Go to Settings > API
//    - Copy "Project URL" → EXPO_PUBLIC_SUPABASE_URL
//    - Copy "anon public" key → EXPO_PUBLIC_SUPABASE_ANON_KEY
//    - Copy "service_role" key → SUPABASE_SERVICE_KEY (backend only)
//
// 4. Apply database schema:
//    - Go to SQL Editor
//    - Run schema.sql from supabase/schema.sql
//    - Run storage_policies.sql from supabase/storage_policies.sql
//
// 5. Create storage bucket:
//    - Go to Storage
//    - Create bucket named "videos" (private)
//
// 6. Enable OAuth providers (optional):
//    - Go to Authentication > Providers
//    - Enable Google/Apple Sign-in
//    - Configure redirect URLs in Authentication > URL Configuration

