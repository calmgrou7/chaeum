// 사주(四柱) 계산 서비스 — 천간(天干) / 지지(地支) 기반

const HEAVENLY_STEMS = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계'];
const EARTHLY_BRANCHES = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해'];

const STEM_ELEMENT: Record<string, string> = {
  갑: '목', 을: '목', 병: '화', 정: '화', 무: '토',
  기: '토', 경: '금', 신: '금', 임: '수', 계: '수',
};

const BRANCH_ELEMENT: Record<string, string> = {
  자: '수', 축: '토', 인: '목', 묘: '목', 진: '토', 사: '화',
  오: '화', 미: '토', 신: '금', 유: '금', 술: '토', 해: '수',
};

const ZODIAC: Record<string, string> = {
  자: '쥐', 축: '소', 인: '호랑이', 묘: '토끼', 진: '용', 사: '뱀',
  오: '말', 미: '양', 신: '원숭이', 유: '닭', 술: '개', 해: '돼지',
};

export interface SajuPillar {
  stem: string;
  branch: string;
  element: string;
  zodiac?: string;
}

export interface GwansangCorrelation {
  feature: string;
  description: string;
  advice: string;
}

export interface SajuResult {
  yearPillar: SajuPillar;
  monthPillar: SajuPillar;
  dayPillar: SajuPillar;
  hourPillar: SajuPillar;
  elements: Record<string, number>;
  dominantElement: string;
  gwansangCorrelations: GwansangCorrelation[];
}

function getStem(index: number): string {
  return HEAVENLY_STEMS[((index % 10) + 10) % 10];
}

function getBranch(index: number): string {
  return EARTHLY_BRANCHES[((index % 12) + 12) % 12];
}

function getYearPillar(year: number): SajuPillar {
  const stemIndex = (year - 4) % 10;
  const branchIndex = (year - 4) % 12;
  const stem = getStem(stemIndex);
  const branch = getBranch(branchIndex);
  return { stem, branch, element: STEM_ELEMENT[stem], zodiac: ZODIAC[branch] };
}

function getMonthPillar(year: number, month: number): SajuPillar {
  const stemBase = (year % 5) * 2;
  const stemIndex = (stemBase + month - 1) % 10;
  const branchIndex = (month + 1) % 12;
  const stem = getStem(stemIndex);
  const branch = getBranch(branchIndex);
  return { stem, branch, element: STEM_ELEMENT[stem] };
}

function getDayPillar(year: number, month: number, day: number): SajuPillar {
  // Simplified day pillar calculation using Julian Day Number
  const a = Math.floor((14 - month) / 12);
  const y = year + 4800 - a;
  const m = month + 12 * a - 3;
  const jdn = day + Math.floor((153 * m + 2) / 5) + 365 * y + Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) - 32045;
  const stemIndex = (jdn + 9) % 10;
  const branchIndex = (jdn + 1) % 12;
  const stem = getStem(stemIndex);
  const branch = getBranch(branchIndex);
  return { stem, branch, element: STEM_ELEMENT[stem] };
}

function getHourPillar(dayPillar: SajuPillar, hour: number): SajuPillar {
  const branchIndex = Math.floor((hour + 1) / 2) % 12;
  const dayIndex = HEAVENLY_STEMS.indexOf(dayPillar.stem);
  const stemIndex = (dayIndex % 5) * 2 + Math.floor(branchIndex / 2) % 2;
  const stem = getStem(stemIndex);
  const branch = getBranch(branchIndex);
  return { stem, branch, element: STEM_ELEMENT[stem] };
}

function countElements(pillars: SajuPillar[]): Record<string, number> {
  const counts: Record<string, number> = { 목: 0, 화: 0, 토: 0, 금: 0, 수: 0 };
  for (const p of pillars) {
    if (p.element && counts[p.element] !== undefined) counts[p.element]++;
    const branchEl = BRANCH_ELEMENT[p.branch];
    if (branchEl && counts[branchEl] !== undefined) counts[branchEl]++;
  }
  return counts;
}

