"""
관상사주 앱 백엔드 API — FastAPI + Claude Vision

실행:
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8000

배포:
  Railway / Render / AWS EC2 등에 배포 후 app.json의 apiBaseUrl 수정
"""

from __future__ import annotations

import base64
import os
from typing import Optional

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="관상사주 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    image_base64: str
    saju_info: Optional[dict] = None


class GwansangPart(BaseModel):
    name: str
    emoji: str
    aspect: str
    fortune: str
    description: str
    advice: str


class TreatmentRecommendation(BaseModel):
    treatment: str
    emoji: str
    reason: str
    category: str


class AnalyzeResponse(BaseModel):
    overallFortune: str
    fortuneScore: int
    summary: str
    parts: list[GwansangPart]
    sajuCompatibility: Optional[str] = None
    recommendedFilter: str
    filterReason: str
    treatmentRecommendations: list[TreatmentRecommendation]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

GWANSANG_SYSTEM_PROMPT = """당신은 30년 경력의 한국 관상학 전문가입니다.
사진 속 얼굴을 분석하여 전통 한국 관상학에 기반한 상세한 분석을 제공합니다.

분석 시 다음 부위를 반드시 포함하세요:
- 이마 (지혜·발전운·초년운)
- 눈·눈썹 (건강·인복·30대운)
- 코 (재물운·40대운)
- 입·인중 (언변·음식복·중년운)
- 귀 (장수·조상덕)

운세 등급: 대길 > 길 > 평 > 흉

반드시 JSON 형식으로만 응답하세요.
추천 필터는 다음 중 하나: 자연 밝음, 따뜻한 피부, 맑은 인상, 입체감 강조, 온화한 인상, 자신감 있는
추천 시술 category는 다음 중 하나: aesthetic, semi_permanent, scalp_care, scalp_tattoo, plastic_surgery
"""

GWANSANG_USER_PROMPT = """다음 얼굴 사진을 관상학적으로 분석하고 아래 JSON 형식으로 정확히 응답하세요:

{
  "overallFortune": "길",
  "fortuneScore": 75,
  "summary": "전체 관상 요약 (2-3문장)",
  "parts": [
    {
      "name": "이마",
      "emoji": "🧠",
      "aspect": "지혜·발전운·초년운",
      "fortune": "길",
      "description": "이마 분석 내용",
      "advice": "이마 관리 조언"
    },
    {
      "name": "눈·눈썹",
      "emoji": "👀",
      "aspect": "건강·인복·30대운",
      "fortune": "대길",
      "description": "눈 분석 내용",
      "advice": "눈 관리 조언"
    },
    {
      "name": "코",
      "emoji": "👃",
      "aspect": "재물운·40대운",
      "fortune": "길",
      "description": "코 분석 내용",
      "advice": "코 관리 조언"
    },
    {
      "name": "입·인중",
      "emoji": "👄",
      "aspect": "언변·음식복·중년운",
      "fortune": "평",
      "description": "입 분석 내용",
      "advice": "입 관리 조언"
    },
    {
      "name": "귀",
      "emoji": "👂",
      "aspect": "장수·조상덕",
      "fortune": "길",
      "description": "귀 분석 내용",
      "advice": "귀 관리 조언"
    }
  ],
  "sajuCompatibility": "관상과 사주의 상관관계 설명",
  "recommendedFilter": "자연 밝음",
  "filterReason": "이 필터를 추천하는 관상학적 이유",
  "treatmentRecommendations": [
    {
      "treatment": "시술명",
      "emoji": "💉",
      "reason": "관상 개선 이유",
      "category": "semi_permanent"
    }
  ]
}"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "service": "관상사주 API"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_face(req: AnalyzeRequest):
    if not req.image_base64:
        raise HTTPException(status_code=400, detail="이미지가 필요합니다.")

    try:
        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2000,
            system=GWANSANG_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": req.image_base64,
                            },
                        },
                        {"type": "text", "text": GWANSANG_USER_PROMPT},
                    ],
                }
            ],
        )

        import json
        raw = message.content[0].text.strip()
        # Extract JSON from potential markdown code block
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        return AnalyzeResponse(**data)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI 응답 파싱 오류")
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI API 오류: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/saju-compatibility")
async def saju_compatibility(data: dict):
    """사주 정보와 관상 분석 결과를 결합하여 심화 분석 제공"""
    return {"message": "사주-관상 심화 분석은 준비 중입니다."}
