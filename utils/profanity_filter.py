# back/utils/profanity_filter.py

import re

# 초성 리스트
CHOSUNG_LIST = [
    "ㄱ",
    "ㄲ",
    "ㄴ",
    "ㄷ",
    "ㄸ",
    "ㄹ",
    "ㅁ",
    "ㅂ",
    "ㅃ",
    "ㅅ",
    "ㅆ",
    "ㅇ",
    "ㅈ",
    "ㅉ",
    "ㅊ",
    "ㅋ",
    "ㅌ",
    "ㅍ",
    "ㅎ",
]
# 중성 리스트
JUNGSUNG_LIST = [
    "ㅏ",
    "ㅐ",
    "ㅑ",
    "ㅒ",
    "ㅓ",
    "ㅔ",
    "ㅕ",
    "ㅖ",
    "ㅗ",
    "ㅘ",
    "왠",
    "ㅙ",
    "ㅛ",
    "ㅜ",
    "ㅝ",
    "ㅞ",
    "ㅚ",
    "ㅠ",
    "ㅡ",
    "ㅢ",
    "ㅣ",
]
# 종성 리스트
JONGSUNG_LIST = [
    "",
    "ㄱ",
    "ㄲ",
    "ㄳ",
    "ㄴ",
    "ㄵ",
    "ㄶ",
    "ㄷ",
    "ㄹ",
    "ㄺ",
    "ㄻ",
    "ㄼ",
    "ㄽ",
    "ㄾ",
    "ㄿ",
    "ㅀ",
    "ㅁ",
    "ㅂ",
    "ㅄ",
    "ㅅ",
    "ㅆ",
    "ㅇ",
    "ㅈ",
    "ㅊ",
    "ㅋ",
    "ㅌ",
    "ㅍ",
    "ㅎ",
]


def decompose_korean(char):
    """한글 문자를 초성, 중성, 종성으로 분리 (Jamo)."""
    if "가" <= char <= "힣":
        offset = ord(char) - ord("가")
        chosung_idx = offset // (21 * 28)
        jungsung_idx = (offset % (21 * 28)) // 28
        jongsung_idx = offset % 28
        return (
            CHOSUNG_LIST[chosung_idx],
            JUNGSUNG_LIST[jungsung_idx],
            JONGSUNG_LIST[jongsung_idx],
        )
    return (char, "", "")


def convert_to_jamo(text):
    """텍스트를 자모로 변환."""
    jamo_text = []
    for char in text:
        if "가" <= char <= "힣":
            jamo_text.extend(decompose_korean(char))
        else:
            jamo_text.append(char)
    return "".join(jamo_text)


