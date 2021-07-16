import array, time
from machine import Pin
import rp2

############################################
# RP2040 PIO e configurações de pinos
############################################
#
# Configuração do anel LED WS2812
led_count = 16 # número de LEDs no anel de luz
PIN_NUM = 13 # pino conectado ao anel de luz
brightness = 1.0 # 0.1 = darker, 1.0 = brightest

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=24) # PIO configuration

# define os parâmetros WS2812
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
    color = hex_to_rgb(color)
    pixel_array[ii] = (color[1]<<16) + (color[0]<<8) + color[2] # definir cor de 24 bits
    
def hex_to_rgb(hex_val):
    return tuple(int(hex_val.lstrip('#')[ii:ii+2],16) for ii in (0,2,4))

############################################
# Loops e chamadas principais
############################################
#
# Crie o esquema de rotação de quatro cores do Google Home
google_colors = ['#4285f4','#ea4335','#fbbc05','#34a853'] # cores hexadecimais do Google
cycles = 5 # número de vezes para fazer um ciclo de 360 graus
for jj in range(int(cycles*len(pixel_array))):
    for ii in range(len(pixel_array)):
        if ii%int(len(pixel_array)/4)==0: # Leds de 90 graus apenas
            set_24bit((ii+jj)%led_count,google_colors[int(ii/len(pixel_array)*4)])
        else:
            set_24bit((ii+jj)%led_count,'#000000') # outros pixels em branco
    update_pix() # atualizar cores de pixel
    time.sleep(0.05) # espere entre as mudanças

# Criar roda de rotação Amazon Alexa
amazon_colors = ['#00dbdc','#0000d4'] # cores hexadecimais da Amazon
light_width = 3 # largura da matriz rotativa de led
cycles = 3 # número de vezes que a largura gira 360 graus
for jj in range(int(cycles*len(pixel_array))):
    for ii in range(len(pixel_array)):
        if ii<light_width: 
            set_24bit((ii+jj)%led_count,amazon_colors[0])
        else:
            set_24bit((ii+jj)%led_count,amazon_colors[1]) # outros pixels em branco
    update_pix() # atualizar cores de pixel
    time.sleep(0.03) # espere entre as mudanças
time.sleep(0.5)

# desligue os LEDs usando o desligamento tipo zíper Alexa
for ii in range(int(len(pixel_array)/2)):
    set_24bit(ii,'#000000') # desligue o lado positivo
    set_24bit(int(len(pixel_array)-ii-1),'#000000') # desligue o lado positivo
    update_pix() # atualize
    time.sleep(0.02) # espere