import React from 'react';
import { View, StyleSheet } from 'react-native';

/**
 * LoadingScreen Component
 * Используется во время загрузки приложения
 */
const LoadingScreen = () => {
  return (
    <View style={styles.container}>
      <View style={styles.spinner} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000080',
  },
  spinner: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 4,
    borderColor: '#fff',
    borderTopColor: 'transparent',
    borderRightColor: 'transparent',
    borderBottomColor: 'transparent',
  },
});

export default LoadingScreen;
