import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { useDSEStore } from '../../store/dseStore';

const DSEListScreen = ({ navigation }) => {
  const { dseList, isLoading, pagination, getDSEList, searchDSE } = useDSEStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDSEList();
  }, []);

  const loadDSEList = async () => {
    try {
      await getDSEList(1);
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось загрузить список DSE');
    }
  };

  const handleSearch = async () => {
    if (searchQuery.trim()) {
      try {
        await searchDSE(searchQuery);
      } catch (error) {
        Alert.alert('Ошибка', 'Ошибка при поиске');
      }
    } else {
      await loadDSEList();
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await loadDSEList();
    } finally {
      setRefreshing(false);
    }
  };

  const handleDSEPress = (dse) => {
    navigation.navigate('DSEDetail', { dseId: dse.id });
  };

  const renderDSEItem = ({ item }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => handleDSEPress(item)}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle}>{item.name}</Text>
        <Text style={[styles.badge, { backgroundColor: getStatusColor(item.status) }]}>
          {item.status || 'В работе'}
        </Text>
      </View>
      <Text style={styles.cardDescription} numberOfLines={2}>
        {item.description || 'Без описания'}
      </Text>
      <View style={styles.cardFooter}>
        <Text style={styles.cardDate}>
          {new Date(item.created_at).toLocaleDateString('ru-RU')}
        </Text>
        <MaterialIcons name="chevron-right" size={20} color="#999" />
      </View>
    </TouchableOpacity>
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

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Записи DSE</Text>
      </View>

      <View style={styles.searchContainer}>
        <MaterialIcons name="search" size={20} color="#999" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Поиск..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={handleSearch}
          placeholderTextColor="#999"
        />
      </View>

      {isLoading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#000080" />
        </View>
      ) : (
        <FlatList
          data={dseList}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderDSEItem}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <MaterialIcons name="folder-open" size={48} color="#ccc" />
              <Text style={styles.emptyText}>Записей не найдено</Text>
            </View>
          }
        />
      )}

      <TouchableOpacity
        style={styles.fab}
        onPress={() => navigation.navigate('CreateDSE')}
      >
        <MaterialIcons name="add" size={24} color="#fff" />
      </TouchableOpacity>
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
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginTop: 16,
    marginBottom: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    paddingHorizontal: 12,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    padding: 12,
    fontSize: 14,
  },
  listContainer: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 80,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    color: '#fff',
    fontSize: 10,
    fontWeight: '600',
    overflow: 'hidden',
  },
  cardDescription: {
    fontSize: 12,
    color: '#666',
    marginBottom: 8,
    lineHeight: 16,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardDate: {
    fontSize: 11,
    color: '#999',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    color: '#999',
    fontSize: 14,
    marginTop: 12,
  },
  fab: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#000080',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
});

export default DSEListScreen;
