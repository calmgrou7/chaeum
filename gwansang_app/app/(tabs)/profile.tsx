import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { calculateSaju, SajuResult } from '../../services/saju';

export default function ProfileScreen() {
  const router = useRouter();
  const [sajuInfo, setSajuInfo] = useState<any>(null);
  const [sajuResult, setSajuResult] = useState<SajuResult | null>(null);
  const [analysisHistory, setAnalysisHistory] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const saju = await AsyncStorage.getItem('saju_info');
    const history = await AsyncStorage.getItem('analysis_history');
    if (saju) {
      const parsed = JSON.parse(saju);
      setSajuInfo(parsed);
      setSajuResult(calculateSaju(parsed.birthYear, parsed.birthMonth, parsed.birthDay, parsed.birthHour));
    }
    if (history) setAnalysisHistory(JSON.parse(history));
  };

  const clearData = () => {
    Alert.alert('초기화', '모든 데이터를 삭제하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '삭제', style: 'destructive',
        onPress: async () => {
          await AsyncStorage.multiRemove(['saju_info', 'analysis_history']);
          setSajuInfo(null);
          setSajuResult(null);
          setAnalysisHistory([]);
        },
      },
    ]);
  };

  if (!sajuInfo) {
    return (
      <LinearGradient colors={['#1a0a2e', '#0d0620']} style={styles.container}>
        <View style={styles.empty}>
          <Text style={styles.emptyIcon}>📿</Text>
          <Text style={styles.emptyTitle}>사주 정보가 없습니다</Text>
          <Text style={styles.emptyDesc}>생년월일시를 입력하면 나만의 사주를 확인하고 관상과 비교할 수 있습니다.</Text>
          <TouchableOpacity style={styles.inputBtn} onPress={() => router.push('/saju-input')}>
            <Text style={styles.inputBtnText}>사주 정보 입력하기</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient colors={['#1a0a2e', '#0d0620']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* Profile header */}
        <View style={styles.profileHeader}>
          <Text style={styles.profileEmoji}>👤</Text>
          <Text style={styles.profileName}>{sajuInfo.name}</Text>
          <Text style={styles.profileBirth}>
            {sajuInfo.birthYear}년 {sajuInfo.birthMonth}월 {sajuInfo.birthDay}일 {sajuInfo.birthHour}시
          </Text>
          <TouchableOpacity onPress={() => router.push('/saju-input')}>
            <Text style={styles.editLink}>✏️ 수정</Text>
          </TouchableOpacity>
        </View>

        {/* Saju pillars */}
        {sajuResult && (
          <>
            <Text style={styles.sectionTitle}>나의 사주 (四柱)</Text>
            <View style={styles.pillarsRow}>
              {[
                { label: '年柱', stem: sajuResult.yearPillar.stem, branch: sajuResult.yearPillar.branch },
                { label: '月柱', stem: sajuResult.monthPillar.stem, branch: sajuResult.monthPillar.branch },
                { label: '日柱', stem: sajuResult.dayPillar.stem, branch: sajuResult.dayPillar.branch },
                { label: '時柱', stem: sajuResult.hourPillar.stem, branch: sajuResult.hourPillar.branch },
              ].map(({ label, stem, branch }) => (
                <View key={label} style={styles.pillar}>
                  <Text style={styles.pillarLabel}>{label}</Text>
                  <Text style={styles.pillarStem}>{stem}</Text>
                  <Text style={styles.pillarBranch}>{branch}</Text>
                </View>
              ))}
            </View>

            <Text style={styles.sectionTitle}>오행 분석</Text>
            <View style={styles.elementGrid}>
              {Object.entries(sajuResult.elements).map(([element, count]) => (
                <View key={element} style={styles.elementItem}>
                  <Text style={styles.elementName}>{element}</Text>
                  <View style={styles.elementBar}>
                    <View style={[styles.elementFill, { width: `${(count as number) * 20}%` }]} />
                  </View>
                  <Text style={styles.elementCount}>{count}개</Text>
                </View>
              ))}
            </View>

            <Text style={styles.sectionTitle}>관상-사주 상관관계</Text>
            {sajuResult.gwansangCorrelations.map((c, i) => (
              <View key={i} style={styles.correlationCard}>
                <Text style={styles.correlationTitle}>{c.feature}</Text>
                <Text style={styles.correlationDesc}>{c.description}</Text>
                <Text style={styles.correlationAdvice}>💡 {c.advice}</Text>
              </View>
            ))}
          </>
        )}

        {/* History */}
        {analysisHistory.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>분석 이력 ({analysisHistory.length}회)</Text>
            {analysisHistory.slice(0, 3).map((h, i) => (
              <View key={i} style={styles.historyCard}>
                <Text style={styles.historyDate}>{new Date(h.date).toLocaleDateString('ko-KR')}</Text>
                <Text style={styles.historyOverall}>종합 운세: {h.overall}</Text>
              </View>
            ))}
          </>
        )}

        <TouchableOpacity style={styles.clearBtn} onPress={clearData}>
          <Text style={styles.clearBtnText}>🗑️ 데이터 초기화</Text>
        </TouchableOpacity>

      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: 20, paddingBottom: 40 },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40, gap: 14 },
  emptyIcon: { fontSize: 72, marginBottom: 8 },
  emptyTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  emptyDesc: { fontSize: 14, color: '#888', textAlign: 'center', lineHeight: 20 },
  inputBtn: {
    backgroundColor: '#d4af37', borderRadius: 14, paddingHorizontal: 28, paddingVertical: 14, marginTop: 8,
  },
  inputBtnText: { fontSize: 16, fontWeight: 'bold', color: '#1a0a2e' },
  profileHeader: {
    alignItems: 'center', backgroundColor: 'rgba(212,175,55,0.08)',
    borderRadius: 20, padding: 24, marginBottom: 24, borderColor: '#d4af37', borderWidth: 1,
  },
  profileEmoji: { fontSize: 56, marginBottom: 8 },
  profileName: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 4 },
  profileBirth: { fontSize: 14, color: '#aaa', marginBottom: 8 },
  editLink: { fontSize: 14, color: '#d4af37' },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#d4af37', marginBottom: 12, marginTop: 8 },
  pillarsRow: { flexDirection: 'row', gap: 8, marginBottom: 20 },
  pillar: {
    flex: 1, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 12,
    padding: 12, alignItems: 'center', borderColor: '#2d1a4e', borderWidth: 1,
  },
  pillarLabel: { fontSize: 11, color: '#d4af37', marginBottom: 6, fontWeight: '600' },
  pillarStem: { fontSize: 22, fontWeight: 'bold', color: '#fff', marginBottom: 2 },
  pillarBranch: { fontSize: 22, color: '#c4a8f0' },
  elementGrid: { gap: 8, marginBottom: 20 },
  elementItem: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  elementName: { fontSize: 14, color: '#ccc', width: 30 },
  elementBar: { flex: 1, height: 8, backgroundColor: '#2d1a4e', borderRadius: 4 },
  elementFill: { height: '100%', backgroundColor: '#d4af37', borderRadius: 4 },
  elementCount: { fontSize: 12, color: '#888', width: 24, textAlign: 'right' },
  correlationCard: {
    backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 14,
    padding: 14, marginBottom: 10, borderColor: '#2d1a4e', borderWidth: 1,
  },
  correlationTitle: { fontSize: 15, fontWeight: 'bold', color: '#d4af37', marginBottom: 6 },
  correlationDesc: { fontSize: 13, color: '#bbb', lineHeight: 18, marginBottom: 6 },
  correlationAdvice: { fontSize: 12, color: '#9b8cc4', fontStyle: 'italic' },
  historyCard: {
    backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 12,
    padding: 12, marginBottom: 8, flexDirection: 'row', justifyContent: 'space-between',
    borderColor: '#2d1a4e', borderWidth: 1,
  },
  historyDate: { fontSize: 13, color: '#888' },
  historyOverall: { fontSize: 13, color: '#d4af37' },
  clearBtn: {
    marginTop: 24, padding: 14, borderRadius: 12,
    backgroundColor: 'rgba(255,50,50,0.1)', borderColor: '#ff4444', borderWidth: 1, alignItems: 'center',
  },
  clearBtnText: { fontSize: 14, color: '#ff6666' },
});
