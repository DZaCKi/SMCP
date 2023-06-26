#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#define SENSOR_PIN A0
#include <DHT.h> 
#define DHTPIN D4  
#define DHTTYPE DHT11 
DHT dht(DHTPIN, DHTTYPE); 
WiFiClient client;
String URL = "http://192.168.43.228/SMCP/datahandler.php";

const char* serverUrl = "http://127.0.0.1:5000/";
const char* ssid = "Zack";
const char* password = "12345678"; 

float temperature = 0.0;
float humidity = 0.0;
int moisture = 0;

void setup() {
  Serial.begin(115200);

  dht.begin(); 
  
  connectWiFi();
}

void loop() {
  if(WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  Load_sensor_Data();
  String postData = "temperature=" + String(temperature) + "&humidity=" + String(humidity) + "&moisture=" +String(moisture);
  
  HTTPClient http;
  http.begin(client, URL);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  int httpCode = http.POST(postData);
  String payload = "";

  if(httpCode > 0) {
    // file found at server
    if(httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      Serial.println(payload);
    } else {
      // HTTP header has been send and Server response header has been handled
      Serial.printf("[HTTP] GET... code: %d\n", httpCode);
    }
  } else {
    Serial.printf("[HTTP] GET... failed, error: %s\n", http.errorToString(httpCode).c_str());
  }
  
  http.end();  //Close connection

  Serial.print("URL : "); Serial.println(URL); 
  Serial.print("Data: "); Serial.println(postData);
  Serial.print("httpCode: "); Serial.println(httpCode);
  Serial.print("payload : "); Serial.println(payload);
  Serial.println("--------------------------------------------------");


  delay(20000);
}


void Load_sensor_Data() {
  //-----------------------------------------------------------
   temperature = dht.readTemperature(); //Celsius
   humidity = dht.readHumidity();
   moisture = analogRead(SENSOR_PIN);
  //-----------------------------------------------------------
  // Check if any reads failed.
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
    temperature = 0;
    humidity = 0;
  }
  //-----------------------------------------------------------
  Serial.printf("Temperature: %d °C\n", temperature);
  Serial.printf("Humidity: %d %%\n", humidity);
  Serial.printf("Moisture: %d \n", moisture);
}

void connectWiFi() {
  WiFi.mode(WIFI_OFF);
  delay(1000);
  //This line hides the viewing of ESP as wifi hotspot
  WiFi.mode(WIFI_STA);
  
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
    
  Serial.print("connected to : "); Serial.println(ssid);
  Serial.print("IP address: "); Serial.println(WiFi.localIP());
}