import { Tabs } from 'expo-router';
import { Platform } from 'react-native';

function TabIcon({ name, focused }: { name: string; focused: boolean }) {
  const icons: Record<string, string> = {
    index: '🔮',
    analysis: '👁️',
    recommend: '🏥',
    profile: '👤',
  };
  return null; // emoji in tabBarLabel
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#d4af37',
        tabBarInactiveTintColor: '#666',
        tabBarStyle: {
          backgroundColor: '#1a0a2e',
          borderTopColor: '#2d1a4e',
          height: Platform.OS === 'ios' ? 88 : 64,
          paddingBottom: Platform.OS === 'ios' ? 28 : 8,
        },
        headerStyle: { backgroundColor: '#1a0a2e' },
        headerTintColor: '#d4af37',
        headerTitleStyle: { fontWeight: 'bold', fontSize: 18 },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: '관상사주',
          tabBarLabel: '🔮 홈',
          headerTitle: '관상사주 — 얼굴로 보는 운명',
        }}
      />
      <Tabs.Screen
        name="analysis"
        options={{
          title: '관상 분석',
          tabBarLabel: '👁️ 관상',
          headerTitle: '관상 분석',
        }}
      />
      <Tabs.Screen
        name="recommend"
        options={{
          title: '업체 추천',
          tabBarLabel: '🏥 추천',
          headerTitle: '맞춤 업체 추천',
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: '내 정보',
          tabBarLabel: '👤 내 정보',
          headerTitle: '나의 사주·관상 정보',
        }}
      />
    </Tabs>
  );
}
