import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { SHOOTRZ_THEME } from '../constants/theme';

interface ShootrzLogoProps {
  size?: 'small' | 'medium' | 'large';
  showTagline?: boolean;
}

export const ShootrzLogo: React.FC<ShootrzLogoProps> = ({
  size = 'medium',
  showTagline = false,
}) => {
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          imageWidth: 120,
          imageHeight: 40,
          taglineText: { fontSize: 10 },
          container: { marginBottom: 4 },
        };
      case 'large':
        return {
          imageWidth: 200,
          imageHeight: 70,
          taglineText: { fontSize: 16 },
          container: { marginBottom: 8 },
        };
      default: // medium
        return {
          imageWidth: 160,
          imageHeight: 55,
          taglineText: { fontSize: 12 },
          container: { marginBottom: 6 },
        };
    }
  };

  const sizeStyles = getSizeStyles();

  return (
    <View style={[styles.container, sizeStyles.container]}>
      <Image
        source={require('../../assets/shootrz-logo.png')}
        style={{
          width: sizeStyles.imageWidth,
          height: sizeStyles.imageHeight,
          resizeMode: 'contain',
        }}
      />
      {showTagline && (
        <Text style={[styles.tagline, sizeStyles.taglineText]}>PERFECT THE GAME</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  tagline: {
    fontWeight: '500',
    color: SHOOTRZ_THEME.colors.secondary,
    textAlign: 'center',
    marginTop: 8,
  },
});
