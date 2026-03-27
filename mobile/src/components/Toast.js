import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

/**
 * Toast Error Component
 */
export const ToastError = ({ message, duration = 3000 }) => {
  const [visible, setVisible] = React.useState(true);

  React.useEffect(() => {
    const timer = setTimeout(() => setVisible(false), duration);
    return () => clearTimeout(timer);
  }, [duration]);

  if (!visible) return null;

  return (
    <View style={styles.errorContainer}>
      <Text style={styles.errorText}>{message}</Text>
    </View>
  );
};

/**
 * Toast Success Component
 */
export const ToastSuccess = ({ message, duration = 3000 }) => {
  const [visible, setVisible] = React.useState(true);

  React.useEffect(() => {
    const timer = setTimeout(() => setVisible(false), duration);
    return () => clearTimeout(timer);
  }, [duration]);

  if (!visible) return null;

  return (
    <View style={styles.successContainer}>
      <Text style={styles.successText}>{message}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  errorContainer: {
    position: 'absolute',
    top: 50,
    left: 16,
    right: 16,
    backgroundColor: '#f44336',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    zIndex: 100,
  },
  errorText: {
    color: '#fff',
    fontSize: 14,
  },
  successContainer: {
    position: 'absolute',
    top: 50,
    left: 16,
    right: 16,
    backgroundColor: '#4caf50',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    zIndex: 100,
  },
  successText: {
    color: '#fff',
    fontSize: 14,
  },
});
