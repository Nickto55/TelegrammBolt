import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useDSEStore } from '../../store/dseStore';

const DSEDetailScreen = ({ route, navigation }) => {
  const { dseId } = route.params;
  const { selectedDSE, isLoading, getDSEDetail } = useDSEStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDSEDetail();
  }, []);

  const loadDSEDetail = async () => {
    try {
      setLoading(true);
      await getDSEDetail(dseId);
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось загрузить деталь DSE');
    } finally {
      setLoading(false);
    }
  };

  if (loading || isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#000080" />
      </View>
    );
  }

  if (!selectedDSE) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Запись не найдена</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{selectedDSE.name}</Text>
        <Text
          style={[
            styles.status,
            { backgroundColor: getStatusColor(selectedDSE.status) },
          ]}
        >
          {selectedDSE.status || 'В работе'}
        </Text>
      </View>

      <View style={styles.content}>
        <Section title="Описание">
          <Text style={styles.text}>
            {selectedDSE.description || 'Нет описания'}
          </Text>
        </Section>

        <Section title="Информация">
          <InfoRow label="ID" value={selectedDSE.id} />
          <InfoRow
            label="Дата создания"
            value={new Date(selectedDSE.created_at).toLocaleDateString('ru-RU')}
          />
          <InfoRow label="Статус" value={selectedDSE.status || 'Неизвестно'} />
        </Section>

        {selectedDSE.additional_info && (
          <Section title="Дополнительная информация">
            <Text style={styles.text}>{selectedDSE.additional_info}</Text>
          </Section>
        )}
      </View>
    </ScrollView>
  );
};

const Section = ({ title, children }) => (
  <View style={styles.section}>
    <Text style={styles.sectionTitle}>{title}</Text>
    {children}
  </View>
);

const InfoRow = ({ label, value }) => (
  <View style={styles.infoRow}>
    <Text style={styles.infoLabel}>{label}:</Text>
    <Text style={styles.infoValue}>{value}</Text>
  </View>
);

const getStatusColor = (status) => {
  switch (status) {
    case 'completed':
      return '#4caf50';
    case 'pending':
      return '#ff9800';
    case 'rejected':
      return '#f44336';
    default:
      return '#2196f3';
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#000080',
    paddingHorizontal: 20,
    paddingVertical: 20,
    paddingTop: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  status: {
    color: '#fff',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
    fontSize: 12,
    fontWeight: '600',
    alignSelf: 'flex-start',
    overflow: 'hidden',
  },
  content: {
    padding: 20,
  },
  section: {
    marginBottom: 24,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  text: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  infoLabel: {
    fontSize: 12,
    color: '#999',
    fontWeight: '600',
  },
  infoValue: {
    fontSize: 12,
    color: '#333',
    maxWidth: '60%',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 14,
    color: '#999',
  },
});

export default DSEDetailScreen;
