import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

const HOURS = Array.from({ length: 24 }, (_, i) => i);

export default function SajuInputScreen() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthDay, setBirthDay] = useState('');
  const [birthHour, setBirthHour] = useState(12);
  const [gender, setGender] = useState<'male' | 'female'>('male');

  const handleSave = async () => {
    if (!name.trim()) { Alert.alert('이름을 입력해주세요.'); return; }
    const year = parseInt(birthYear);
    const month = parseInt(birthMonth);
    const day = parseInt(birthDay);
    if (!year || year < 1900 || year > 2025) { Alert.alert('올바른 출생연도를 입력해주세요.'); return; }
    if (!month || month < 1 || month > 12) { Alert.alert('올바른 월을 입력해주세요.'); return; }
    if (!day || day < 1 || day > 31) { Alert.alert('올바른 일을 입력해주세요.'); return; }

    await AsyncStorage.setItem('saju_info', JSON.stringify({
      name: name.trim(), birthYear: year, birthMonth: month, birthDay: day,
      birthHour, gender,
    }));
    Alert.alert('저장 완료', `${name}님의 사주 정보가 저장되었습니다.`, [
      { text: '확인', onPress: () => router.back() },
    ]);
  };

  return (
    <LinearGradient colors={['#1a0a2e', '#0d0620']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

        <View style={styles.header}>
          <Text style={styles.headerEmoji}>📿</Text>
          <Text style={styles.headerTitle}>사주 정보 입력</Text>
          <Text style={styles.headerDesc}>
            정확한 생년월일시를 입력할수록{'\n'}더 정확한 관상-사주 분석이 가능합니다.
          </Text>
        </View>

        <Text style={styles.label}>이름</Text>
        <TextInput
          style={styles.input}
          placeholder="이름을 입력하세요"
          placeholderTextColor="#555"
          value={name}
          onChangeText={setName}
        />

        <Text style={styles.label}>성별</Text>
        <View style={styles.genderRow}>
          {(['male', 'female'] as const).map((g) => (
            <TouchableOpacity
              key={g}
              style={[styles.genderBtn, gender === g && styles.genderBtnActive]}
              onPress={() => setGender(g)}
            >
              <Text style={styles.genderEmoji}>{g === 'male' ? '👨' : '👩'}</Text>
              <Text style={[styles.genderLabel, gender === g && styles.genderLabelActive]}>
                {g === 'male' ? '남성' : '여성'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>출생 연도</Text>
        <TextInput
          style={styles.input}
          placeholder="예: 1990"
          placeholderTextColor="#555"
          keyboardType="number-pad"
          maxLength={4}
          value={birthYear}
          onChangeText={setBirthYear}
        />

        <View style={styles.row}>
          <View style={{ flex: 1 }}>
            <Text style={styles.label}>월</Text>
            <TextInput
              style={styles.input}
              placeholder="1 ~ 12"
              placeholderTextColor="#555"
              keyboardType="number-pad"
              maxLength={2}
              value={birthMonth}
              onChangeText={setBirthMonth}
            />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.label}>일</Text>
            <TextInput
              style={styles.input}
              placeholder="1 ~ 31"
              placeholderTextColor="#555"
              keyboardType="number-pad"
              maxLength={2}
              value={birthDay}
              onChangeText={setBirthDay}
            />
          </View>
        </View>

        <Text style={styles.label}>출생 시각 (시주) — {birthHour}시</Text>
        <Text style={styles.subLabel}>모르는 경우 12시(정오)로 설정하세요</Text>
        <ScrollView
          horizontal showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ gap: 6, paddingBottom: 4 }}
        >
          {HOURS.map((h) => (
            <TouchableOpacity
              key={h}
              style={[styles.hourBtn, birthHour === h && styles.hourBtnActive]}
              onPress={() => setBirthHour(h)}
            >
              <Text style={[styles.hourText, birthHour === h && styles.hourTextActive]}>
                {h}시
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>사주(四柱)란?</Text>
          <Text style={styles.infoText}>
            사주는 태어난 연(年)·월(月)·일(日)·시(時)의 네 기둥(四柱)으로 구성됩니다.
            각 기둥은 천간(天干)과 지지(地支)로 이루어져 오행(목·화·토·금·수)의 균형을 나타냅니다.
            관상과 사주를 함께 분석하면 더욱 정확한 운세 파악이 가능합니다.
          </Text>
        </View>

        <TouchableOpacity style={styles.saveBtn} onPress={handleSave}>
          <Text style={styles.saveBtnText}>📿 사주 저장하기</Text>
        </TouchableOpacity>

      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { padding: 20, paddingBottom: 60 },
  header: { alignItems: 'center', marginBottom: 28 },
  headerEmoji: { fontSize: 56, marginBottom: 8 },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: '#d4af37', marginBottom: 8 },
  headerDesc: { fontSize: 14, color: '#888', textAlign: 'center', lineHeight: 20 },
  label: { fontSize: 14, fontWeight: '600', color: '#d4af37', marginBottom: 6, marginTop: 16 },
  subLabel: { fontSize: 12, color: '#666', marginBottom: 8, marginTop: -4 },
  input: {
    backgroundColor: 'rgba(255,255,255,0.07)', borderRadius: 12,
    padding: 14, fontSize: 16, color: '#fff',
    borderColor: '#2d1a4e', borderWidth: 1,
  },
  row: { flexDirection: 'row', gap: 12 },
  genderRow: { flexDirection: 'row', gap: 12 },
  genderBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    padding: 14, borderRadius: 12, backgroundColor: 'rgba(255,255,255,0.06)',
    borderColor: '#2d1a4e', borderWidth: 1,
  },
  genderBtnActive: { borderColor: '#d4af37', backgroundColor: 'rgba(212,175,55,0.12)' },
  genderEmoji: { fontSize: 24 },
  genderLabel: { fontSize: 16, color: '#888', fontWeight: '600' },
  genderLabelActive: { color: '#d4af37' },
  hourBtn: {
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10,
    backgroundColor: 'rgba(255,255,255,0.05)', borderColor: '#2d1a4e', borderWidth: 1,
  },
  hourBtnActive: { borderColor: '#d4af37', backgroundColor: 'rgba(212,175,55,0.15)' },
  hourText: { fontSize: 13, color: '#777' },
  hourTextActive: { color: '#d4af37', fontWeight: 'bold' },
  infoBox: {
    backgroundColor: 'rgba(100,60,180,0.1)', borderRadius: 14, padding: 16,
    marginTop: 24, marginBottom: 12, borderColor: '#7b5ea7', borderWidth: 1,
  },
  infoTitle: { fontSize: 15, fontWeight: 'bold', color: '#c4a8f0', marginBottom: 8 },
  infoText: { fontSize: 13, color: '#9b8cc4', lineHeight: 20 },
  saveBtn: { backgroundColor: '#d4af37', borderRadius: 16, padding: 18, alignItems: 'center', marginTop: 16 },
  saveBtnText: { fontSize: 18, fontWeight: 'bold', color: '#1a0a2e' },
});
