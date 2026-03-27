import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const InvitesScreen = () => {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Приглашения</Text>
      </View>
      <View style={styles.content}>
        <Text style={styles.comingSoon}>Скоро появится</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#000080',
    paddingHorizontal: 20,
    paddingVertical: 16,
    paddingTop: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  comingSoon: {
    fontSize: 16,
    color: '#999',
  },
});

export default InvitesScreen;
