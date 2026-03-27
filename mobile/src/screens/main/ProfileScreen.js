import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { useAuthStore } from '../../store/authStore';

const ProfileScreen = ({ navigation }) => {
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    Alert.alert(
      'Выход',
      'Вы уверены, что хотите выйти?',
      [
        { text: 'Отмена', onPress: () => {} },
        {
          text: 'Выход',
          onPress: () => logout(),
          style: 'destructive',
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <MaterialIcons name="person" size={48} color="#fff" />
        </View>
        <Text style={styles.name}>{user?.full_name || 'Anonymous'}</Text>
        <Text style={styles.email}>{user?.email}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Информация аккаунта</Text>
        <MenuRow
          icon="email"
          label="Email"
          value={user?.email}
          onPress={() => {}}
        />
        <MenuRow
          icon="phone"
          label="Телефон"
          value={user?.phone || 'Не указан'}
          onPress={() => {}}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Действия</Text>
        <MenuItem
          icon="edit"
          label="Изменить профиль"
          onPress={() => {}}
        />
        <MenuItem
          icon="lock"
          label="Изменить пароль"
          onPress={() => {}}
        />
        <MenuItem
          icon="notifications"
          label="Уведомления"
          onPress={() => {}}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Приложение</Text>
        <MenuRow
          icon="info"
          label="Версия"
          value="1.0.0"
          onPress={() => {}}
        />
        <MenuItem
          icon="help"
          label="Справка и поддержка"
          onPress={() => {}}
        />
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <MaterialIcons name="logout" size={20} color="#f44336" />
        <Text style={styles.logoutText}>Выход</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const MenuItem = ({ icon, label, onPress }) => (
  <TouchableOpacity style={styles.menuItem} onPress={onPress}>
    <MaterialIcons name={icon} size={20} color="#000080" />
    <Text style={styles.menuLabel}>{label}</Text>
    <MaterialIcons name="chevron-right" size={20} color="#ccc" />
  </TouchableOpacity>
);

const MenuRow = ({ icon, label, value, onPress }) => (
  <TouchableOpacity style={styles.menuItem} onPress={onPress}>
    <MaterialIcons name={icon} size={20} color="#000080" />
    <View style={styles.menuContent}>
      <Text style={styles.menuLabel}>{label}</Text>
      <Text style={styles.menuValue}>{value}</Text>
    </View>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#000080',
    paddingVertical: 40,
    paddingTop: 50,
    alignItems: 'center',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  email: {
    fontSize: 12,
    color: '#ddd',
  },
  section: {
    marginTop: 24,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#999',
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 1,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  menuContent: {
    flex: 1,
    marginLeft: 12,
  },
  menuLabel: {
    fontSize: 14,
    color: '#333',
    marginRight: 12,
  },
  menuValue: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginVertical: 20,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#f44336',
  },
  logoutText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: '#f44336',
  },
});

export default ProfileScreen;
