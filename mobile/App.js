import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from './src/store/authStore';
import RootNavigator from './src/navigation/RootNavigator';

export default function App() {
  const initializeAuth = useAuthStore((state) => state.initializeAuth);

  useEffect(() => {
    initializeAuth();
  }, []);

  return (
    <>
      <StatusBar barStyle="light-content" backgroundColor="#000080" />
      <RootNavigator />
    </>
  );
}
