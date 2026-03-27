import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useDSEStore } from '../../store/dseStore';

const CreateDSEScreen = ({ navigation }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('pending');
  const { createDSE, isLoading } = useDSEStore();

  const handleCreate = async () => {
    if (!name.trim()) {
      Alert.alert('Ошибка', 'Введите название');
      return;
    }

    try {
      const dseData = {
        name: name.trim(),
        description: description.trim(),
        status,
      };

      await createDSE(dseData);
      Alert.alert('Успешно', 'DSE запись создана', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось создать запись');
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Создать запись DSE</Text>
      </View>

      <View style={styles.form}>
        <Text style={styles.label}>Название</Text>
        <TextInput
          style={styles.input}
          placeholder="Введите название"
          value={name}
          onChangeText={setName}
          editable={!isLoading}
          placeholderTextColor="#999"
        />

        <Text style={styles.label}>Описание</Text>
        <TextInput
          style={[styles.input, styles.textarea]}
          placeholder="Введите описание"
          value={description}
          onChangeText={setDescription}
          editable={!isLoading}
          multiline
          numberOfLines={4}
          textAlignVertical="top"
          placeholderTextColor="#999"
        />

        <Text style={styles.label}>Статус</Text>
        <View style={styles.statusContainer}>
          {['pending', 'in_progress', 'completed'].map((s) => (
            <TouchableOpacity
              key={s}
              style={[
                styles.statusButton,
                status === s && styles.statusButtonActive,
              ]}
              onPress={() => setStatus(s)}
            >
              <Text
                style={[
                  styles.statusButtonText,
                  status === s && styles.statusButtonTextActive,
                ]}
              >
                {s === 'pending'
                  ? 'На заседании'
                  : s === 'in_progress'
                  ? 'В работе'
                  : 'Завершено'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity
          style={[styles.button, isLoading && styles.buttonDisabled]}
          onPress={handleCreate}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Создать</Text>
          )}
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
    backgroundColor: '#000080',
    paddingHorizontal: 20,
    paddingVertical: 16,
    paddingTop: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  form: {
    padding: 20,
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
    fontSize: 14,
    backgroundColor: '#fff',
  },
  textarea: {
    minHeight: 100,
  },
  statusContainer: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap',
  },
  statusButton: {
    flex: 1,
    minWidth: '30%',
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 6,
    backgroundColor: '#fff',
    alignItems: 'center',
  },
  statusButtonActive: {
    backgroundColor: '#000080',
    borderColor: '#000080',
  },
  statusButtonText: {
    fontSize: 12,
    color: '#333',
    fontWeight: '600',
    textAlign: 'center',
  },
  statusButtonTextActive: {
    color: '#fff',
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
});

export default CreateDSEScreen;
