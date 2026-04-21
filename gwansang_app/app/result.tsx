import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Image, Dimensions, Share,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useLocalSearchParams, useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { GwansangAnalysis } from '../services/api';

const { width } = Dimensions.get('window');

const FORTUNE_COLORS: Record<string, string> = {
  '대길': '#d4af37', '길': '#4caf50', '평': '#888', '흉': '#ff7043',
};

export default function ResultScreen() {
  const { analysisJson, imageUri } = useLocalSearchParams<{ analysisJson: string; imageUri: string }>();
  const router = useRouter();
  const analysis: GwansangAnalysis = analysisJson ? JSON.parse(analysisJson) : null;

  useEffect(() => {
    if (analysis) saveToHistory();
  }, []);

  const saveToHistory = async () => {
    const raw = await AsyncStorage.getItem('analysis_history');
    const history = raw ? JSON.parse(raw) : [];
    history.unshift({ date: new Date().toISOString(), overall: analysis.overallFortune, imageUri });
    if (history.length > 20) history.pop();
    await AsyncStorage.setItem('analysis_history', JSON.stringify(history));
  };

  const handleShare = async () => {
    await Share.share({
      message: `관상사주 분석 결과\n\n종합 운세: ${analysis?.overallFortune}\n\n관상사주 앱에서 나의 운세를 확인해보세요!`,
    });
  };

  if (!analysis) {
    return (
      <LinearGradient colors={['#1a0a2e', '#0d0620']} style={styles.container}>
        <View style={styles.center}>
          <Text style={styles.errorText}>분석 결과를 불러올 수 없습니다.</Text>
        </View>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient colors={['#1a0a2e', '#0d0620']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* Photo + overall */}
        <View style={styles.topSection}>
          {imageUri && (
            <Image source={{ uri: imageUri }} style={styles.photo} />
          )}
          <View style={styles.overallBox}>
            <Text style={styles.overallLabel}>종합 운세</Text>
            <Text style={[styles.overallValue, { color: FORTUNE_COLORS[analysis.overallFortune] || '#fff' }]}>
              {analysis.overallFortune}
            </Text>
            <Text style={styles.overallScore}>운세 점수 {analysis.fortuneScore}점</Text>
          </View>
        </View>

        <Text style={styles.summary}>{analysis.summary}</Text>

        {/* Part-by-part analysis */}
        <Text style={styles.sectionTitle}>부위별 관상 분석</Text>
        {analysis.parts.map((part) => (
          <View key={part.name} style={styles.partCard}>
            <View style={styles.partHeader}>
              <Text style={styles.partEmoji}>{part.emoji}</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.partName}>{part.name}</Text>
                <Text style={styles.partAspect}>{part.aspect}</Text>
              </View>
              <View style={[styles.fortuneBadge, { backgroundColor: `${FORTUNE_COLORS[part.fortune] || '#555'}22`, borderColor: FORTUNE_COLORS[part.fortune] || '#555' }]}>
                <Text style={[styles.fortuneText, { color: FORTUNE_COLORS[part.fortune] || '#fff' }]}>{part.fortune}</Text>
              </View>
            </View>
            <Text style={styles.partDesc}>{part.description}</Text>
            <Text style={styles.partAdvice}>💡 {part.advice}</Text>
          </View>
        ))}

        {/* Saju compatibility */}
        {analysis.sajuCompatibility && (
          <>
            <Text style={styles.sectionTitle}>사주와의 상관관계</Text>
            <View style={styles.sajuCard}>
              <Text style={styles.sajuCompatText}>{analysis.sajuCompatibility}</Text>
            </View>
          </>
        )}

        {/* Filter recommendation */}
        <Text style={styles.sectionTitle}>관상 보정 필터 추천</Text>
        <View style={styles.filterCard}>
          <Text style={styles.filterTitle}>추천 필터: {analysis.recommendedFilter}</Text>
          <Text style={styles.filterDesc}>{analysis.filterReason}</Text>
          <TouchableOpacity
            style={styles.filterBtn}
            onPress={() => router.push({ pathname: '/filter', params: { imageUri, filter: analysis.recommendedFilter } })}
          >
            <Text style={styles.filterBtnText}>✨ 필터 적용해보기</Text>
          </TouchableOpacity>
        </View>

        {/* Treatment recommendations */}
        <Text style={styles.sectionTitle}>관상 개선 추천 시술</Text>
        {analysis.treatmentRecommendations.map((rec, i) => (
          <TouchableOpacity
            key={i}
            style={styles.treatCard}
            onPress={() => router.push(`/recommend?category=${rec.category}` as any)}
          >
            <Text style={styles.treatEmoji}>{rec.emoji}</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.treatName}>{rec.treatment}</Text>
              <Text style={styles.treatReason}>{rec.reason}</Text>
            </View>
            <Text style={styles.treatArrow}>›</Text>
          </TouchableOpacity>
        ))}

        {/* Actions */}
        <View style={styles.actions}>
          <TouchableOpacity style={styles.shareBtn} onPress={handleShare}>
            <Text style={styles.shareBtnText}>🔗 공유하기</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.retryBtn} onPress={() => router.back()}>
            <Text style={styles.retryBtnText}>다시 분석하기</Text>
          </TouchableOpacity>
        </View>

      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: 20, paddingBottom: 40 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  errorText: { fontSize: 16, color: '#888' },
  topSection: { flexDirection: 'row', gap: 14, marginBottom: 16, alignItems: 'center' },
  photo: { width: 110, height: 145, borderRadius: 14, borderColor: '#d4af37', borderWidth: 1.5 },
  overallBox: { flex: 1, alignItems: 'center', gap: 4 },
  overallLabel: { fontSize: 13, color: '#888' },
  overallValue: { fontSize: 36, fontWeight: 'bold' },
  overallScore: { fontSize: 14, color: '#888' },
  summary: { fontSize: 14, color: '#bbb', lineHeight: 21, marginBottom: 20, backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: 14 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#d4af37', marginBottom: 12, marginTop: 8 },
  partCard: { backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 14, padding: 14, marginBottom: 10, borderColor: '#2d1a4e', borderWidth: 1 },
  partHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 10 },
  partEmoji: { fontSize: 28 },
  partName: { fontSize: 15, fontWeight: 'bold', color: '#fff' },
  partAspect: { fontSize: 12, color: '#888', marginTop: 2 },
  fortuneBadge: { borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4, borderWidth: 1 },
  fortuneText: { fontSize: 14, fontWeight: 'bold' },
  partDesc: { fontSize: 13, color: '#bbb', lineHeight: 19, marginBottom: 6 },
  partAdvice: { fontSize: 12, color: '#9b8cc4', fontStyle: 'italic' },
  sajuCard: { backgroundColor: 'rgba(100,60,180,0.1)', borderRadius: 14, padding: 14, marginBottom: 16, borderColor: '#7b5ea7', borderWidth: 1 },
  sajuCompatText: { fontSize: 13, color: '#c4a8f0', lineHeight: 20 },
  filterCard: { backgroundColor: 'rgba(212,175,55,0.08)', borderRadius: 14, padding: 16, marginBottom: 16, borderColor: '#d4af37', borderWidth: 1 },
  filterTitle: { fontSize: 16, fontWeight: 'bold', color: '#d4af37', marginBottom: 6 },
  filterDesc: { fontSize: 13, color: '#aaa', lineHeight: 18, marginBottom: 12 },
  filterBtn: { backgroundColor: '#d4af37', borderRadius: 10, padding: 12, alignItems: 'center' },
  filterBtnText: { fontSize: 15, fontWeight: 'bold', color: '#1a0a2e' },
  treatCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: 12, marginBottom: 8, gap: 12, borderColor: '#2d1a4e', borderWidth: 1 },
  treatEmoji: { fontSize: 28 },
  treatName: { fontSize: 14, fontWeight: 'bold', color: '#fff', marginBottom: 2 },
  treatReason: { fontSize: 12, color: '#888' },
  treatArrow: { fontSize: 22, color: '#555' },
  actions: { flexDirection: 'row', gap: 10, marginTop: 20 },
  shareBtn: { flex: 1, backgroundColor: '#d4af37', borderRadius: 12, padding: 14, alignItems: 'center' },
  shareBtnText: { fontSize: 15, fontWeight: 'bold', color: '#1a0a2e' },
  retryBtn: { flex: 1, backgroundColor: 'rgba(255,255,255,0.07)', borderRadius: 12, padding: 14, alignItems: 'center', borderColor: '#444', borderWidth: 1 },
  retryBtnText: { fontSize: 15, color: '#ccc' },
});
