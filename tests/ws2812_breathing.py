import array, time
from machine import Pin
import rp2

############################################
# RP2040 PIO e configurações de pinos
############################################
#
# Configuração do anel LED WS2812
led_count = 16 # número de LEDs no anel de luz
PIN_NUM = 13 # pin connected to ring light
brightness = 1.0 # 0.1 = darker, 1.0 = brightest

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=24) # configuração PIO

# definir parâmetros WS2812
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
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))

# Ative a máquina de estado
sm.active(1)

# Gama de LEDs armazenados em uma matriz
ar = array.array("I", [0 for _ in range(led_count)])
#
############################################
# Funções para coloração RGB
############################################
#
def pixels_show(brightness_input=brightness):
    dimmer_ar = array.array("I", [0 for _ in range(led_count)])
    for ii,cc in enumerate(ar):
        r = int(((cc >> 8) & 0xFF) * brightness_input) # Vermelho de 8 bits esmaecido para brilho
        g = int(((cc >> 16) & 0xFF) * brightness_input) # Verde de 8 bits esmaecido para o brilho
        b = int((cc & 0xFF) * brightness_input) # Azul de 8 bits esmaecido para o brilho
        dimmer_ar[ii] = (g<<16) + (r<<8) + b # Cor de 24 bits esmaecida para brilho
    sm.put(dimmer_ar, 8) # update the state machine with new colors
    time.sleep_ms(10)

def pixels_set(i, color):
    ar[i] = (color[1]<<16) + (color[0]<<8) + color[2] # set 24-bit color
        
def breathing_led(color):
    step = 5
    breath_amps = [ii for ii in range(0,255,step)]
    breath_amps.extend([ii for ii in range(255,-1,-step)])
    for ii in breath_amps:
        for jj in range(len(ar)):
            pixels_set(jj, color) # mostrar todas as cores
        pixels_show(ii/255)
        time.sleep(0.02)
#
############################################
# Principais chamadas e loops
############################################
#
# color specifications
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
yellow = (255,255,0)
cyan = (0,255,255)
white = (255,255,255)
blank = (0,0,0)
colors = [blue,yellow,cyan,red,green,white]

while True: # loop indefinidamente
    for color in colors: # emular LED de respiração (semelhante ao Alexa da Amazon)
        breathing_led(color)
        time.sleep(0.1) # espere entre as cores