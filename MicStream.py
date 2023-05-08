import re
import sys

import json
import time

import requests

import pyaudio
from google.cloud import speech
from six.moves import queue

from threading import Thread, Event



# ===# 번역기 통신 모듈 #===#
# Default
# text = " 번역기 테스트 "
# from = 한국어 (ko)
# to = 영어 (en)
# 가용 언어 코드 : 한국어, 영어, 중국어, 일본어, 독일어, 프랑스어, 스페인어, 이탈리아어, 러시아어, 베트남어

API_URL = "https://dmtcloud.kr/translate-text"
LANGUAGE_CODE = {
    "한국어": {
        "DMT": "ko",
        "GOOGLE": "ko-KR"
    },
    "영어": {
        "DMT": "en",
        "GOOGLE": "en-US"
    },
    "중국어": {
        "DMT": "zh-CN",
        "GOOGLE": "zh"
    },
    "일본어": {
        "DMT": "ja",
        "GOOGLE": "ja-JP"
    },
    "독일어": {
        "DMT": "de",
        "GOOGLE": "de-DE"
    },
    "프랑스어": {
        "DMT": "fr",
        "GOOGLE": "fr-FR"
    },
    "스페인어": {
        "DMT": "es",
        "GOOGLE": "es-ES"
    },
    "포르투갈어": {
        "DMT": "pt",
        "GOOGLE": "pt-PT"
    },
    "이탈리아어": {
        "DMT": "it",
        "GOOGLE": "it-IT"
    },
    "러시아어": {
        "DMT": "ru",
        "GOOGLE": "ru-RU"
    },
    "베트남어": {
        "DMT": "vi",
        "GOOGLE": "vi-VN"
    }
}

STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 44100
CHUNK_SIZE = int(SAMPLE_RATE / 10)

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"


class MicStream(Thread):
    def __init__(self, name, track, langauge, mic=None, flags=None):
        super().__init__(daemon=True)
        self.name = name
        self.track = track
        self.lang1, self.lang2 = langauge
        self.mic_info = mic
        self.direction = flags
        self.running_state = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("MicStream 종료됨.")

    def run(self):
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code=LANGUAGE_CODE[self.lang1]["GOOGLE"],
            max_alternatives=1,
            enable_automatic_punctuation=True,
            use_enhanced=True
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

        mic_manager = MicrophoneStream(SAMPLE_RATE, CHUNK_SIZE, mic_info=self.mic_info)

        sys.stdout.write("\033[0;33m")
        sys.stdout.write('\nListening, say "Quit" or "Exit" to stop.\n\n')
        sys.stdout.write("End (ms)       Transcript Results/Status\n")
        sys.stdout.write("=====================================================\n")

        with mic_manager as stream:
            while not stream.closed:
                sys.stdout.write(YELLOW)
                sys.stdout.write(
                    "\n" + str(STREAMING_LIMIT) + ": NEW REQUEST\n"
                )

                stream.audio_input = []
                audio_generator = stream.generator()

                requests = (
                    speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator
                )

                responses = client.streaming_recognize(streaming_config, requests)

                self.listen_print_loop(responses, stream)

                if stream.result_end_time > 0:
                    stream.final_request_end_time = stream.is_final_end_time

                stream.result_end_time = 0
                stream.last_audio_input = []
                stream.last_audio_input = stream.audio_input
                stream.audio_input = []

                if not stream.last_transcript_was_final:
                    sys.stdout.write("\n")
                stream.new_stream = True

    def listen_print_loop(self, responses, stream):
        for response in responses:
            if get_current_time() - stream.start_time > STREAMING_LIMIT:
                stream.start_time = get_current_time()
                break

            if not response.results:
                continue

            result = response.results[0]

            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            result_sceonds = 0
            result_micros = 0

            if result.result_end_time.seconds:
                result_sceonds = result.result_end_time.seconds

            if result.result_end_time.microseconds:
                result_micros = result.result_end_time.microseconds

            stream.result_end_time = int((result_sceonds * 1000) + (result_micros / 1000))

            if not self.running_state:
                sys.stdout.write(YELLOW)
                sys.stdout.write("State Exiting...\n")
                print("State : ", self.running_state)
                stream.closed = True
                break

            if result.is_final:
                if self.direction == "None" or self.direction == "Left":
                    # 실제 출력
                    self.track.append_both(transcript, post_translate(from_lang=LANGUAGE_CODE[self.lang1]["DMT"], to_lang=LANGUAGE_CODE[self.lang2]["DMT"], post_text=transcript))
                    # track.append_left(transcript)
                    # track.append_right(post_translate(post_text=transcript))
                elif self.direction == "Right":
                    # 실제 출력
                    self.track.append_both(post_translate(from_lang=LANGUAGE_CODE[self.lang1]["DMT"], to_lang=LANGUAGE_CODE[self.lang2]["DMT"], post_text=transcript), transcript)
                    # track.append_left(post_translate(post_text=transcript))
                    # track.append_right(transcript)
                # 콘솔 출력
                sys.stdout.write(GREEN)
                sys.stdout.write("\033[K")
                sys.stdout.write("\n" + transcript + "\n")
                sys.stdout.write("번역문 : {translate}\n".format(translate=post_translate(from_lang=LANGUAGE_CODE[self.lang1]["DMT"], to_lang=LANGUAGE_CODE[self.lang2]["DMT"], post_text=transcript)))

                stream.is_final_end_time = stream.result_end_time
                stream.last_transcript_was_final = True

                if not self.running_state:
                    sys.stdout.write(YELLOW)
                    sys.stdout.write("State Exiting...\n")
                    print("State : ", self.running_state)
                    stream.closed = True
                    break

                # interrupt saying [exit, quit]
                if re.search(r"\b(exit|quit|끝)\b", transcript, re.I):
                    sys.stdout.write(YELLOW)
                    sys.stdout.write("Exiting...\n")
                    stream.closed = True
                    break

            else:
                # 실제 출력
                if self.direction == "Left":
                    self.track.realize_left(transcript)
                elif self.direction == "Right":
                    self.track.realize_right(transcript)

                # 콘솔 출력
                sys.stdout.write(RED)
                print("\r" + transcript, end="")

                stream.last_transcript_was_final = False

        if stream.result_end_time > 0:
            stream.final_request_end_time = stream.is_final_end_time

        stream.result_end_time = 0
        stream.last_audio_input = []
        stream.last_audio_input = stream.audio_input
        stream.audio_input = []

    def stop(self):
        self.running_state = False

    def set_micInfo(self, mic_info):
        self.mic_info = mic_info

    def set_langauge(self, language):
        self.lang1, self.lang2 = language


