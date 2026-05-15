// Email Service for Password Reset and Data Export
// This uses a simple approach that works on mobile devices

// BUG FIX: Removed unused Platform import
import { Linking, Alert } from 'react-native';
import * as MailComposer from 'expo-mail-composer';

class EmailService {
  // Check if email is available on device
  async isAvailable(): Promise<boolean> {
    try {
      return await MailComposer.isAvailableAsync();
    } catch (error) {
      return false;
    }
  }

  // Send password reset email
  async sendPasswordResetEmail(email: string): Promise<{ success: boolean; error?: string }> {
    try {
      const available = await this.isAvailable();

      if (!available) {
        // Fallback: Open default email app
        const subject = 'SHOOTRZ - Password Reset Request';
        const body = `You have requested to reset your password for your SHOOTRZ account (${email}).\n\nFor security reasons, please contact support@shootrz.com to complete your password reset.\n\nIf you didn't request this, please ignore this email.\n\n- SHOOTRZ Team`;

        const mailto = `mailto:support@shootrz.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

        const canOpen = await Linking.canOpenURL(mailto);
        if (canOpen) {
          await Linking.openURL(mailto);
          return { success: true };
        } else {
          return {
            success: false,
            error: 'No email app available. Please contact support@shootrz.com',
          };
        }
      }

      // BUG FIX: Removed fake random "reset code" — it had no server validation and was misleading.
      // Password resets should go through Supabase's built-in resetPasswordForEmail flow.
      const result = await MailComposer.composeAsync({
        recipients: [email],
        subject: 'SHOOTRZ - Password Reset Request',
        body: `Hello,\n\nYou have requested to reset your password for your SHOOTRZ account.\n\nPlease use the password reset link sent to your email by SHOOTRZ to complete the process.\n\nIf you didn't request this, please ignore this email.\n\nStay strong,\nSHOOTRZ Team\n\n"PERFECT THE GAME"`,
      });

      if (result.status === 'sent') {
        return { success: true };
      } else if (result.status === 'saved') {
        return { success: true }; // Email saved to drafts
      } else {
        return { success: false, error: 'Email cancelled' };
      }
    } catch (error) {
      console.error('Send email error:', error);
      return { success: false, error: 'Failed to send email. Please try again.' };
    }
  }

  // Send data export email
  async sendDataExportEmail(
    email: string,
    exportData: string
  ): Promise<{ success: boolean; error?: string }> {
    try {
      const available = await this.isAvailable();

      if (!available) {
        // Show alert with data
        Alert.alert(
          'Export Data',
          'Your data is ready. Copy the data below or contact support@shootrz.com to receive it via email.',
          [
            { text: 'OK' },
            {
              text: 'Contact Support',
              onPress: () => {
                Linking.openURL('mailto:support@shootrz.com?subject=SHOOTRZ Data Export Request');
              },
            },
          ]
        );
        return { success: true };
      }

      // Compose email with export data
      const result = await MailComposer.composeAsync({
        recipients: [email],
        subject: 'SHOOTRZ - Your Training Data Export',
        body: `Hello,\n\nHere is your complete SHOOTRZ training data export:\n\n---\n\nDATA EXPORT:\n${exportData.substring(0, 500)}...\n\n(Full data attached or available in app)\n\n---\n\nThank you for using SHOOTRZ!\n\n"PERFECT THE GAME"\n\n- SHOOTRZ Team`,
      });

      if (result.status === 'sent' || result.status === 'saved') {
        return { success: true };
      } else {
        return { success: false, error: 'Email cancelled' };
      }
    } catch (error) {
      console.error('Send data export error:', error);
      return { success: false, error: 'Failed to send export. Please try again.' };
    }
  }

  // Send welcome email
  async sendWelcomeEmail(name: string, email: string): Promise<void> {
    try {
      const available = await this.isAvailable();
      if (!available) return;

      await MailComposer.composeAsync({
        recipients: [email],
        subject: 'Welcome to SHOOTRZ! 🏀',
        body: `Hi ${name},\n\nWelcome to SHOOTRZ - your AI-powered basketball training assistant!\n\nWe're excited to help you perfect your game. Here's what you can do:\n\n🏀 Analyze your shooting form with AI\n💪 Access professional drills and workouts\n📊 Track your progress over time\n🤖 Get personalized coaching from Coach J\n🎯 Set and achieve your basketball goals\n\nLet's get started!\n\nBest,\nThe SHOOTRZ Team\n\n"PERFECT THE GAME"`,
      });
    } catch (error) {
      console.error('Send welcome email error:', error);
    }
  }

  // Send achievement notification email
  async sendAchievementEmail(name: string, email: string, achievement: string): Promise<void> {
    try {
      const available = await this.isAvailable();
      if (!available) return;

      await MailComposer.composeAsync({
        recipients: [email],
        subject: '🏆 New Achievement Unlocked in SHOOTRZ!',
        body: `Hi ${name},\n\nCongratulations! 🎉\n\nYou've unlocked a new achievement: ${achievement}\n\nKeep up the great work! Your dedication to improving your game is paying off.\n\nKeep shooting,\nSHOOTRZ Team\n\n"PERFECT THE GAME"`,
      });
    } catch (error) {
      console.error('Send achievement email error:', error);
    }
  }
}

// Singleton instance
export const emailService = new EmailService();
