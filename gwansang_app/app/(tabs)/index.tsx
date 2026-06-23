import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet, ImageBackground, Dimensions, Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

const FORTUNE_TIPS = [
  '이마가 넓고 맑으면 지혜롭고 발전이 빠릅니다.',
  '눈썹이 짙고 고르면 건강하고 인복이 풍부합니다.',
  '코끝이 둥글고 살집이 있으면 재복이 따릅니다.',
  '입이 크고 입술이 도톰하면 언변이 좋고 사람을 모읍니다.',
  '귀가 크고 귓불이 두꺼우면 장수하고 복록이 깊습니다.',
];

export default function HomeScreen() {
  const router = useRouter();
  const [hasSaju, setHasSaju] = useState(false);
  const [sajuName, setSajuName] = useState('');
  const [tipIndex, setTipIndex] = useState(0);
  const fadeAnim = new Animated.Value(1);

  useEffect(() => {
    (async () => {
      const saju = await AsyncStorage.getItem('saju_info');
      if (saju) {
        const parsed = JSON.parse(saju);
        setHasSaju(true);
        setSajuName(parsed.name || '');
      }
    })();

    const interval = setInterval(() => {
      Animated.sequence([
        Animated.timing(fadeAnim, { toValue: 0, duration: 400, useNativeDriver: true }),
        Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }),
      ]).start();
      setTipIndex((i) => (i + 1) % FORTUNE_TIPS.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <LinearGradient colors={['#1a0a2e', '#0d0620', '#0a1628']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* Hero */}
        <View style={styles.hero}>
          <Text style={styles.heroEmoji}>🔮</Text>
          <Text style={styles.heroTitle}>관상사주</Text>
          <Text style={styles.heroSubtitle}>
            얼굴로 읽는 나의 운명{'\n'}필터 하나로 운을 바꾸다
          </Text>
        </View>

        {/* Tip card */}
        <Animated.View style={[styles.tipCard, { opacity: fadeAnim }]}>
          <Text style={styles.tipLabel}>✨ 오늘의 관상 팁</Text>
          <Text style={styles.tipText}>{FORTUNE_TIPS[tipIndex]}</Text>
        </Animated.View>

        {/* Main actions */}
        <View style={styles.actions}>
          <TouchableOpacity
            style={[styles.mainBtn, styles.primaryBtn]}
            onPress={() => router.push('/analysis')}
          >
            <Text style={styles.mainBtnIcon}>👁️</Text>
            <Text style={styles.mainBtnTitle}>관상 분석 시작</Text>
            <Text style={styles.mainBtnSub}>사진으로 얼굴 운세 파악</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.mainBtn, styles.secondaryBtn]}
            onPress={() => hasSaju ? router.push('/profile') : router.push('/saju-input')}
          >
            <Text style={styles.mainBtnIcon}>📿</Text>
            <Text style={styles.mainBtnTitle}>
              {hasSaju ? `${sajuName}님의 사주` : '사주 정보 입력'}
            </Text>
            <Text style={styles.mainBtnSub}>
              {hasSaju ? '사주와 관상 비교 보기' : '생년월일시로 사주 확인'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Quick links */}
        <Text style={styles.sectionTitle}>빠른 메뉴</Text>
        <View style={styles.quickGrid}>
          {[
            { icon: '💆', label: '에스테틱', path: '/recommend?category=aesthetic' },
            { icon: '💉', label: '반영구', path: '/recommend?category=semi_permanent' },
            { icon: '🦱', label: '두피케어', path: '/recommend?category=scalp_care' },
            { icon: '🖋️', label: '두피문신', path: '/recommend?category=scalp_tattoo' },
            { icon: '🏥', label: '성형외과', path: '/recommend?category=plastic_surgery' },
            { icon: '🔮', label: '운세상담', path: '/recommend?category=fortune' },
          ].map(({ icon, label, path }) => (
            <TouchableOpacity
              key={label}
              style={styles.quickItem}
              onPress={() => router.push(path as any)}
            >
              <Text style={styles.quickIcon}>{icon}</Text>
              <Text style={styles.quickLabel}>{label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Info */}
        <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>관상이 바뀌면 사주가 바뀐다</Text>
          <Text style={styles.infoText}>
            동양 철학에서 관상(觀相)과 사주(四柱)는 서로 영향을 주고받습니다.
            AI 필터로 얼굴을 보정하면 어떤 운이 열리는지 확인해보세요.
            전문 시술로 실제 관상을 개선하면 더 큰 변화를 경험할 수 있습니다.
          </Text>
        </View>

      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { paddingHorizontal: 20, paddingBottom: 40 },
  hero: { alignItems: 'center', paddingTop: 32, paddingBottom: 24 },
  heroEmoji: { fontSize: 72, marginBottom: 8 },
  heroTitle: { fontSize: 36, fontWeight: 'bold', color: '#d4af37', letterSpacing: 2 },
  heroSubtitle: { fontSize: 15, color: '#aaa', textAlign: 'center', marginTop: 8, lineHeight: 22 },
  tipCard: {
    backgroundColor: 'rgba(212,175,55,0.08)',
    borderColor: '#d4af37',
    borderWidth: 1,
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
  },
  tipLabel: { fontSize: 12, color: '#d4af37', marginBottom: 6, fontWeight: '600' },
  tipText: { fontSize: 14, color: '#ddd', lineHeight: 20 },
  actions: { gap: 12, marginBottom: 28 },
  mainBtn: {
    borderRadius: 18,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  primaryBtn: { backgroundColor: 'rgba(212,175,55,0.15)', borderColor: '#d4af37', borderWidth: 1.5 },
  secondaryBtn: { backgroundColor: 'rgba(100,60,180,0.15)', borderColor: '#7b5ea7', borderWidth: 1.5 },
  mainBtnIcon: { fontSize: 32 },
  mainBtnTitle: { fontSize: 18, fontWeight: 'bold', color: '#fff', flex: 1 },
  mainBtnSub: { fontSize: 12, color: '#aaa', position: 'absolute', bottom: 14, left: 68 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#d4af37', marginBottom: 12 },
  quickGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 28 },
  quickItem: {
    width: (width - 60) / 3,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
    borderColor: '#2d1a4e',
    borderWidth: 1,
  },
  quickIcon: { fontSize: 28, marginBottom: 6 },
  quickLabel: { fontSize: 12, color: '#ccc', fontWeight: '600' },
  infoBox: {
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderRadius: 16,
    padding: 20,
    borderColor: '#2d1a4e',
    borderWidth: 1,
  },
  infoTitle: { fontSize: 16, fontWeight: 'bold', color: '#d4af37', marginBottom: 10 },
  infoText: { fontSize: 13, color: '#aaa', lineHeight: 20 },
});
