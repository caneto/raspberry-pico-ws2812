import array, time
from machine import Pin
import rp2

############################################
# RP2040 PIO e configurações de pinos
############################################
#
# Configuração do anel LED WS2812
led_count = 16 # number of LEDs in ring light
PIN_NUM = 13 # pin connected to ring light
brightness = 0.5 # 0.1 = darker, 1.0 = brightest

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=24) # PIO configuration

# define WS2812 parameters
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()


# Crie o StateMachine com o programa ws2812, produzindo no pino pré-definido
# na frequência de 8 MHz
state_mach = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))

# Ative a máquina de estado
state_mach.active(1)

# Gama de LEDs armazenados em uma matriz
pixel_array = array.array("I", [0 for _ in range(led_count)])
#
############################################
# Funções para coloração RGB
############################################
#
def update_pix(brightness_input=brightness): # escurecendo as cores e atualizando a máquina de estado (state_mach)
    dimmer_array = array.array("I", [0 for _ in range(led_count)])
    for ii,cc in enumerate(pixel_array):
        r = int(((cc >> 8) & 0xFF) * brightness_input) # Vermelho de 8 bits esmaecido para brilho
        g = int(((cc >> 16) & 0xFF) * brightness_input) # Verde de 8 bits esmaecido para o brilho
        b = int((cc & 0xFF) * brightness_input) # Azul de 8 bits esmaecido para o brilho
        dimmer_array[ii] = (g<<16) + (r<<8) + b # Cor de 24 bits esmaecida para brilho
    state_mach.put(dimmer_array, 8) # atualize a máquina de estado com novas cores
    time.sleep_ms(10)

def set_24bit(ii, color): # definir cores para o formato de 24 bits dentro do pixel_array
    pixel_array[ii] = (color[1]<<16) + (color[0]<<8) + color[2] # set 24-bit color

#
############################################
# Loops e chamadas principais
############################################
#
color = (255,0,0) # looping color
blank = (255,255,255) # color for other pixels
cycles = 5 # number of times to cycle 360-degrees
for ii in range(int(cycles*len(pixel_array))+1):
    for jj in range(len(pixel_array)):
        if jj==int(ii%led_count): # no caso de passarmos pelo número de pixels na matriz
            set_24bit(jj,color) # pinte e faça um loop em um único pixel
        else:
            set_24bit(jj,blank) # desligar outros
    update_pix() # update pixel colors
    time.sleep(0.05) # wait 50ms