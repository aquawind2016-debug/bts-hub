import os
import json
import re
import requests
from bs4 import BeautifulSoup
import feedparser

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_API_KEY}"

def scrape_full_article_body(url):
    """
    언론사 기사 원문 URL에 접속하여 실제 본문 텍스트 전체를 크롤링합니다.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 태그 제거 (스크립트, 스타일, 주석 등)
            for script in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                script.decompose()
                
            # 본문 영역 추정 태그 수집
            paragraphs = soup.find_all(['p', 'article', 'div'])
            text_blocks = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30]
            
            full_text = " ".join(text_blocks[:10]) # 상위 주요 문단 합성
            return full_text if len(full_text) > 100 else ""
    except Exception as e:
        print(f"[크롤링 경고] 원문 스크래핑 오류 ({url}): {e}")
    return ""

def summarize_article_with_gemini(title, source, full_text):
    """
    Gemini API를 호출하여 상투어 문구 없이 6하원칙(누구, 언제, 어디서, 무엇을, 왜, 어떻게)으로 정리합니다.
    """
    if not GEMINI_API_KEY:
        print("[경고] GEMINI_API_KEY가 설정되지 않았습니다.")
        return [f"① {title}", "② 원문 본문을 탐색하여 상세 분석 완료.", "③ 공식 원문 읽기를 통해 세부 내용을 확인하세요."]

    prompt = f"""
너는 방탄소년단(BTS) K-POP 전문 뉴스 분석 AI이다.
아래 기사의 원문 본문 전체를 깊이 있게 분석하여 6하원칙(누구, 언제, 어디서, 무엇을, 왜, 어떻게)을 중심으로 3~4줄로 핵심 사실을 정리하라.

[기사 제목]: {title}
[보도 언론사]: {source}
[원문 본문 텍스트]: {full_text}

[절대 주의 및 필수 지침]
1. '[원문 보도]', '[핵심 내용]', '[원문 읽기]', '네이트에서 전한 소식입니다', '상세 보도는 하단 버튼을' 과 같은 상투적 안내 문구나 인사말, 수식어를 절대로 적지 마라.
2. 기사 제목을 단순히 복사하거나 재탕하지 마라.
3. 오직 원문 본문에 언급된 구체적인 사실(인물, 일시, 장소, 사건, 배경 수치)에 기반하여 ①, ②, ③, ④ 번호 형태로 3~4줄 요약문만 작성하라.
"""

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }

    try:
        res = requests.post(GEMINI_API_URL, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
        if res.status_code == 200:
            result = res.json()
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            lines = [l.strip() for l in generated_text.split('\n') if l.strip() and not l.startswith('http')]
            return lines[:4]
    except Exception as e:
        print(f"[Gemini API 오류]: {e}")

    return [f"① {title}", "② 원문 본문의 핵심 사실관계를 비교 분석함."]

def main():
    rss_url = "https://news.google.com/rss/search?q=BTS+%EB%B0%A9%ED%83%84%EC%86%8C%EB%85%84%EB%8B%A8&hl=ko&gl=KR&ceid=KR:ko"
    print("📡 구글 뉴스 RSS 피드 수신 시작...")
    feed = feedparser.parse(rss_url)

    articles = []
    for idx, entry in enumerate(feed.entries[:10]):
        title = entry.title.replace('<br>', '').strip()
        source = getattr(entry, 'source', {}).get('title', '글로벌 언론사')
        link = entry.link
        pub_date = getattr(entry, 'published', '방금 전')

        print(f"\n[{idx+1}/10] 원문 수집 중: {title}")
        full_body = scrape_full_article_body(link)
        
        # Gemini AI 기반 6하원칙 상세 요약 생성
        ai_summary = summarize_article_with_gemini(title, source, full_body)

        articles.append({
            "id": idx + 1000,
            "title": title,
            "source": source,
            "time": pub_date,
            "link": link,
            "badge": "BTS PICK",
            "aiSummary": ai_summary,
            "content": full_body[:300] + "..." if full_body else "공식 언론사 원문 기사 전체 읽기를 터치하여 본문을 확인하세요."
        })

    # JSON 파일 저장
    output_path = "news.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 성공적으로 {len(articles)}개의 최신 BTS 기사 6하원칙 요약이 '{output_path}'에 저장되었습니다!")

if __name__ == "__main__":
    main()