class ProfanityFilter:
    # 기존 단어 목록 및 자음/모음 기반 비속어 (필터링 대체에도 사용)
    PROFANITY_WORDS = [
        "바보",
        "멍청이",
        "새끼",
        "시발",
        "개새끼",
        "병신",
        "존나",
        "좆",
        "씨발",
        "애미",
        "창녀",
        "개같은",
        "미친놈",
        "꺼져",
        "지랄",
        "염병",
        "따먹",
        "걸레",
        "씹",
        "염병할",
        "미친",
        "호로새끼",
        "썅",
        "개수작",
        "씹새끼",
        "족같다",
        "개소리",
        "엠창",
        "등신",
        "병신같은",
        "개놈",
        "또라이",
        "삐리",
        "걸래년",
        "빠가",
        "상놈",
        "병자",
        "돌대가리",
        "돌아이",
        "육시랄",
        "ㅅㅂ",
        "ㅈㄴ",
        "ㄲㅈ",
        "ㄷㅊ",
        "ㅁㅊ",
        "ㅆㅂ",
        "ㅂㅅ",
        "ㅈㄹ",
        "ㅊㄴ",
        "ㅇㅁ",
        "새꺄",
        "썅년",
        "개년",
        "개지랄",
        "졸라",
        "개같네",
        "닥쳐",
        "지랄마",
        "븅신",
        "쓰레기",
        "애미뒤진",
        "창놈",
        "호로자식",
        "등신아",
        "쪼다",
        "찐따",
        "병맛",
        "미친놈아",
        "싸이코",
        "개새",
        "씹새",
        "씨발놈",
        "씨발년",
        "씨발새끼",
        "좆같은",
        "지랄하네",
        "병신새끼",
        "개같은년",
        "개같은놈",
        "쌍년",
        "쌍놈",
        "개같은새끼",
        "염병할놈",
        "염병할년",
        "개씹",
        "씹새",
        "좆밥",
        "븅딱",
        "색기",
        "씨발련아",
        "개쓰레기",
        "ㄱㅅㄲ",
        "ㅄ",
        "ㅁㅊㄴ",
        "ㅈㄴㅈㄹ",
        "ㅆㅂㅅㄲ",
        "ㄱㄷㅊ",
        "ㅁㅊㄴㅇ",  # 초성으로만 된 욕설 추가
    ]

    # 자모 기반 비속어 패턴 (정규 표현식으로 컴파일)
    PROFANITY_JAMO_PATTERNS = [
        re.compile(r"ㅅㅣㅂㅏㄹ"),
        re.compile(r"ㅈㅗㄴㄴㅏ"),
        re.compile(r"ㅂㅕㅇㅅㅣㄴ"),
        re.compile(r"ㄱㅐㅅㅐㄲㅣ"),
        re.compile(r"ㅆㅣㅂ"),
        re.compile(r"ㅈㅗㅅ"),
        re.compile(r"ㅂㅏㅂㅗ"),
        re.compile(r"ㅁㅓㅇㅊㅓㅇㅇㅣ"),
        re.compile(r"ㅅㅂ"),
        re.compile(r"ㅈㄴ"),
        re.compile(r"ㄲㅈ"),
        re.compile(r"ㄷㅊ"),
        re.compile(r"ㅁㅊ"),
        re.compile(r"ㅆㅂ"),
        re.compile(r"ㅂㅅ"),
        re.compile(r"ㅈㄹ"),
        re.compile(r"ㅊㄴ"),
        re.compile(r"ㅇㅁ"),
        re.compile(r"ㅅㅐㄲㅑ"),
        re.compile(r"ㅆㅑㅇㄴㅕㄴ"),
        re.compile(r"ㄱㅐㄴㅕㄴ"),
        re.compile(r"ㄱㅐㅈㅣㄹㅏㄹ"),
        re.compile(r"ㅈㅗㄹㄹㅏ"),
        re.compile(r"ㄱㅐㄱㅏㅌㄴㅔ"),
        re.compile(r"ㄷㅏㄱㅊㅕ"),
        re.compile(r"ㅈㅣㄹㅏㄹㅁㅏ"),
        re.compile(r"ㅂㅕㅇㅅㅣㄴ"),
        re.compile(r"ㅆㅡㄹㅔㄱㅣ"),
        re.compile(r"ㄱㅓㄹㄹㅔ"),
        re.compile(r"ㅇㅐㅁㅣㄷㅗㅣㅈㅣㄴ"),
        re.compile(r"ㅊㅏㅇㄴㅗㅁ"),
        re.compile(r"ㅎㅗㄹㅗㅈㅏㅅㅣㄱ"),
        re.compile(r"ㄷㅡㅇㅅㅣㄴㅇㅏ"),
        re.compile(r"ㅉㅗㄷㅏ"),
        re.compile(r"ㅉㅣㄴㄸㅏ"),
        re.compile(r"ㅂㅕㅇㅁㅏㅅ"),
        re.compile(r"ㅁㅣㅊㅣㄴㄴㅗㅁㅇㅏ"),
        re.compile(r"ㅆㅏㅇㅣㅋㅗ"),
        re.compile(r"ㄱㅐㅆㅐ"),
        re.compile(r"ㅆㅣㅂㅅㅐ"),
        re.compile(r"ㅆㅣㅂㅏㄹㄴㅗㅁ"),
        re.compile(r"ㅆㅣㅂㅏㄹㄴㅕㄴ"),
        re.compile(r"ㅆㅣㅂㅏㄹㅅㅐㄲㅣ"),
        re.compile(r"ㅈㅗㅅㄱㅏㅌㅇㅡㄴ"),
        re.compile(r"ㅈㅣㄹㅏㄹㅎㅏㄴㅔ"),
        re.compile(r"ㅂㅕㅇㅅㅣㄴㅅㅐㄲㅣ"),
        re.compile(r"ㄱㅐㄱㅏㅌㅇㅡㄴㄴㅕㄴ"),
        re.compile(r"ㄱㅐㄱㅏㅌㅇㅡㄴㄴㅗㅁ"),
        re.compile(r"ㄱㅐㅆㅐ"),
        re.compile(r"ㅆㅑㅇㄴㅗㅁ"),
        re.compile(r"ㅆㅑㅇㄴㅕㄴ"),
        re.compile(r"ㅎㅗㄹㅗㅅㅐ"),
        re.compile(r"ㅇㅐㅈㅏ"),
        re.compile(r"ㅈㅏㅇㅇㅐㅇㅣㄴㅂㅣㅎㅏㄷㅏㄴㅇㅓ"),
        re.compile(r"ㅂㅓㄹㅓㅈㅣ"),
        re.compile(r"ㅆㅡㄹㅔㄱㅣㄱㅏㅌㅇㅡㄴ"),
        re.compile(r"ㅂㅕㅇㄸㅏㄱ"),
        re.compile(r"ㅅㅐㄱㄱㅣ"),
        re.compile(r"ㅆㅣㅂㅏㄹㄹㅕㄴㅇㅏ"),
        re.compile(r"ㄱㅐㅆㅡㄹㅔㄱㅣ"),
        re.compile(r"ㅆㅏㅇㄴㅕㄴ"),
        re.compile(r"ㅆㅏㅇㄴㅗㅁ"),
        re.compile(r"ㄱㅐㄱㅏㅌㅇㅡㄴㅅㅐㄲㅣ"),
        re.compile(r"ㅇㅕㅁㅂㅕㅇㅎㅏㄹㄴㅗㅁ"),
        re.compile(r"ㅇㅕㅁㅂㅕㅇㅎㅏㄹㄴㅕㄴ"),
        re.compile(r"ㄱㅐㅆㅣㅂ"),
        re.compile(r"ㅆㅣㅂㅅㅐ"),
        re.compile(r"ㅈㅗㅅㅂㅏㅂ"),
        re.compile(r"ㄱㅅㄲ"),
        re.compile(r"ㅂㅅ"),
        re.compile(r"ㅁㅊㄴ"),
        re.compile(r"ㅈㄴㅈㄹ"),
        re.compile(r"ㅆㅂㅅㄲ"),
        re.compile(r"ㄱㄷㅊ"),
        re.compile(r"ㅁㅊㄴㅇ"),
    ]

    def contains_profanity(self, text):
        if not isinstance(text, str):
            return False

        text_lower = text.lower()
        jamo_text_lower = convert_to_jamo(text_lower)

        # 1. 단어 기반 필터링
        for word in self.PROFANITY_WORDS:
            if word in text_lower:
                return True

        # 2. 자모 기반 필터링 (미리 컴파일된 패턴 사용)
        for pattern in self.PROFANITY_JAMO_PATTERNS:
            if pattern.search(jamo_text_lower):
                return True

        return False

    def filter_profanity(self, text, replace_char="*"):
        if not isinstance(text, str):
            return text

        filtered_text = text
        text_lower = text.lower()
        jamo_text_lower = convert_to_jamo(text_lower)

        # 1. 단어 기반 필터링 (모든 비속어 단어를 대소문자 구분 없이 찾아 대체)
        for word in self.PROFANITY_WORDS:
            filtered_text = re.sub(
                re.escape(word),
                replace_char * len(word),
                filtered_text,
                flags=re.IGNORECASE,
            )

        # 2. 자모 기반 필터링 (자모 분리된 비속어 패턴 대체)
        # 이 부분은 원래 텍스트에서 비속어에 해당하는 부분을 찾아 대체해야 함
        # 원본 텍스트의 길이를 유지하면서 대체하기 위해 더 복잡한 로직이 필요
        # 여기서는 간단하게 자모 텍스트에서 매칭되는 부분을 찾고, 원래 텍스트의 길이를 기준으로 대체
        # 주의: 이 방법은 원본 텍스트의 정확한 위치와 길이를 반영하지 못할 수 있음
        for pattern in self.PROFANITY_JAMO_PATTERNS:
            for match in pattern.finditer(jamo_text_lower):
                # 매칭된 자모 길이만큼 원본 텍스트를 대체
                # 여기서는 단순히 매칭된 자모 패턴의 길이만큼 *로 대체하지만,
                # 실제 단어의 길이와 다를 수 있으므로 더 정교한 매핑 로직이 필요할 수 있습니다.
                # 예를 들어, 'ㅅㅂ'이 '시발'의 자모 분리형이라면, '시발'의 길이(2)만큼 대체하는 식.
                # 여기서는 자모 패턴의 길이만큼 대체하는 간단한 방식을 사용합니다.
                matched_length = len(match.group(0))
                # 원본 텍스트에서 해당 자모 패턴에 해당하는 부분을 찾기 위한 로직이 필요
                # 현재 구조에서는 직접적인 매핑이 어려우므로, 이 부분은 유의해야 함
                # 일단은 단순히 자모 길이에 비례하여 *를 추가
                filtered_text = self._replace_jamo_profanity_in_original_text(filtered_text, pattern, replace_char)

        return filtered_text

    def _replace_jamo_profanity_in_original_text(self, original_text, jamo_pattern, replace_char):
        # 이 함수는 실제 한글 텍스트에서 자모 패턴에 해당하는 부분을 찾아 대체합니다.
        # 한글 자모 분리/합성 로직을 역으로 이용하여 원본 텍스트의 위치를 추정합니다.
        # 이 구현은 복잡하며, 완벽한 정확성을 보장하기 어려울 수 있습니다.

        # 간단한 구현: 자모 패턴이 포함된 경우 원본 텍스트의 모든 비속어 단어를 대체
        # 이 방법은 'contains_profanity'에서 이미 사용된 단어 기반 매칭과 중복될 수 있습니다.
        # 더 정교한 자모 대체는 각 비속어에 대한 원본-자모 매핑 테이블을 구축해야 합니다.

        # 여기서는 임시로 PROFANITY_WORDS에 있는 모든 단어를 다시 한 번 대체하는 방식으로 구현합니다.
        # 이는 이상적인 자모 기반 대체가 아니며, 추후 개선이 필요할 수 있습니다.
        for word in self.PROFANITY_WORDS:
            # 패턴 매칭 후 원본 텍스트에서 해당 단어를 대체
            if jamo_pattern.search(convert_to_jamo(word.lower())):
                original_text = re.sub(
                    re.escape(word),
                    replace_char * len(word),
                    original_text,
                    flags=re.IGNORECASE,
                )
        return original_text
