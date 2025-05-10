from machine import Pin, ADC
from time import sleep, ticks_ms, ticks_diff
import i2c_lcd
import dht
import json
from wifi_server import WiFiServer

# Constantes como en Arduino original
DECIMAL_PRECISION = 2                    # decimal places for current value
MV_PER_AMP_VALUE = 1000                 # WCS2702 current module for 2.0A
MODULE_MIDDLE_VOLTAGE = 2500            # for 5V power supply
MODULE_SUPPLY_VOLTAGE = 5000            # 5V power supply in mV

# Solar Panel Specifications at STC (1000 W/m²)
SHORT_CIRCUIT_CURRENT_STC = 0.300       # Short Circuit Current in A
IRRADIATION_STC = 1000                  # W/m² at STC condition

# Configuración de pines
adc = ADC(Pin(1))                       # Current Analog Input Pin
adc.atten(ADC.ATTN_11DB)               # Full range: 0-3.3V
cal_button = Pin(15, Pin.IN, Pin.PULL_UP)  # Botón de calibración con pull-up
dht_sensor = dht.DHT22(Pin(4))          # DHT22 en GPIO4

class SolarMeter:
    def __init__(self):
        self.current_offset = 0
        self.current_sample_sum = 0
        self.current_sample_count = 0
        self.final_current = 0
        self.irradiation = 0
        self.temperature = 0
        self.humidity = 0
        self.lcd = i2c_lcd.LCD(scl_pin=22, sda_pin=21)
        self.wifi = WiFiServer()
        self.wifi.start()
        
    def read_dht(self):
        """Lee temperatura y humedad del DHT22"""
        try:
            dht_sensor.measure()
            self.temperature = dht_sensor.temperature()
            self.humidity = dht_sensor.humidity()
            return True
        except:
            print("Error leyendo DHT22")
            return False
            
    def read_raw_samples(self, num_samples=1000):
        """Lee muestras crudas del ADC como en Arduino"""
        current_sum = 0
        for _ in range(num_samples):
            raw = adc.read()
            # Convertir directamente como en Arduino
            adjusted = raw - ((MODULE_MIDDLE_VOLTAGE/MODULE_SUPPLY_VOLTAGE) * 4095)
            current_sum += adjusted
            sleep(0.001)
        return current_sum / num_samples
        
    def read_current(self):
        """Lee la corriente actual como en Arduino"""
        # Obtener promedio de 1000 muestras
        current_mean = self.read_raw_samples(1000)
        
        # Convertir a corriente como en Arduino
        self.final_current = (((current_mean / 4095) * MODULE_SUPPLY_VOLTAGE) / MV_PER_AMP_VALUE)
        
        # Aplicar offset
        self.final_current = self.final_current + self.current_offset
        return max(0, self.final_current)
        
    def calculate_irradiation(self, current):
        """Calcula irradiación como en Arduino"""
        if current < 0.0001:  # Si la corriente es muy baja
            return 0
        # Irradiation = (finalCurrent2/ShortCircuitCurrentSTC*1000)
        return (current / SHORT_CIRCUIT_CURRENT_STC) * IRRADIATION_STC
        
    def calibrate(self):
        """Calibra el offset como en Arduino"""
        self.lcd.clear()
        self.lcd.write("INITIALIZING....")
        print("Calibrating...")
        
        # Obtener promedio directamente
        current_mean = self.read_raw_samples(1000)
        
        # Calcular corriente sin offset
        current = (((current_mean / 4095) * MODULE_SUPPLY_VOLTAGE) / MV_PER_AMP_VALUE)
        
        # Establecer offset
        self.current_offset = -current
        
        self.lcd.clear()
        self.lcd.write("OFFSET DONE")
        print(f"Offset: {self.current_offset:.3f}")
        sleep(1)
        self.lcd.clear()
        
    def get_json_data(self):
        """Retorna datos en formato JSON"""
        return json.dumps({
            'current': self.final_current * 1000,  # en mA
            'irradiance': self.calculate_irradiation(self.final_current),  # Calcular en el momento
            'temperature': self.temperature,
            'humidity': self.humidity
        })
        
    def main_loop(self):
        self.lcd.clear()
        self.lcd.write("SOLAR STATION")
        sleep(1)
        
        # Calibración inicial
        self.calibrate()
        
        last_button = True  # Estado anterior del botón
        last_update = ticks_ms()
        last_dht_read = ticks_ms()
        
        while True:
            try:
                # Verificar botón
                button = cal_button.value()  # Lee el estado actual (0 = presionado, 1 = no presionado)
                if button == 0 and last_button == 1:  # Detecta el flanco de bajada (cuando se presiona)
                    print("Botón presionado - Recalibrando...")
                    self.calibrate()
                last_button = button
                
                # Actualizar cada 1 segundo
                now = ticks_ms()
                if ticks_diff(now, last_update) >= 1000:
                    # Leer valores
                    final_current = self.read_current()
                    irradiation = self.calculate_irradiation(final_current)
                    
                    # Leer DHT22 cada 2 segundos
                    if ticks_diff(now, last_dht_read) >= 2000:
                        self.read_dht()
                        last_dht_read = now
                    
                    # Enviar datos por WebSocket
                    self.wifi.broadcast(self.get_json_data())
                    
                    # Debug
                    print(f"I: {final_current*1000:.2f}mA, W: {irradiation:.2f}W/m², T: {self.temperature:.1f}°C, H: {self.humidity:.1f}%")
                    
                    # Display LCD
                    self.lcd.set_cursor(0, 0)
                    if final_current < 0.0001:
                        self.lcd.write("NO CURRENT      ")
                    else:
                        self.lcd.write(f"{self.temperature:>4.1f}C")
                        self.lcd.set_cursor(0, 6)
                        self.lcd.write(f"{irradiation:>6.1f}W/m2")
                    
                    self.lcd.set_cursor(1, 0)
                    self.lcd.write(f"{self.humidity:>4.1f}%")
                    self.lcd.set_cursor(1, 6)
                    self.lcd.write(f"{final_current*1000:>6.1f}mA")
                    
                    last_update = now
                    
                # Manejar conexiones web
                self.wifi.handle_clients()
                    
                sleep(0.01)
                
            except Exception as e:
                print(f"Error: {e}")
                sleep(1)

def main():
    meter = SolarMeter()
    meter.main_loop()

if __name__ == "__main__":
    main()