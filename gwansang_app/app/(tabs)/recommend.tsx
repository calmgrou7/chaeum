import React, { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet, TextInput, Linking, Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { BUSINESS_DATA, BusinessCategory, Business } from '../../constants/businesses';

const { width } = Dimensions.get('window');

const CATEGORIES = [
  { key: 'all', label: '전체', icon: '🏢' },
  { key: 'aesthetic', label: '에스테틱', icon: '💆' },
  { key: 'semi_permanent', label: '반영구', icon: '💉' },
  { key: 'scalp_care', label: '두피케어', icon: '🦱' },
  { key: 'scalp_tattoo', label: '두피문신', icon: '🖋️' },
  { key: 'plastic_surgery', label: '성형외과', icon: '🏥' },
  { key: 'fortune', label: '운세상담', icon: '🔮' },
];

export default function RecommendScreen() {
  const { category: initialCategory } = useLocalSearchParams<{ category?: string }>();
  const [activeCategory, setActiveCategory] = useState(initialCategory || 'all');
  const [search, setSearch] = useState('');
  const router = useRouter();

  const filtered = BUSINESS_DATA.filter((b) => {
    const matchCategory = activeCategory === 'all' || b.category === activeCategory;
    const matchSearch = search === '' ||
      b.name.includes(search) || b.description.includes(search) || b.tags.some(t => t.includes(search));
    return matchCategory && matchSearch;
  });

  return (
    <LinearGradient colors={['#1a0a2e', '#0d0620']} style={styles.container}>
      {/* Search */}
      <View style={styles.searchBar}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.searchInput}
          placeholder="업체명, 시술명 검색"
          placeholderTextColor="#555"
          value={search}
          onChangeText={setSearch}
        />
      </View>

      {/* Category tabs */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.categoryRow}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}
      >
        {CATEGORIES.map(({ key, label, icon }) => (
          <TouchableOpacity
            key={key}
            style={[styles.catBtn, activeCategory === key && styles.catBtnActive]}
            onPress={() => setActiveCategory(key)}
          >
            <Text style={styles.catBtnIcon}>{icon}</Text>
            <Text style={[styles.catBtnLabel, activeCategory === key && styles.catBtnLabelActive]}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Results */}
      <ScrollView contentContainerStyle={styles.list} showsVerticalScrollIndicator={false}>
        <Text style={styles.resultCount}>{filtered.length}개 업체</Text>
        {filtered.map((biz) => (
          <BusinessCard key={biz.id} business={biz} />
        ))}
        {filtered.length === 0 && (
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>🔍</Text>
            <Text style={styles.emptyText}>검색 결과가 없습니다</Text>
          </View>
        )}
      </ScrollView>
    </LinearGradient>
  );
}

function BusinessCard({ business: b }: { business: Business }) {
  const categoryEmoji: Record<string, string> = {
    aesthetic: '💆', semi_permanent: '💉', scalp_care: '🦱',
    scalp_tattoo: '🖋️', plastic_surgery: '🏥', fortune: '🔮',
  };

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardEmoji}>{categoryEmoji[b.category] || '🏢'}</Text>
        <View style={styles.cardTitleArea}>
          <Text style={styles.cardName}>{b.name}</Text>
          <Text style={styles.cardCategory}>{b.categoryLabel}</Text>
        </View>
        <View style={styles.ratingBadge}>
          <Text style={styles.ratingText}>⭐ {b.rating}</Text>
        </View>
      </View>

      <Text style={styles.cardDesc}>{b.description}</Text>

      <View style={styles.gwansangTag}>
        <Text style={styles.gwansangTagText}>🔮 {b.gwansangEffect}</Text>
      </View>

      <View style={styles.tagRow}>
        {b.tags.map((tag) => (
          <View key={tag} style={styles.tag}>
            <Text style={styles.tagText}>{tag}</Text>
          </View>
        ))}
      </View>

      <View style={styles.cardFooter}>
        <Text style={styles.address}>📍 {b.address}</Text>
        <View style={styles.footerBtns}>
          <TouchableOpacity
            style={styles.callBtn}
            onPress={() => Linking.openURL(`tel:${b.phone}`)}
          >
            <Text style={styles.callBtnText}>📞 전화</Text>
          </TouchableOpacity>
          {b.naverMapUrl && (
            <TouchableOpacity
              style={styles.mapBtn}
              onPress={() => Linking.openURL(b.naverMapUrl!)}
            >
              <Text style={styles.mapBtnText}>🗺️ 지도</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.07)',
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 12,
    paddingHorizontal: 14,
    borderColor: '#2d1a4e',
    borderWidth: 1,
  },
  searchIcon: { fontSize: 16, marginRight: 8 },
  searchInput: { flex: 1, height: 44, color: '#fff', fontSize: 15 },
  categoryRow: { marginTop: 12, marginBottom: 4, maxHeight: 60 },
  catBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderColor: '#2d1a4e',
    borderWidth: 1,
  },
  catBtnActive: { backgroundColor: 'rgba(212,175,55,0.2)', borderColor: '#d4af37' },
  catBtnIcon: { fontSize: 15 },
  catBtnLabel: { fontSize: 13, color: '#888', fontWeight: '600' },
  catBtnLabelActive: { color: '#d4af37' },
  list: { paddingHorizontal: 16, paddingBottom: 40, paddingTop: 8 },
  resultCount: { fontSize: 13, color: '#666', marginBottom: 12 },
  card: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 18,
    padding: 16,
    marginBottom: 14,
    borderColor: '#2d1a4e',
    borderWidth: 1,
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10, gap: 10 },
  cardEmoji: { fontSize: 36 },
  cardTitleArea: { flex: 1 },
  cardName: { fontSize: 17, fontWeight: 'bold', color: '#fff' },
  cardCategory: { fontSize: 12, color: '#888', marginTop: 2 },
  ratingBadge: {
    backgroundColor: 'rgba(212,175,55,0.15)',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderColor: '#d4af37',
    borderWidth: 1,
  },
  ratingText: { fontSize: 13, color: '#d4af37', fontWeight: 'bold' },
  cardDesc: { fontSize: 13, color: '#aaa', lineHeight: 19, marginBottom: 10 },
  gwansangTag: {
    backgroundColor: 'rgba(100,60,180,0.15)',
    borderRadius: 8,
    padding: 8,
    marginBottom: 10,
    borderColor: '#7b5ea7',
    borderWidth: 1,
  },
  gwansangTagText: { fontSize: 12, color: '#c4a8f0', fontStyle: 'italic' },
  tagRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 12 },
  tag: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  tagText: { fontSize: 11, color: '#bbb' },
  cardFooter: { borderTopColor: '#2d1a4e', borderTopWidth: 1, paddingTop: 10, gap: 8 },
  address: { fontSize: 12, color: '#777' },
  footerBtns: { flexDirection: 'row', gap: 8 },
  callBtn: {
    backgroundColor: '#d4af37',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  callBtnText: { fontSize: 13, fontWeight: 'bold', color: '#1a0a2e' },
  mapBtn: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderColor: '#444',
    borderWidth: 1,
  },
  mapBtnText: { fontSize: 13, color: '#ccc' },
  empty: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyIcon: { fontSize: 48 },
  emptyText: { fontSize: 15, color: '#555' },
});
