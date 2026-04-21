import axios from 'axios';
import Constants from 'expo-constants';
import * as FileSystem from 'expo-file-system';

const BASE_URL = Constants.expoConfig?.extra?.apiBaseUrl || 'http://localhost:8000';

export interface GwansangPart {
  name: string;
  emoji: string;
  aspect: string;
  fortune: '대길' | '길' | '평' | '흉';
  description: string;
  advice: string;
}

export interface TreatmentRecommendation {
  treatment: string;
  emoji: string;
  reason: string;
  category: string;
}

export interface GwansangAnalysis {
  overallFortune: '대길' | '길' | '평' | '흉';
  fortuneScore: number;
  summary: string;
  parts: GwansangPart[];
  sajuCompatibility?: string;
  recommendedFilter: string;
  filterReason: string;
  treatmentRecommendations: TreatmentRecommendation[];
}

export async function analyzeGwansang(imageUri: string): Promise<GwansangAnalysis> {
  // Convert local URI to base64
  const base64 = await FileSystem.readAsStringAsync(imageUri, {
    encoding: FileSystem.EncodingType.Base64,
  });

  const response = await axios.post<GwansangAnalysis>(
    `${BASE_URL}/api/analyze`,
    { image_base64: base64 },
    { timeout: 30000 }
  );
  return response.data;
}

// Fallback mock for development (when backend is not running)
export function mockAnalyzeGwansang(): GwansangAnalysis {
  return {
    overallFortune: '길',
    fortuneScore: 72,
    summary:
      '전체적으로 균형 잡힌 관상입니다. 이마가 넓어 지혜롭고 발전 가능성이 높으며, 코의 기운이 좋아 중년 이후 재물운이 점점 상승할 것입니다. 눈썹이 짙고 눈이 맑아 인복이 풍부하고 귀인의 도움을 많이 받을 상입니다.',
    parts: [
      {
        name: '이마',
        emoji: '🧠',
        aspect: '지혜·발전운·초년운',
        fortune: '길',
        description: '이마가 넓고 결점 없이 맑습니다. 지혜롭고 학문적 능력이 뛰어나며 초년에 좋은 환경에서 성장했음을 나타냅니다.',
        advice: '이마를 항상 깨끗하게 유지하고 앞머리로 가리지 마세요. 이마를 드러내면 기운이 더 좋아집니다.',
      },
      {
        name: '눈·눈썹',
        emoji: '👀',
        aspect: '건강·인복·30대운',
        fortune: '대길',
        description: '눈이 맑고 눈썹이 풍성하여 인복이 대단히 좋습니다. 30대에 좋은 인연과 기회가 많이 찾아올 상입니다.',
        advice: '눈썹 모양을 자연스럽게 유지하세요. 눈썹 문신보다 자연 눈썹을 가꾸는 것이 기운 보존에 유리합니다.',
      },
      {
        name: '코',
        emoji: '👃',
        aspect: '재물운·40대운',
        fortune: '길',
        description: '코의 형태가 단정하고 콧볼이 적당히 넓어 재물이 들어오는 기운이 있습니다. 40대에 재물운이 크게 향상될 것입니다.',
        advice: '코끝을 따뜻하게 유지하고, 실내 온도를 적절히 조절하세요. 코가 차면 재물이 새어나간다고 합니다.',
      },
      {
        name: '입·인중',
        emoji: '👄',
        aspect: '언변·음식복·중년운',
        fortune: '평',
        description: '입의 기운이 보통 수준입니다. 언변은 좋으나 음식에 대한 복은 보통이며, 중년 이후 안정적인 삶이 예상됩니다.',
        advice: '입술 관리를 통해 입의 기운을 높이세요. 입술이 촉촉하고 윤기 있으면 말의 기운이 좋아집니다.',
      },
      {
        name: '귀',
        emoji: '👂',
        aspect: '장수·조상덕·어린시절',
        fortune: '길',
        description: '귀가 적당히 크고 귓불이 두터워 장수의 기운이 있습니다. 조상의 덕을 받으며 어린 시절 안정적인 환경이었음을 나타냅니다.',
        advice: '귀를 마사지해주면 건강과 장수운이 더욱 강해집니다. 귀 아래 혈자리를 자주 자극하세요.',
      },
    ],
    sajuCompatibility:
      '관상의 오행과 사주의 오행을 비교하면 목(木)의 기운이 강하게 나타납니다. 이마와 눈의 기운이 사주의 발전운을 잘 보조하고 있어 전체적으로 좋은 조화를 이루고 있습니다.',
    recommendedFilter: '자연 밝음',
    filterReason:
      '이마와 눈의 기운을 더욱 강화하기 위해 밝고 맑은 필터를 추천합니다. 피부 톤을 밝게 하면 발전운과 인복이 더욱 상승합니다.',
    treatmentRecommendations: [
      {
        treatment: '눈썹 반영구 시술',
        emoji: '💉',
        reason: '눈썹을 더욱 자연스럽고 풍성하게 만들어 인복운을 강화합니다.',
        category: 'semi_permanent',
      },
      {
        treatment: '피부 에스테틱',
        emoji: '💆',
        reason: '피부 결을 고르게 하면 이마의 기운이 맑아져 발전운이 상승합니다.',
        category: 'aesthetic',
      },
      {
        treatment: '두피 케어',
        emoji: '🦱',
        reason: '두피가 건강해야 이마의 기운이 강해집니다. 두피 관리로 전체 관상을 개선하세요.',
        category: 'scalp_care',
      },
    ],
  };
}
