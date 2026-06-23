import { DarkTheme, ThemeProvider } from '@react-navigation/native';
import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded] = useFonts({});

  useEffect(() => {
    if (loaded) SplashScreen.hideAsync();
  }, [loaded]);

  if (!loaded) return null;

  return (
    <ThemeProvider value={DarkTheme}>
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: '#1a0a2e' },
          headerTintColor: '#d4af37',
          headerTitleStyle: { fontWeight: 'bold' },
          contentStyle: { backgroundColor: '#0d0620' },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="saju-input"
          options={{ title: '사주 정보 입력', presentation: 'modal' }}
        />
        <Stack.Screen
          name="result"
          options={{ title: '관상 분석 결과' }}
        />
        <Stack.Screen
          name="filter"
          options={{ title: '관상 보정 필터' }}
        />
        <Stack.Screen
          name="business-detail"
          options={{ title: '업체 상세' }}
        />
      </Stack>
      <StatusBar style="light" />
    </ThemeProvider>
  );
}
