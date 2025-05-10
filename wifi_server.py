import network
import socket
import json
from time import sleep

class WiFiServer:
    def __init__(self, ssid="SolarMeter", password="12345678"):
        self.ap = network.WLAN(network.AP_IF)
        self.ssid = ssid
        self.password = password
        self.socket = None
        self.current_data = {}
        
    def start(self):
        # Configurar AP
        self.ap.active(True)
        self.ap.config(essid=self.ssid, password=self.password)
        while not self.ap.active():
            sleep(0.1)
        
        # Configurar servidor web
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', 80))
        self.socket.listen(5)
        self.socket.setblocking(False)
        print(f"AP activo. SSID: {self.ssid}, IP: {self.ap.ifconfig()[0]}")
        
    def handle_clients(self):
        """Maneja nuevas conexiones y datos de clientes"""
        try:
            # Verificar nuevas conexiones
            try:
                client, addr = self.socket.accept()
                print(f"Nueva conexión desde {addr}")
                
                # Leer la solicitud
                request = client.recv(1024).decode()
                
                # Determinar qué página servir
                if 'GET /data' in request:
                    self.serve_data(client)
                else:
                    self.serve_page(client)
                    
                client.close()
            except:
                pass
                
        except Exception as e:
            print(f"Error manejando clientes: {e}")
    
    def broadcast(self, data):
        """Actualiza los datos actuales"""
        self.current_data = json.loads(data)
        
    def serve_data(self, client):
        """Envía los datos actuales como JSON"""
        response = json.dumps(self.current_data)
        client.send('HTTP/1.1 200 OK\n')
        client.send('Content-Type: application/json\n')
        client.send('Access-Control-Allow-Origin: *\n')
        client.send('Connection: close\n\n')
        client.send(response.encode())
        
    def serve_page(self, client):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Solar Meter</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { 
                    font-family: Arial; 
                    margin: 20px;
                    background-color: #f0f0f0;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    text-align: center;
                }
                .value {
                    font-size: 24px;
                    margin: 15px 0;
                    padding: 10px;
                    background: #f8f8f8;
                    border-radius: 5px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .label {
                    color: #666;
                }
                .number {
                    font-weight: bold;
                    color: #333;
                }
                .status {
                    text-align: center;
                    color: #666;
                    margin-top: 20px;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Solar Meter</h1>
                <div class="value">
                    <span class="label">Corriente:</span>
                    <span class="number"><span id="current">--</span> mA</span>
                </div>
                <div class="value">
                    <span class="label">Irradiancia:</span>
                    <span class="number"><span id="irradiance">--</span> W/m&sup2;</span>
                </div>
                <div class="value">
                    <span class="label">Temperatura:</span>
                    <span class="number"><span id="temp">--</span> &deg;C</span>
                </div>
                <div class="value">
                    <span class="label">Humedad:</span>
                    <span class="number"><span id="humidity">--</span> %</span>
                </div>
                <div class="status" id="status">Conectando...</div>
            </div>
            
            <script>
                let failedAttempts = 0;
                const status = document.getElementById('status');
                
                function updateValues() {
                    fetch('/data')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('current').textContent = data.current.toFixed(1);
                            document.getElementById('irradiance').textContent = data.irradiance.toFixed(1);
                            document.getElementById('temp').textContent = data.temperature.toFixed(1);
                            document.getElementById('humidity').textContent = data.humidity.toFixed(1);
                            status.textContent = 'Conectado - Actualizando en vivo';
                            status.style.color = '#4CAF50';
                            failedAttempts = 0;
                        })
                        .catch(error => {
                            failedAttempts++;
                            status.textContent = `Error de conexión (intento ${failedAttempts})`;
                            status.style.color = '#f44336';
                        });
                }
                
                // Actualizar cada segundo
                setInterval(updateValues, 1000);
                updateValues();  // Primera actualización
            </script>
        </body>
        </html>
        """
        client.send('HTTP/1.1 200 OK\n')
        client.send('Content-Type: text/html\n')
        client.send('Connection: close\n\n')
        client.send(html.encode())