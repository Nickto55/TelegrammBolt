import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { useAuthStore } from '../../store/authStore';
import { useDSEStore } from '../../store/dseStore';

const DashboardScreen = ({ navigation }) => {
  const { user } = useAuthStore();
  const { dseList, isLoading, getDSEList } = useDSEStore();
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      await getDSEList(1);
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось загрузить данные');
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await getDSEList(1);
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.greeting}>Добро пожаловать, {user?.full_name}!</Text>
        <Text style={styles.date}>{new Date().toLocaleDateString('ru-RU')}</Text>
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{dseList.length}</Text>
          <Text style={styles.statLabel}>Записей DSE</Text>
        </View>

        <View style={styles.statCard}>
          <Text style={styles.statValue}>0</Text>
          <Text style={styles.statLabel}>Сообщений</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Последние записи</Text>
        {isLoading ? (
          <ActivityIndicator size="large" color="#000080" />
        ) : dseList.length > 0 ? (
          dseList.slice(0, 3).map((dse) => (
            <View key={dse.id} style={styles.card}>
              <Text style={styles.cardTitle}>{dse.name}</Text>
              <Text style={styles.cardSubtitle}>
                {dse.status || 'В работе'}
              </Text>
            </View>
          ))
        ) : (
          <Text style={styles.emptyText}>Записей не найдено</Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Быстрые действия</Text>
        <View style={styles.actionContainer}>
          <View style={styles.actionButton}>
            <Text style={styles.actionButtonText}>📝 Создать DSE</Text>
          </View>
          <View style={styles.actionButton}>
            <Text style={styles.actionButtonText}>💬 Сообщения</Text>
          </View>
        </View>
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
    paddingVertical: 20,
    paddingTop: 40,
  },
  greeting: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  date: {
    fontSize: 12,
    color: '#ddd',
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 10,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000080',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  section: {
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#000080',
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 12,
    color: '#999',
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    fontSize: 14,
    paddingVertical: 20,
  },
  actionContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#000080',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
});

export default DashboardScreen;
