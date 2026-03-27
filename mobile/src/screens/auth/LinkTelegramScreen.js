import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useAuthStore } from '../../store/authStore';

const LinkTelegramScreen = ({ navigation }) => {
  const [linkingCode, setLinkingCode] = useState('');
  const [showCamera, setShowCamera] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();
  const { linkTelegram, isLoading, error } = useAuthStore();

  const handleLinkTelegram = async () => {
    if (!linkingCode) {
      Alert.alert('Ошибка', 'Введите или отсканируйте код привязки');
      return;
    }

    try {
      await linkTelegram(linkingCode);
      Alert.alert('Успешно', 'Ваш Telegram аккаунт привязан');
    } catch (err) {
      Alert.alert('Ошибка', error || 'Не удалось привязать Telegram');
    }
  };

  const handleBarCodeScanned = ({ data }) => {
    setLinkingCode(data);
    setShowCamera(false);
  };

  const requestCameraPermission = async () => {
    const { granted } = await requestPermission();
    if (granted) {
      setShowCamera(true);
    } else {
      Alert.alert('Ошибка', 'Требуется разрешение на доступ к камере');
    }
  };

  if (showCamera && permission?.granted) {
    return (
      <View style={styles.cameraContainer}>
        <CameraView
          style={styles.camera}
          facing="back"
          onBarcodeScanned={handleBarCodeScanned}
        />
        <TouchableOpacity
          style={styles.closeButton}
          onPress={() => setShowCamera(false)}
        >
          <Text style={styles.closeButtonText}>Закрыть</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Привязать Telegram</Text>
        <Text style={styles.subtitle}>
          Отсканируйте QR код или введите код привязки из Telegram бота
        </Text>
      </View>

      <View style={styles.formContainer}>
        <TouchableOpacity
          style={styles.cameraButton}
          onPress={requestCameraPermission}
        >
          <Text style={styles.cameraButtonText}>📷 Отсканировать QR код</Text>
        </TouchableOpacity>

        <View style={styles.divider}>
          <View style={styles.line} />
          <Text style={styles.dividerText}>или</Text>
          <View style={styles.line} />
        </View>

        <Text style={styles.label}>Код привязки</Text>
        <TextInput
          style={styles.input}
          placeholder="Введите 6-значный код"
          value={linkingCode}
          onChangeText={setLinkingCode}
          editable={!isLoading}
          maxLength={6}
          keyboardType="numeric"
          placeholderTextColor="#999"
        />

        {error && <Text style={styles.errorText}>{error}</Text>}

        <TouchableOpacity
          style={[styles.button, isLoading && styles.buttonDisabled]}
          onPress={handleLinkTelegram}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Привязать аккаунт</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.skipButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.skipButtonText}>Пропустить</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    paddingTop: 40,
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  formContainer: {
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  cameraButton: {
    backgroundColor: '#000080',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },
  cameraButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
  },
  line: {
    flex: 1,
    height: 1,
    backgroundColor: '#ddd',
  },
  dividerText: {
    marginHorizontal: 12,
    color: '#999',
    fontSize: 12,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#fff',
    textAlign: 'center',
    letterSpacing: 2,
  },
  button: {
    backgroundColor: '#000080',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
    marginTop: 24,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  skipButton: {
    marginTop: 12,
    padding: 12,
    alignItems: 'center',
  },
  skipButtonText: {
    color: '#000080',
    fontSize: 14,
    fontWeight: '600',
  },
  errorText: {
    color: '#d32f2f',
    fontSize: 12,
    marginTop: 8,
  },
  cameraContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  closeButton: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: '#000080',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default LinkTelegramScreen;
