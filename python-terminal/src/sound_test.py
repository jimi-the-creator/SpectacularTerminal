import pygame
import math
import array
import time

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

print("Mixer initialized as:", pygame.mixer.get_init())

def make_test_tone(freq=650, duration_ms=350, volume=0.8):
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    samples = array.array("h")

    for i in range(n_samples):
        t = i / sample_rate
        envelope = math.exp(-3 * t)
        wave = math.sin(2 * math.pi * freq * t)
        value = int(32767 * volume * wave * envelope)

        samples.append(value)
        samples.append(value)

    return pygame.mixer.Sound(buffer=samples.tobytes())

sound = make_test_tone()
sound.play()

time.sleep(1)

pygame.quit()
