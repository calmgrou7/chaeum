export type BusinessCategory =
  | 'aesthetic'
  | 'semi_permanent'
  | 'scalp_care'
  | 'scalp_tattoo'
  | 'plastic_surgery'
  | 'fortune';

export interface Business {
  id: string;
  name: string;
  category: BusinessCategory;
  categoryLabel: string;
  description: string;
  gwansangEffect: string;
  rating: string;
  address: string;
  phone: string;
  tags: string[];
  naverMapUrl?: string;
  instagramUrl?: string;
  priceRange?: string;
}

export const BUSINESS_DATA: Business[] = [
  // 에스테틱
  {
    id: 'ae1',
    name: '운명피부관리실',
    category: 'aesthetic',
    categoryLabel: '피부 에스테틱',
    description: '20년 경력의 전문가가 피부 결을 고르게 정돈합니다. 이마·볼·턱선 집중 케어로 관상의 기운을 끌어올립니다.',
    gwansangEffect: '이마와 볼의 기운을 밝혀 발전운·재물운 상승',
    rating: '4.9',
    address: '서울 강남구 신사동',
    phone: '02-1234-5678',
    tags: ['이마케어', '볼탄력', '피부정화', '관상개선'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '5~20만원',
  },
  {
    id: 'ae2',
    name: '기운에스테틱',
    category: 'aesthetic',
    categoryLabel: '피부 에스테틱',
    description: '동양 의학을 접목한 혈자리 에스테틱으로 얼굴의 기운 흐름을 개선합니다. 피부 개선과 동시에 운세 상승.',
    gwansangEffect: '얼굴 기운 순환 개선으로 전체 관상 밝아짐',
    rating: '4.8',
    address: '서울 마포구 연남동',
    phone: '02-2345-6789',
    tags: ['혈자리', '동양미용', '기운개선', '피부관리'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '8~25만원',
  },
  // 반영구
  {
    id: 'sp1',
    name: '자연눈썹스튜디오',
    category: 'semi_permanent',
    categoryLabel: '반영구 메이크업',
    description: '눈썹 결 타투·헤어라인·입술 반영구 전문. 자연스럽고 뚜렷한 눈썹으로 인복운과 건강운을 강화합니다.',
    gwansangEffect: '눈썹이 풍성해져 인복·건강운 대폭 상승',
    rating: '4.9',
    address: '서울 강남구 압구정동',
    phone: '02-3456-7890',
    tags: ['눈썹반영구', '눈썹결타투', '입술반영구', '헤어라인'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '15~40만원',
  },
  {
    id: 'sp2',
    name: '복덕반영구',
    category: 'semi_permanent',
    categoryLabel: '반영구 메이크업',
    description: '관상 전문가와 협력하여 관상에 맞는 눈썹·입술 디자인으로 복을 불러들이는 반영구 시술을 제공합니다.',
    gwansangEffect: '맞춤 눈썹·입술 디자인으로 관상 전체 기운 상승',
    rating: '4.7',
    address: '서울 서초구 방배동',
    phone: '02-4567-8901',
    tags: ['관상맞춤', '눈썹디자인', '입술반영구', '복덕관상'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '20~50만원',
  },
  // 두피케어
  {
    id: 'sc1',
    name: '두피운명센터',
    category: 'scalp_care',
    categoryLabel: '두피 케어',
    description: '두피 건강이 곧 이마의 기운입니다. 전문 두피 진단 후 맞춤 케어로 모발 건강과 관상의 이마 기운을 강화합니다.',
    gwansangEffect: '두피·이마 기운 활성화로 발전운·지혜운 상승',
    rating: '4.8',
    address: '서울 강동구 천호동',
    phone: '02-5678-9012',
    tags: ['두피진단', '탈모케어', '두피스케일링', '모발관리'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '5~15만원',
  },
  {
    id: 'sc2',
    name: '헤어운세케어',
    category: 'scalp_care',
    categoryLabel: '두피 케어',
    description: '탈모 및 두피 트러블 전문 클리닉. 한방 두피 케어와 현대 의학을 접목하여 두피 기운과 관상을 동시에 개선합니다.',
    gwansangEffect: '모발 밀도 증가로 이마 기운 안정화, 귀인운 상승',
    rating: '4.6',
    address: '서울 노원구 중계동',
    phone: '02-6789-0123',
    tags: ['한방두피', '탈모치료', '두피기운', '헤어케어'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '5~20만원',
  },
  // 두피문신
  {
    id: 'st1',
    name: '헤어라인문신연구소',
    category: 'scalp_tattoo',
    categoryLabel: '두피문신 (SMP)',
    description: 'SMP(두피문신) 전문. 탈모 부위를 자연스럽게 채워 이마 라인을 완성합니다. 관상에서 이마 기운을 강화합니다.',
    gwansangEffect: '이마 라인 완성으로 발전운·초년운·명예운 상승',
    rating: '4.9',
    address: '서울 강남구 역삼동',
    phone: '02-7890-1234',
    tags: ['SMP', '두피문신', '헤어라인', '탈모커버'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '50~200만원',
  },
  {
    id: 'st2',
    name: '관상두피아트',
    category: 'scalp_tattoo',
    categoryLabel: '두피문신 (SMP)',
    description: '관상 원리에 맞는 헤어라인 설계로 이마 형태를 최적화합니다. 단순한 탈모 커버가 아닌 관상 개선 목적의 시술.',
    gwansangEffect: '헤어라인 최적화로 이마 관상 대폭 개선, 관운 상승',
    rating: '4.8',
    address: '서울 서대문구 신촌동',
    phone: '02-8901-2345',
    tags: ['관상헤어라인', 'SMP전문', '관상개선', '두피아트'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '80~250만원',
  },
  // 성형외과
  {
    id: 'ps1',
    name: '관상성형의원',
    category: 'plastic_surgery',
    categoryLabel: '성형외과',
    description: '관상학적 원리를 의료 시술에 적용하는 성형외과입니다. 코·눈꺼풀·턱·이마 등 관상 개선 전문 시술을 제공합니다.',
    gwansangEffect: '핵심 관상 부위 개선으로 전체 운세 대길로 상승',
    rating: '4.7',
    address: '서울 강남구 청담동',
    phone: '02-9012-3456',
    tags: ['관상성형', '코성형', '눈성형', '이마성형', '관운개선'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '200만원~',
  },
  {
    id: 'ps2',
    name: '복덕클리닉',
    category: 'plastic_surgery',
    categoryLabel: '성형외과',
    description: '비수술적 시술(필러·보톡스·실리프팅)로 관상을 개선합니다. 수술 없이 관상의 기운을 높이는 방법을 제안합니다.',
    gwansangEffect: '비수술 관상 개선으로 재물운·인복운 점진적 상승',
    rating: '4.8',
    address: '서울 강남구 논현동',
    phone: '02-0123-4567',
    tags: ['필러', '보톡스', '실리프팅', '비수술관상개선'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '30~300만원',
  },
  // 운세상담
  {
    id: 'fo1',
    name: '관상사주연구원',
    category: 'fortune',
    categoryLabel: '관상·사주 상담',
    description: '30년 경력의 관상·사주 전문가. AI 분석 결과를 더욱 깊이 있게 해석하고 실제 운세와 개운 방향을 제시합니다.',
    gwansangEffect: '전문 상담으로 관상-사주 연계 분석 및 개운 방향 제시',
    rating: '4.9',
    address: '서울 종로구 인사동',
    phone: '02-1111-2222',
    tags: ['관상상담', '사주팔자', '개운상담', '운명상담'],
    naverMapUrl: 'https://map.naver.com',
    priceRange: '5~20만원',
  },
];
