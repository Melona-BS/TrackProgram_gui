import sys
from threading import Thread

import pygame
from pygame.locals import *

import pyaudio
import pyautogui

FPS = 30
SAMPLE_RATE = 44100
CHUNK_SIZE = int(SAMPLE_RATE / 10)


class TrackProgram(Thread):
    def __init__(self, lang_info=("한국어", "영어"), font_size=48, display_mode='양방향'):
        super().__init__(daemon=True)
        # 기기 정보 초기화
        self.name = "track_program"
        pygame.init()
        pygame.display.init()
        self.clock = pygame.time.Clock()
        self.screen = None
        # Surface 설정
        self.displaySize = pyautogui.size()
        self.left_surface = pygame.surface.Surface((int(self.displaySize.width / 2), self.displaySize.height))
        self.right_surface = pygame.surface.Surface((int(self.displaySize.width / 2), self.displaySize.height))
        self.scroll_y = 0
        self.surface_height = self.displaySize.height
        # 텍스트 설정
        self.fontSize = font_size
        self.left_lang = lang_info[0]
        self.right_lang = lang_info[1]
        self.left_font = self.set_language_font(self.left_lang)
        self.right_font = self.set_language_font(self.right_lang)
        self.left_text = []
        self.right_text = []
        # 텍스트 그래픽 설정
        self.left_y = 20
        self.right_y = 20
        self.line_count = 0
        self.line_height = []
        # 자막 모드 설정
        self.mode = display_mode
        # Program 시작 트리거 설정
        self.running = True

    def run(self):
        # 스크린 설정
        self.screen = pygame.display.set_mode(self.displaySize, FULLSCREEN)
        self.screen.fill((255, 255, 255))
        self.screen.blit(self.left_surface, (0, self.scroll_y))
        self.screen.blit(self.right_surface, (self.screen.get_width() / 2, self.scroll_y))
        self.line_height.append(max(self.left_y, self.right_y))
        while self.running:
            self.events()
            self.clock.tick(FPS)
        print('quit track')
        pygame.quit()

    def stop(self):
        self.running = False

    def events(self):
        mouse = pygame.mouse.get_pos()
        # 이벤트 처리 코드
        for event in pygame.event.get():
            # 윈도우 창닫기 버튼
            if event.type == pygame.QUIT:
                self.running = False
            # 스크롤 이벤트
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.displaySize.height == self.surface_height:
                    return
                # wheel up
                if event.button == 4:
                    if min(self.scroll_y, 0) != 0:
                        self.scroll_y = min(self.scroll_y + 50, 0)
                        self.screen.blit(self.left_surface, (0, self.scroll_y))
                        self.screen.blit(self.right_surface, (self.screen.get_width() / 2, self.scroll_y))
                        pygame.display.flip()
                # wheel down
                elif event.button == 5:
                    if max(self.scroll_y, -self.surface_height + self.displaySize.height) != -self.surface_height + self.displaySize.height:
                        self.scroll_y = max(self.scroll_y - 50, -self.surface_height + self.displaySize.height)
                        self.screen.blit(self.left_surface, (0, self.scroll_y))
                        self.screen.blit(self.right_surface, (self.screen.get_width() / 2, self.scroll_y))
                        pygame.display.flip()

    def growth_height_surface(self):
        self.surface_height = self.surface_height + self.displaySize.height
        temp_surface = pygame.surface.Surface((int(self.displaySize.width / 2), self.surface_height))
        temp_surface.blit(self.left_surface.copy(), (0, 0))
        self.left_surface = temp_surface
        temp_surface = pygame.surface.Surface((int(self.displaySize.width / 2), self.surface_height))
        temp_surface.blit(self.right_surface.copy(), (0, 0))
        self.right_surface = temp_surface

    def realize_left(self, new_text):
        self.left_surface.fill(pygame.Color(0, 0, 0))
        realize_text_list = self.left_text + [new_text]
        self.draw_left(self.left_surface, realize_text_list, (20, 20), self.left_font, (20, 20))
        if (self.displaySize.height - self.scroll_y) < self.left_y:
            # 카메라 위치 고정 코드
            camera_y = self.scroll_y - (self.left_y - (self.displaySize.height - self.scroll_y))
            self.screen.blit(self.left_surface, (0, camera_y))
            self.screen.blit(self.right_surface, (self.screen.get_width() / 2, self.scroll_y))
        pygame.display.flip()

    def realize_right(self, new_text):
        self.right_surface.fill(pygame.Color(0, 0, 0))
        realize_text_list = self.right_text + [new_text]
        self.draw_right(self.right_surface, realize_text_list, (20, 20), self.right_font, (20, 20))
        if (self.displaySize.height - self.scroll_y) < self.right_y:
            # 카메라 위치 고정 코드
            camera_y = self.scroll_y - (self.right_y - (self.displaySize.height - self.scroll_y))
            self.screen.blit(self.right_surface, (0, camera_y))
            self.screen.blit(self.right_surface, (self.screen.get_width() / 2, self.scroll_y))
        pygame.display.flip()

    def append_left(self, new_text):
        self.left_surface.fill(pygame.Color(0, 0, 0))
        self.left_text.append(new_text)
        self.draw_left(self.left_surface, self.left_text, (20, 20), self.left_font, (20, 20))

    def append_right(self, new_text):
        self.right_surface.fill(pygame.Color(0, 0, 0))
        self.right_text.append(new_text)
        self.draw_right(self.right_surface, self.right_text, (20, 20), self.right_font, (20, 20))

    def append_both(self, left_text, right_text):
        self.append_left(left_text)
        self.append_right(right_text)
        # 높이 갱신
        self.line_height.append(max(self.left_y, self.right_y))
        # 높이 갱신에 따른 화면 사이즈 갱신
        if self.line_height[-1] + self.fontSize * 5 > self.surface_height:
            self.growth_height_surface()
            pygame.display.flip()
        # 사이즈 갱신 후, 화면 스크롤
        if self.line_height[-1] >= self.displaySize.height:
            # 카메라 위치 고정 코드
            self.scroll_y += (-self.line_height[-1]) + self.line_height[-2]
            self.screen.blit(self.screen, (0, self.scroll_y))
            pygame.display.flip()
        self.screen.blit(self.left_surface, (0, self.scroll_y))
        self.screen.blit(self.right_surface, (self.screen.get_width() / 2, self.scroll_y))
        pygame.display.flip()

    def draw_left(self, surface, new_text, position, font, padding=(0, 0), color=pygame.Color('white')):
        line_count = 0
        for text in new_text:
            words = [list(word) for word in text.split('\n')]
            space = font.size(' ')[0]
            max_width, max_height = (surface.get_width() - padding[0], surface.get_height() - padding[1])
            x = position[0] + padding[0]
            y = self.line_height[line_count] + padding[1]
            for line in words:
                for word in line:
                    word_surface = font.render(word, 0, color)
                    word_width, word_height = word_surface.get_size()
                    if x + word_width >= max_width:
                        x = position[0] + padding[0]
                        y += word_height
                    surface.blit(word_surface, (x, y))
                    x += word_width + space
                x = position[0]
                y += word_height
                self.left_y = y
            line_count += 1
        self.screen.blit(self.left_surface, (0, self.scroll_y))
        pygame.display.flip()

    def draw_right(self, surface, new_text, position, font, padding=(0, 0), color=pygame.Color('white')):
        line_count = 0
        for text in new_text:
            words = [list(word) for word in text.split('\n')]
            space = font.size(' ')[0]
            max_width, max_height = (surface.get_width() - padding[0], surface.get_height() - padding[1])
            x = position[0] + padding[0]
            y = self.line_height[line_count] + padding[1]
            for line in words:
                for word in line:
                    word_surface = font.render(word, 0, color)
                    word_width, word_height = word_surface.get_size()
                    if x + word_width >= max_width:
                        x = position[0] + padding[0]
                        y += word_height
                    surface.blit(word_surface, (x, y))
                    x += word_width + space
                x = position[0]
                y += word_height
            self.right_y = y
            line_count += 1
        # 텍스트 뒤집기
        if self.mode == '양방향':
            self.right_surface = pygame.transform.flip(self.right_surface, True, False)
        self.screen.blit(self.right_surface, (self.screen.get_width() / 2, self.scroll_y))
        pygame.display.flip()

    def set_language_font(self, language):
        if language == '한국어':
            print("한국어 폰트 설정됨.")
            return pygame.font.Font("NotoSansKR-Black.otf", self.fontSize)
        elif language == '중국어':
            print("중국어 폰트 설정됨.")
            return pygame.font.Font("NotoSansSC-Black.otf", self.fontSize)
        elif language == '일본어':
            print("일본어 폰트 설정됨.")
            return pygame.font.Font("NotoSansJP-Black.ttf", self.fontSize)
        else:
            print("기본 폰트 설정됨.")
            return pygame.font.Font("NotoSansCJK-Bold.ttc", self.fontSize)

    def set_fontSize(self, font_size):
        self.fontSize = int(font_size)

    def set_mode(self, mode):
        self.mode = mode