def post_translate(from_lang="ko", to_lang="en", post_text="번역기 테스트"):
    api_headers = {'Content-Type': 'application/json'}
    data = {
        'text':
            post_text,
        'from':
            from_lang,
        'to':
            to_lang
    }
    response = requests.post(API_URL, headers=api_headers, data=json.dumps(data))
    # print("번역 확인 : {text}".format(text=response.json()[0]["translations"]))
    return response.json()[0]["translations"]


def get_current_time():
    return int(round(time.time() * 1000))


class MicrophoneStream:
    def __init__(self, rate, chunk_size, audio_interface=pyaudio.PyAudio(), mic_info=None):
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
        self._buff = queue.Queue()
        # 시간 정보를 기준으로 마이크 입력 데이터를 끊음.
        self.start_time = get_current_time()
        self.closed = True
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True

        # 마이크 설정
        self._audio_stream = audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            # 오디오 스트림을 비동기식으로 실행
            # 네트워크 요청 수행 중, 오버헤드 발생.
            stream_callback=self._fill_buffer,
            # 디바이스 지정 인덱싱
            input_device_index=None if mic_info is None else mic_info['index']
        )

    def __enter__(self):
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        print("MicrophoneStream 종료됨")

    def _fill_buffer(self, in_data, *args, **kwargs):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            data = []

            if self.new_stream and self.last_audio_input:

                chunk_time = STREAMING_LIMIT / len(self.last_audio_input)

                if chunk_time != 0:
                    if self.bridging_offset < 0:
                        self.bridging_offset = 0

                    if self.bridging_offset > self.final_request_end_time:
                        self.bridging_offset = self.final_request_end_time

                    chunks_from_ms = round(
                        (self.final_request_end_time - self.bridging_offset) / chunk_time
                    )

                    self.bridging_offset = round(
                        (len(self.last_audio_input) - chunks_from_ms) * chunk_time
                    )

                    for i in range(chunks_from_ms, len(self.last_audio_input)):
                        data.append(self.last_audio_input[i])

                self.new_stream = False

            chunk = self._buff.get()
            self.audio_input.append(chunk)

            if chunk is None:
                return
            data.append(chunk)

            while True:
                try:
                    chunk = self._buff.get(block=False)

                    if chunk is None:
                        return

                    data.append(chunk)
                    self.audio_input.append(chunk)

                except queue.Empty:
                    break

            yield b"".join(data)

    def clear_buff(self):
        self._buff.put(None)
