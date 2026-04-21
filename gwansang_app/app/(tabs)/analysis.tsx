import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Image,
  ScrollView, ActivityIndicator, Alert, Dimensions,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { analyzeGwansang } from '../../services/api';

const { width } = Dimensions.get('window');

export default function AnalysisScreen() {
  const router = useRouter();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const pickImage = async (fromCamera: boolean) => {
    const permFn = fromCamera
      ? ImagePicker.requestCameraPermissionsAsync
      : ImagePicker.requestMediaLibraryPermissionsAsync;
    const { status } = await permFn();
    if (status !== 'granted') {
      Alert.alert('권한 필요', '사진 접근 권한이 필요합니다.');
      return;
    }

    const fn = fromCamera
      ? ImagePicker.launchCameraAsync
      : ImagePicker.launchImageLibraryAsync;
    const result = await fn({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.85,
    });

    if (!result.canceled && result.assets[0]) {
      setImageUri(result.assets[0].uri);
    }
  };

  const handleAnalyze = async () => {
    if (!imageUri) return;
    setLoading(true);
    try {
      const result = await analyzeGwansang(imageUri);
      router.push({
        pathname: '/result',
        params: { analysisJson: JSON.stringify(result), imageUri },
      });
    } catch (e) {
      Alert.alert('오류', '분석 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <LinearGradient colors={['#1a0a2e', '#0d0620']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        <Text style={styles.guide}>
          정면을 바라보는 얼굴 사진을 선택하세요.{'\n'}
          밝은 조명에서 찍은 사진이 가장 정확합니다.
        </Text>

        {/* Image display */}
        <View style={styles.imageBox}>
          {imageUri ? (
            <Image source={{ uri: imageUri }} style={styles.preview} />
          ) : (
            <View style={styles.placeholder}>
              <Text style={styles.placeholderIcon}>📸</Text>
              <Text style={styles.placeholderText}>사진을 선택해주세요</Text>
            </View>
          )}
        </View>

        {/* Pick buttons */}
        <View style={styles.pickRow}>
          <TouchableOpacity style={styles.pickBtn} onPress={() => pickImage(true)}>
            <Text style={styles.pickBtnIcon}>📷</Text>
            <Text style={styles.pickBtnLabel}>카메라</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.pickBtn} onPress={() => pickImage(false)}>
            <Text style={styles.pickBtnIcon}>🖼️</Text>
            <Text style={styles.pickBtnLabel}>갤러리</Text>
          </TouchableOpacity>
        </View>

        {/* Analyze button */}
        {imageUri && (
          <TouchableOpacity
            style={[styles.analyzeBtn, loading && styles.analyzeBtnDisabled]}
            onPress={handleAnalyze}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#1a0a2e" />
            ) : (
              <Text style={styles.analyzeBtnText}>👁️ 관상 분석 시작</Text>
            )}
          </TouchableOpacity>
        )}

        {loading && (
          <View style={styles.loadingInfo}>
            <Text style={styles.loadingText}>AI가 관상을 분석하는 중입니다...</Text>
            <Text style={styles.loadingSubText}>이마·눈·코·입·귀·골격을 읽고 있어요</Text>
          </View>
        )}

        {/* How it works */}
        <Text style={styles.sectionTitle}>분석 항목</Text>
        {[
          { icon: '🧠', part: '이마', desc: '지혜·발전운·초년운' },
          { icon: '👀', part: '눈·눈썹', desc: '건강·인복·30대운' },
          { icon: '👃', part: '코', desc: '재물운·40대운·자존심' },
          { icon: '👄', part: '입·인중', desc: '언변·음식복·중년운' },
          { icon: '👂', part: '귀', desc: '장수·조상덕·어린시절' },
          { icon: '🦴', part: '골격·윤곽', desc: '전체 운세·리더십' },
        ].map(({ icon, part, desc }) => (
          <View key={part} style={styles.partRow}>
            <Text style={styles.partIcon}>{icon}</Text>
            <View>
              <Text style={styles.partName}>{part}</Text>
              <Text style={styles.partDesc}>{desc}</Text>
            </View>
          </View>
        ))}

      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: 20, paddingBottom: 40 },
  guide: { fontSize: 14, color: '#aaa', textAlign: 'center', marginBottom: 20, lineHeight: 20 },
  imageBox: {
    width: width - 40,
    height: (width - 40) * 1.2,
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#1a0a2e',
    borderColor: '#2d1a4e',
    borderWidth: 2,
    marginBottom: 16,
    alignSelf: 'center',
  },
  preview: { width: '100%', height: '100%' },
  placeholder: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  placeholderIcon: { fontSize: 64 },
  placeholderText: { fontSize: 15, color: '#555' },
  pickRow: { flexDirection: 'row', gap: 12, marginBottom: 20 },
  pickBtn: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
    borderColor: '#2d1a4e',
    borderWidth: 1,
  },
  pickBtnIcon: { fontSize: 28, marginBottom: 4 },
  pickBtnLabel: { fontSize: 14, color: '#ccc', fontWeight: '600' },
  analyzeBtn: {
    backgroundColor: '#d4af37',
    borderRadius: 16,
    padding: 18,
    alignItems: 'center',
    marginBottom: 16,
  },
  analyzeBtnDisabled: { opacity: 0.6 },
  analyzeBtnText: { fontSize: 18, fontWeight: 'bold', color: '#1a0a2e' },
  loadingInfo: { alignItems: 'center', marginBottom: 24, gap: 4 },
  loadingText: { fontSize: 14, color: '#d4af37' },
  loadingSubText: { fontSize: 12, color: '#777' },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#d4af37', marginBottom: 14, marginTop: 8 },
  partRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderColor: '#2d1a4e',
    borderWidth: 1,
  },
  partIcon: { fontSize: 28 },
  partName: { fontSize: 15, fontWeight: 'bold', color: '#fff', marginBottom: 2 },
  partDesc: { fontSize: 12, color: '#888' },
});
