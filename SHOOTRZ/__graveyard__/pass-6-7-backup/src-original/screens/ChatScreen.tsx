import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, Animated, ColorValue } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { hapticFeedback } from '../utils/hapticFeedback';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
}

export const ChatScreen: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Hey there! I'm Coach J, your AI basketball trainer. I'm here to help you perfect your game! What would you like to work on today?",
      isUser: false,
      timestamp: new Date().toISOString(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [quickQuestions] = useState([
    "Help me with shooting form",
    "What drills should I practice?",
    "How do I improve my balance?",
    "Elbow alignment tips",
    "Best practice routine",
  ]);

  const generateCoachResponse = (userMessage: string): string => {
    const message = userMessage.toLowerCase();
    
    // Basketball-specific coaching responses
    if (message.includes('shooting') || message.includes('shot')) {
      return "Great question about shooting! The key is the BEEF method: Balance, Eyes on target, Elbow alignment, and Follow-through. Make sure your elbow is at 90 degrees and follow through with your shooting hand pointing to the basket. Want me to analyze your form?";
    }
    
    if (message.includes('form') || message.includes('technique')) {
      return "Perfect form starts with your feet shoulder-width apart, knees slightly bent. Keep your shooting elbow aligned with the basket, and remember to follow through with your index and middle fingers pointing down. Practice makes permanent, so focus on consistency!";
    }
    
    if (message.includes('practice') || message.includes('drill')) {
      return "I recommend starting with form shooting close to the basket - 50 shots focusing purely on technique. Then move to the free throw line for consistency drills. Try the 'around the world' drill to practice from different angles. What's your current skill level?";
    }
    
    if (message.includes('elbow') || message.includes('alignment')) {
      return "Elbow alignment is crucial! Your shooting elbow should be directly under the ball, forming a 90-degree angle. If it's flaring out, practice shooting with your elbow touching your side. This creates a straight line from your elbow to the basket.";
    }
    
    if (message.includes('balance') || message.includes('stance')) {
      return "Balance is everything! Keep your feet shoulder-width apart with your shooting foot slightly forward. Your weight should be evenly distributed. Imagine a straight line from your shooting foot through your body to the basket.";
    }
    
    if (message.includes('follow through') || message.includes('release')) {
      return "Follow-through is your friend! After releasing the ball, hold your shooting hand in the 'gooseneck' position - index and middle fingers pointing down. This ensures proper backspin and trajectory. Hold this position until the ball hits the rim.";
    }
    
    if (message.includes('help') || message.includes('tips')) {
      return "I'm here to help you improve! I can give you tips on shooting form, suggest drills, analyze your technique, and help you set goals. Try asking me about specific aspects like 'elbow alignment' or 'balance' for detailed coaching!";
    }
    
    if (message.includes('goal') || message.includes('improve')) {
      return "Setting goals is key to improvement! Start with specific, measurable goals like 'make 80% of free throws' or 'shoot 100 form shots daily.' Track your progress and celebrate small wins. What specific area do you want to focus on?";
    }
    
    // Default responses
    const responses = [
      "That's a great question! Basketball is all about fundamentals and consistency. What specific aspect of your game would you like to work on?",
      "I love your enthusiasm! Remember, every great shooter started with the basics. Focus on one thing at a time - whether it's your stance, elbow alignment, or follow-through.",
      "Excellent! The key to improvement is deliberate practice. Set small, achievable goals and track your progress. What's your current biggest challenge?",
      "That's exactly the right mindset! Basketball is a mental game as much as physical. Stay focused, stay confident, and keep practicing those fundamentals.",
      "Great to hear from you! Remember the SHOOTRZ motto: 'Perfect the Game.' Every shot is an opportunity to improve. What would you like to perfect today?",
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    hapticFeedback.medium();

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);

    // Simulate typing delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

    const coachResponse: Message = {
      id: (Date.now() + 1).toString(),
      text: generateCoachResponse(inputText),
      isUser: false,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, coachResponse]);
    setIsTyping(false);
  };

  const quickQuestionsList = [
    "How do I improve my shooting form?",
    "What drills should I practice?",
    "Help with elbow alignment",
    "Tips for better balance",
    "How to set goals?",
  ];

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <KeyboardAvoidingView 
        style={styles.keyboardAvoidingView} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.coachInfo}>
          <Ionicons name="chatbubbles" size={32} color={SHOOTRZ_THEME.colors.primary} style={{ marginRight: SHOOTRZ_THEME.spacing.md }} />
          <View>
            <Text style={styles.coachName}>Coach J</Text>
            <Text style={styles.coachTitle}>AI Basketball Trainer</Text>
          </View>
        </View>
        <View style={styles.statusIndicator}>
          <View style={styles.statusDot} />
          <Text style={styles.statusText}>Online</Text>
        </View>
      </View>

      {/* Messages */}
      <ScrollView style={styles.messagesContainer} showsVerticalScrollIndicator={false}>
        {messages.map((message) => (
          <View key={message.id} style={[
            styles.messageContainer,
            message.isUser ? styles.userMessage : styles.coachMessage
          ]}>
            {message.isUser ? (
              <LinearGradient
                colors={SHOOTRZ_THEME.gradients.primary as [ColorValue, ColorValue]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.userBubble}
              >
                <Text style={styles.userText}>
                  {message.text}
                </Text>
              </LinearGradient>
            ) : (
              <View style={styles.coachBubble}>
                <View style={styles.coachAvatarContainer}>
                  <Ionicons name="chatbubbles" size={16} color={SHOOTRZ_THEME.colors.primary} />
                </View>
                <View style={styles.coachTextContainer}>
                  <Text style={styles.coachName}>Coach J</Text>
                  <Text style={styles.coachText}>
                    {message.text}
                  </Text>
                </View>
              </View>
            )}
          </View>
        ))}
        
        {isTyping && (
          <View style={[styles.messageContainer, styles.coachMessage]}>
            <View style={styles.coachBubble}>
              <View style={styles.coachAvatarContainer}>
                <Ionicons name="chatbubbles" size={16} color={SHOOTRZ_THEME.colors.primary} />
              </View>
              <View style={styles.coachTextContainer}>
                <Text style={styles.coachName}>Coach J</Text>
                <View style={styles.typingIndicator}>
                  <Text style={styles.typingText}>typing</Text>
                  <View style={styles.typingDots}>
                    <View style={[styles.dot, styles.dot1]} />
                    <View style={[styles.dot, styles.dot2]} />
                    <View style={[styles.dot, styles.dot3]} />
                  </View>
                </View>
              </View>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Quick Questions */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickQuestions}>
        {quickQuestions.map((question, index) => (
          <LinearGradient
            key={index}
            colors={SHOOTRZ_THEME.gradients.secondary as [ColorValue, ColorValue]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.quickQuestionButton}
          >
            <TouchableOpacity
              onPress={() => {
                hapticFeedback.light();
                setInputText(question);
              }}
            >
              <Text style={styles.quickQuestionText}>{question}</Text>
            </TouchableOpacity>
          </LinearGradient>
        ))}
      </ScrollView>

      {/* Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          placeholder="Ask Coach J anything about basketball..."
          placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
          value={inputText}
          onChangeText={setInputText}
          multiline
          maxLength={500}
        />
        {inputText.trim() ? (
          <LinearGradient
            colors={SHOOTRZ_THEME.gradients.primary as [ColorValue, ColorValue]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.sendButton}
          >
            <TouchableOpacity
              onPress={handleSendMessage}
            >
              <Text style={styles.sendButtonText}>Send</Text>
            </TouchableOpacity>
          </LinearGradient>
        ) : (
          <TouchableOpacity
            style={styles.sendButtonDisabled}
            disabled={true}
          >
            <Text style={styles.sendButtonTextDisabled}>Send</Text>
          </TouchableOpacity>
        )}
      </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  coachInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  coachAvatarContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: SHOOTRZ_THEME.spacing.xs,
  },
  coachName: {
    ...SHOOTRZ_THEME.typography.heading3,
    marginBottom: 2,
  },
  coachTitle: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: SHOOTRZ_THEME.colors.secondary,
    marginRight: SHOOTRZ_THEME.spacing.xs,
  },
  statusText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  messagesContainer: {
    flex: 1,
    padding: SHOOTRZ_THEME.spacing.md,
  },
  messageContainer: {
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  userMessage: {
    alignItems: 'flex-end',
  },
  coachMessage: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: SHOOTRZ_THEME.spacing.md,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
  },
  userBubble: {
    backgroundColor: SHOOTRZ_THEME.colors.primary,
  },
  coachBubble: {
    backgroundColor: 'transparent',
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  coachTextContainer: {
    flex: 1,
  },
  coachNameText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.primary,
    fontWeight: '600',
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  messageText: {
    ...SHOOTRZ_THEME.typography.body,
    lineHeight: 20,
  },
  userText: {
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  coachText: {
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  typingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typingText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textMuted,
    fontStyle: 'italic',
    marginRight: SHOOTRZ_THEME.spacing.xs,
  },
  typingDots: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: SHOOTRZ_THEME.colors.textMuted,
    marginHorizontal: 1,
  },
  dot1: {
    opacity: 0.4,
  },
  dot2: {
    opacity: 0.7,
  },
  dot3: {
    opacity: 1,
  },
  quickQuestions: {
    maxHeight: 50,
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  quickQuestionButton: {
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
    marginRight: SHOOTRZ_THEME.spacing.sm,
  },
  quickQuestionText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textPrimary,
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: SHOOTRZ_THEME.spacing.md,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderTopWidth: 1,
    borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  textInput: {
    flex: 1,
    ...COMPONENT_STYLES.input,
    marginRight: SHOOTRZ_THEME.spacing.md,
    maxHeight: 100,
    textAlignVertical: 'top',
  },
  sendButton: {
    paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    marginLeft: SHOOTRZ_THEME.spacing.sm,
  },
  sendButtonDisabled: {
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    marginLeft: SHOOTRZ_THEME.spacing.sm,
    opacity: 0.5,
  },
  sendButtonText: {
    ...SHOOTRZ_THEME.typography.button,
    color: SHOOTRZ_THEME.colors.textPrimary,
    textAlign: 'center',
  },
  sendButtonTextDisabled: {
    ...SHOOTRZ_THEME.typography.button,
    color: SHOOTRZ_THEME.colors.textMuted,
    textAlign: 'center',
  },
});
