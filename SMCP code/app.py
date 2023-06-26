from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import requests, json
import urllib.request
import pickle
from flask_socketio import SocketIO, emit
import time,threading
app = Flask(__name__)
socketio = SocketIO(app)
# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smcp',
}

try:
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    print('Connected to the database')
except mysql.connector.Error as error:
    print('Failed to connect to the database:', error)








@app.route('/')
def main():
    '''
    query = 'SELECT temperature, humidity, moisture FROM data_sensor ORDER BY datetime DESC LIMIT 1'
    cursor.execute(query)
    values = cursor.fetchone()
    temp = values[0]
    humid = values[1]
    mois = values[2]
    '''
    return render_template('main.html')



@socketio.on('connect')
def handle_connect():
    query = 'SELECT temperature, humidity, moisture FROM data_sensor ORDER BY datetime DESC LIMIT 1'
    cursor.execute(query)
    values = cursor.fetchone()
    temp = values[0]
    humid = values[1]
    mois = values[2]
    emit('initial_values', {'temperature': temp, 'humidity': humid, 'moisture': mois})

def listen_for_changes():
    # Function to listen for database changes
    while True:
        
        query = 'SELECT temperature, humidity, moisture FROM data_sensor ORDER BY datetime DESC LIMIT 1'
        cursor.execute(query)
        values = cursor.fetchone()
        temp = values[0]
        humid = values[1]
        mois = values[2]
        socketio.emit('update_values', {'temperature': temp, 'humidity': humid, 'moisture': mois}, broadcast=True)
        
        time.sleep(5)

# Start the thread to listen for changes in the database
change_thread = threading.Thread(target=listen_for_changes)
change_thread.start()



@app.route('/irrigation')
def irrigation():
    sm = get_soil_moisture()
    w = get_rainfall_forecast()
    IrrigationNeeds = is_irrigation_needed()
    return render_template('irrigation.html', soil_moisture=sm ,rain_forecast = w, IN = IrrigationNeeds)


@app.route('/crop-prediction', methods=['GET', 'POST'])
def crop_prediction():
    query = 'SELECT temperature, humidity FROM data_sensor ORDER BY datetime DESC LIMIT 1'
    cursor.execute(query)
    values = cursor.fetchone()
    temp = values[0]
    humid = values[1]

    if request.method == 'POST':
        n_value = float(request.form.get('n'))
        p_value = float(request.form.get('p'))
        k_value = float(request.form.get('k'))
        ph_value = float(request.form.get('ph'))
        rf_value = float(request.form.get('rainfall'))
        crop_result = get_crop_prediction(n_value, p_value, k_value, ph_value, temp, humid, rf_value)
        query = 'INSERT INTO improvement (N, P, K, temperature, humidity, pH, rainfall, crop) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (n_value, p_value, k_value, temp, humid, ph_value, rf_value, crop_result)) 
        db.commit()
        return redirect(url_for('prediction', crop_result=crop_result))
    
    return render_template('cropPrediction.html')
    
    

@app.route('/prediction', methods=['GET','POST'])
def prediction():
    crop_result = request.args.get('crop_result')
    return render_template('prediction.html',crop_result=crop_result)






# ---------------------------------------------------------------------------------------------------------------------------------------





# get the latest soil moisture value from the database
def get_soil_moisture():
    query = 'SELECT moisture FROM data_sensor ORDER BY datetime DESC LIMIT 1'
    cursor.execute(query)
    soil_moisture = cursor.fetchone()[0]
    return soil_moisture



# rain forecast api
def get_rainfall_forecast ():
    APIkey = 'be9601b548361368d0841019aa62d1af'
    baseURL = 'https://api.openweathermap.org/data/2.5/weather?q=constantine'
    cURL = baseURL + '&appid=' + APIkey

    w = requests.get(cURL)

    with urllib.request.urlopen(cURL) as url:
         data = json.loads(url.read().decode())
         weather = data["clouds"]["all"]
         
    return weather

#irrigation decision
def is_irrigation_needed():
    soil_moisture = get_soil_moisture()
    rainfall = get_rainfall_forecast()

    if soil_moisture >= 800 and rainfall< 90 :
        return "Irrigation needed!"
    else:
        return "Irrigation is not needed."
    

#crop prediction ml
def get_crop_prediction(n_value, p_value, k_value, ph_value, temp, humid, rf_value):
    
    model_loaded = pickle.load(open('crop_prediction.pkl','rb'))
    datalist = [[n_value, p_value, k_value, ph_value, temp, humid, rf_value]]
    print(datalist)
    result = model_loaded.predict(datalist)
    print(result)
    crop_dict = {
    'rice': 1,
    'maize': 2,
    'jute': 3,
    'cotton': 4,
    'coconut': 5,
    'papaya': 6,
    'orange': 7,
    'apple': 8,
    'muskmelon': 9,
    'watermelon': 10,
    'grapes': 11,
    'mango': 12,
    'banana': 13,
    'pomegranate': 14,
    'lentil': 15,
    'blackgram': 16,
    'mungbean': 17,
    'mothbeans': 18,
    'pigeonpeas': 19,
    'kidneybeans': 20,
    'chickpea': 21,
    'coffee': 22
    }
    
    rs = remap_result(result, crop_dict)
    return rs




#remaping crops
def remap_result(result, crop_dict):
    
    for crop_name, crop_id in crop_dict.items():
        if crop_id == result:
            return crop_name
    
    return None




        

if __name__ == '__main__':
    app.run(debug=True)
