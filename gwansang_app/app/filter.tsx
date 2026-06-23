import React, { useState, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Image, Dimensions, Alert, Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImageManipulator from 'expo-image-manipulator';
import * as MediaLibrary from 'expo-media-library';
import { useLocalSearchParams, useRouter } from 'expo-router';

const { width } = Dimensions.get('window');
const PREVIEW_SIZE = width - 40;

const FILTERS = [
  {
    id: 'natural',
    name: '자연 밝음',
    emoji: '☀️',
    description: '밝고 맑은 인상 → 이마 운이 좋아집니다',
    fortuneEffect: '발전운·지혜운 상승',
    config: { brightness: 0.15, contrast: 0.05, saturation: 0.1 },
  },
  {
    id: 'warm',
    name: '따뜻한 피부',
    emoji: '🌅',
    description: '따뜻한 톤으로 건강한 인상 → 재물운이 향상됩니다',
    fortuneEffect: '재물운·건강운 상승',
    config: { brightness: 0.05, contrast: 0.1, saturation: 0.2 },
  },
  {
    id: 'clarity',
    name: '맑은 인상',
    emoji: '💎',
    description: '피부 결이 고르고 맑아 보여 → 인복이 풍성해집니다',
    fortuneEffect: '인복·사교운 상승',
    config: { brightness: 0.1, contrast: -0.05, saturation: -0.05 },
  },
  {
    id: 'prominent',
    name: '입체감 강조',
    emoji: '🗿',
    description: '골격을 뚜렷하게 강조 → 리더십과 권위가 높아집니다',
    fortuneEffect: '리더십·명예운 상승',
    config: { brightness: -0.05, contrast: 0.2, saturation: 0 },
  },
  {
    id: 'gentle',
    name: '온화한 인상',
    emoji: '🌸',
    description: '부드럽고 친근한 느낌 → 귀인의 도움이 따릅니다',
    fortuneEffect: '귀인운·연애운 상승',
    config: { brightness: 0.08, contrast: -0.1, saturation: 0.15 },
  },
  {
    id: 'confident',
    name: '자신감 있는',
    emoji: '👑',
    description: '강하고 당당한 인상 → 성공운과 출세운이 강해집니다',
    fortuneEffect: '출세운·성공운 상승',
    config: { brightness: 0, contrast: 0.15, saturation: 0.05 },
  },
];

export default function FilterScreen() {
  const { imageUri: initialUri, filter: initialFilter } = useLocalSearchParams<{
    imageUri: string;
    filter?: string;
  }>();
  const [activeFilter, setActiveFilter] = useState(
    FILTERS.find((f) => f.name === initialFilter) || FILTERS[0]
  );
  const [processedUri, setProcessedUri] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const router = useRouter();

  const applyFilter = async (filter: typeof FILTERS[0]) => {
    if (!initialUri) return;
    setActiveFilter(filter);
    setProcessing(true);
    try {
      const result = await ImageManipulator.manipulateAsync(
        initialUri,
        [],
        {
          compress: 0.85,
          format: ImageManipulator.SaveFormat.JPEG,
        }
      );
      setProcessedUri(result.uri);
    } catch (e) {
      console.error(e);
    } finally {
      setProcessing(false);
    }
  };

  const saveImage = async () => {
    const uri = processedUri || initialUri;
    if (!uri) return;
    const { status } = await MediaLibrary.requestPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('권한 필요', '사진을 저장하려면 미디어 라이브러리 접근 권한이 필요합니다.');
      return;
    }
    await MediaLibrary.saveToLibraryAsync(uri);
    Alert.alert('저장 완료', '보정된 사진이 갤러리에 저장되었습니다.');
  };

  const currentUri = processedUri || initialUri;

  return (
    <LinearGradient colors={['#1a0a2e', '#0d0620']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* Preview */}
        <View style={styles.previewContainer}>
          {currentUri ? (
            <Image source={{ uri: currentUri }} style={styles.preview} />
          ) : (
            <View style={styles.previewEmpty}>
              <Text style={styles.previewEmptyText}>사진을 선택해주세요</Text>
            </View>
          )}
          {processing && (
            <View style={styles.processingOverlay}>
              <Text style={styles.processingText}>✨ 필터 적용 중...</Text>
            </View>
          )}
        </View>

        {/* Active filter effect info */}
        <View style={styles.effectCard}>
          <Text style={styles.effectEmoji}>{activeFilter.emoji}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.effectName}>{activeFilter.name} 필터</Text>
            <Text style={styles.effectFortune}>🔮 {activeFilter.fortuneEffect}</Text>
          </View>
        </View>
        <Text style={styles.effectDesc}>{activeFilter.description}</Text>

        {/* Filter options */}
        <Text style={styles.sectionTitle}>필터 선택</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ gap: 10, paddingBottom: 8 }}
        >
          {FILTERS.map((f) => (
            <TouchableOpacity
              key={f.id}
              style={[styles.filterThumb, activeFilter.id === f.id && styles.filterThumbActive]}
              onPress={() => applyFilter(f)}
            >
              <Text style={styles.filterThumbEmoji}>{f.emoji}</Text>
              <Text style={[styles.filterThumbName, activeFilter.id === f.id && styles.filterThumbNameActive]}>
                {f.name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Fortune explanation */}
        <Text style={styles.sectionTitle}>왜 관상이 바뀌면 사주가 바뀔까?</Text>
        <View style={styles.infoCard}>
          <Text style={styles.infoText}>
            동양 철학에서는 사람의 얼굴이 운명을 반영하는 동시에 운명을 만들어간다고 봅니다.
            {'\n\n'}인상이 바뀌면 주변 사람들의 반응이 달라지고, 그에 따라 기회와 인연도 달라집니다.
            이를 <Text style={styles.infoHighlight}>심상(心相)</Text>이 관상을 바꾸고, 관상이 운명을 바꾼다고 표현합니다.
            {'\n\n'}전문적인 시술을 통해 관상을 개선하면 더 크고 지속적인 변화를 경험할 수 있습니다.
          </Text>
        </View>

        {/* Recommend treatment button */}
        <TouchableOpacity
          style={styles.treatBtn}
          onPress={() => router.push('/recommend' as any)}
        >
          <Text style={styles.treatBtnText}>🏥 관련 시술 업체 보기</Text>
        </TouchableOpacity>

        {/* Save button */}
        <TouchableOpacity style={styles.saveBtn} onPress={saveImage}>
          <Text style={styles.saveBtnText}>💾 보정 사진 저장</Text>
        </TouchableOpacity>

      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: 20, paddingBottom: 40 },
  previewContainer: {
    width: PREVIEW_SIZE, height: PREVIEW_SIZE * 1.2,
    borderRadius: 20, overflow: 'hidden',
    backgroundColor: '#1a0a2e', marginBottom: 14,
    borderColor: '#2d1a4e', borderWidth: 2, alignSelf: 'center', position: 'relative',
  },
  preview: { width: '100%', height: '100%' },
  previewEmpty: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  previewEmptyText: { fontSize: 15, color: '#555' },
  processingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(26,10,46,0.7)',
    alignItems: 'center', justifyContent: 'center',
  },
  processingText: { fontSize: 16, color: '#d4af37' },
  effectCard: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: 'rgba(212,175,55,0.08)', borderRadius: 14, padding: 14,
    marginBottom: 8, borderColor: '#d4af37', borderWidth: 1,
  },
  effectEmoji: { fontSize: 36 },
  effectName: { fontSize: 16, fontWeight: 'bold', color: '#fff', marginBottom: 4 },
  effectFortune: { fontSize: 13, color: '#d4af37' },
  effectDesc: { fontSize: 13, color: '#aaa', marginBottom: 20, lineHeight: 18 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: '#d4af37', marginBottom: 12 },
  filterThumb: {
    alignItems: 'center', padding: 12, borderRadius: 14, minWidth: 90,
    backgroundColor: 'rgba(255,255,255,0.05)', borderColor: '#2d1a4e', borderWidth: 1,
  },
  filterThumbActive: { borderColor: '#d4af37', backgroundColor: 'rgba(212,175,55,0.12)' },
  filterThumbEmoji: { fontSize: 28, marginBottom: 4 },
  filterThumbName: { fontSize: 11, color: '#888', textAlign: 'center' },
  filterThumbNameActive: { color: '#d4af37' },
  infoCard: {
    backgroundColor: 'rgba(100,60,180,0.1)', borderRadius: 14, padding: 16,
    marginBottom: 16, borderColor: '#7b5ea7', borderWidth: 1,
  },
  infoText: { fontSize: 13, color: '#c4a8f0', lineHeight: 21 },
  infoHighlight: { color: '#d4af37', fontWeight: 'bold' },
  treatBtn: {
    backgroundColor: 'rgba(255,255,255,0.06)', borderRadius: 14, padding: 16,
    alignItems: 'center', marginBottom: 10, borderColor: '#444', borderWidth: 1,
  },
  treatBtnText: { fontSize: 15, color: '#ccc', fontWeight: '600' },
  saveBtn: {
    backgroundColor: '#d4af37', borderRadius: 14, padding: 16, alignItems: 'center',
  },
  saveBtnText: { fontSize: 16, fontWeight: 'bold', color: '#1a0a2e' },
});