function getGwansangCorrelations(elements: Record<string, number>): GwansangCorrelation[] {
  const correlations: GwansangCorrelation[] = [];
  const sorted = Object.entries(elements).sort(([, a], [, b]) => b - a);
  const [dominant] = sorted[0];
  const [weakest] = sorted[sorted.length - 1];

  const ELEMENT_GWANSANG: Record<string, GwansangCorrelation> = {
    목: {
      feature: '눈·눈썹 (목(木)의 기운)',
      description: '사주에 목(木)의 기운이 강합니다. 관상에서 눈과 눈썹이 인복과 발전운을 나타내며, 눈을 생기 있게 유지하면 기운이 더욱 강해집니다.',
      advice: '눈썹 관리와 아이라인 시술로 눈의 기운을 강화하세요. 자연스럽고 뚜렷한 눈썹이 목의 기운을 북돋습니다.',
    },
    화: {
      feature: '이마·인당 (화(火)의 기운)',
      description: '사주에 화(火)의 기운이 강합니다. 관상에서 이마와 인당(양 눈썹 사이)이 명예운과 리더십을 나타냅니다.',
      advice: '이마를 드러내고 인당 부위를 맑게 유지하세요. 에스테틱 시술로 이마 피부 결을 고르게 하면 화의 기운이 빛납니다.',
    },
    토: {
      feature: '코·볼·턱 (토(土)의 기운)',
      description: '사주에 토(土)의 기운이 강합니다. 관상에서 코와 볼, 턱이 재물운과 안정감을 나타냅니다.',
      advice: '코 주변을 따뜻하게 유지하고, 피부 탄력 관리를 하세요. 볼과 턱에 살집이 있어야 재물이 모입니다.',
    },
    금: {
      feature: '코끝·광대·얼굴형 (금(金)의 기운)',
      description: '사주에 금(金)의 기운이 강합니다. 관상에서 코끝과 광대뼈, 전반적인 얼굴 윤곽이 의지력과 실행력을 나타냅니다.',
      advice: '윤곽 시술이나 하이라이터로 광대와 코끝을 강조하면 금의 기운이 활성화됩니다.',
    },
    수: {
      feature: '귀·인중·입술 (수(水)의 기운)',
      description: '사주에 수(水)의 기운이 강합니다. 관상에서 귀와 인중, 입술이 지혜와 장수를 나타냅니다.',
      advice: '귀 마사지를 자주 하고 입술을 촉촉하게 유지하세요. 입술 반영구 시술로 수의 기운을 강화할 수 있습니다.',
    },
  };

  if (ELEMENT_GWANSANG[dominant]) correlations.push(ELEMENT_GWANSANG[dominant]);

  const SUPPLEMENT_ADVICE: Record<string, GwansangCorrelation> = {
    목: { feature: '목(木) 보완', description: '목의 기운이 부족합니다. 눈썹과 눈의 관리가 필요합니다.', advice: '눈썹 반영구 시술이나 눈썹 결 관리를 추천합니다.' },
    화: { feature: '화(火) 보완', description: '화의 기운이 부족합니다. 이마와 인당 관리가 필요합니다.', advice: '피부 미용과 에스테틱 시술로 이마를 밝게 가꾸세요.' },
    토: { feature: '토(土) 보완', description: '토의 기운이 부족합니다. 코와 볼 부위 관리가 필요합니다.', advice: '필러 시술이나 피부 볼륨 관리로 토의 기운을 보완하세요.' },
    금: { feature: '금(金) 보완', description: '금의 기운이 부족합니다. 얼굴 윤곽 관리가 필요합니다.', advice: '윤곽 시술이나 두피 케어로 금의 기운을 높이세요.' },
    수: { feature: '수(水) 보완', description: '수의 기운이 부족합니다. 귀와 입술 관리가 필요합니다.', advice: '입술 반영구 시술과 귀 마사지로 수의 기운을 보완하세요.' },
  };

  if (weakest !== dominant && SUPPLEMENT_ADVICE[weakest]) {
    correlations.push(SUPPLEMENT_ADVICE[weakest]);
  }

  return correlations;
}

export function calculateSaju(year: number, month: number, day: number, hour: number): SajuResult {
  const yearPillar = getYearPillar(year);
  const monthPillar = getMonthPillar(year, month);
  const dayPillar = getDayPillar(year, month, day);
  const hourPillar = getHourPillar(dayPillar, hour);
  const pillars = [yearPillar, monthPillar, dayPillar, hourPillar];
  const elements = countElements(pillars);
  const dominantElement = Object.entries(elements).sort(([, a], [, b]) => b - a)[0][0];
  const gwansangCorrelations = getGwansangCorrelations(elements);
  return { yearPillar, monthPillar, dayPillar, hourPillar, elements, dominantElement, gwansangCorrelations };
}
