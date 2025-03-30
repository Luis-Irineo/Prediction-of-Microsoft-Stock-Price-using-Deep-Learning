# -*- coding: utf-8 -*-
"""Predicción del Stock de  Microsoft vía Deeplearning por Datos Mayores a la Media

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1zeZE6okhCmLrL9IhCGrjsZvra4b7N1vj
"""

# Si usas Google Colab

#from google.colab import drive
#drive.mount("/content/drive")
#import os
#os.chdir("Tu_directorio_de_colab")

# Se importan las librerias
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar los datos de entrenamiento
train_data = pd.read_csv('Microsoft_Stock.csv', index_col='Date', parse_dates=True)

train_data.describe()

train_data.isna().sum()

sns.heatmap(train_data.corr(), annot=True)
plt.show()

sns.pairplot(train_data)
plt.show()

#train_data = np.round(train_data)
median = train_data.Open.median()
train_data_or = train_data[train_data['Open'] >=median ][['High','Low','Close']]

# Limpieza de datos
train_data_or.replace(['---', '               ---', 'NaN', '', ' '], np.nan, inplace=True)
imputer = SimpleImputer(strategy='mean')
train_data_or = pd.DataFrame(imputer.fit_transform(train_data_or), columns=train_data_or.columns, index=train_data_or.index)

# Escalado de datos
scaler = MinMaxScaler(feature_range=(0, 1))    ###transforma los datos en ceros y uno
train_scaled = scaler.fit_transform(train_data_or)

# Crear secuencias de temporales, datos para el entrenamiento
def create_dataset(dataset, look_back=60):
    X, Y = [], []
    for i in range(len(dataset) - look_back):
        a = dataset[i:(i + look_back), :]
        X.append(a)
        Y.append(dataset[i + look_back, 0])
    return np.array(X), np.array(Y)

X_train, y_train = create_dataset(train_scaled, 60)

# Modelo LSTM
model = Sequential([
    LSTM(100, input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True),  #return_sequences=True Devuelve salidas para cada paso (necesario para apilar LSTM)
    Dropout(0.2), #evita el sobreajuste , apaga aleatoriamete el 20% de las neuronas durante el entrenamiento#
    LSTM(100, return_sequences=False), #return sequences = False nos da la salid final y no toda la secuencia
    Dense(1) #capa final densa
])
model.compile(optimizer=Adam(learning_rate=0.01), loss='mean_squared_error')

model.summary()

# Entrenar el modelo
model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=1)

# Preparar los datos reales de 2024 para comparación
real_data_2024 = pd.read_csv('Microsoft_Stock.csv', index_col='Date', parse_dates=True)
real_data_2024 = real_data_2024[['High','Low','Close']]
real_data_2024.replace(['---', '               ---', 'NaN', '', ' '], np.nan, inplace=True)
real_data_2024 = pd.DataFrame(imputer.transform(real_data_2024), columns=real_data_2024.columns, index=real_data_2024.index)
real_scaled = scaler.transform(real_data_2024)

# Crear datos de entrada para predicción
X_real, _ = create_dataset(np.vstack([train_scaled[-60:], real_scaled]), 60)

# Predicciones
predictions_scaled = model.predict(X_real)
predictions = scaler.inverse_transform(np.concatenate([predictions_scaled, np.zeros((len(predictions_scaled), 2))], axis=1))[:, 0]

# Datos reales para comparar
real_demand = scaler.inverse_transform(real_scaled)[:, 0]

real_demand

# Graficar
plt.figure(figsize=(14, 7))
plt.plot(real_data_2024.index, real_demand, label='Datos Reales', color='blue')
plt.plot(real_data_2024.index[:len(predictions)], predictions, label='Predicciones', color='red')
plt.title('Predicciones vs Datos Reales 2015-2021')
plt.xlabel('Fecha')
plt.ylabel('Estimación del Precio de Venta del Stock')
plt.legend()
plt.grid(True)
plt.show()

import plotly.graph_objects as go
import pandas as pd
from sklearn.metrics import r2_score

# Asegurarse de que tanto 'real_demand' como 'predictions' tienen el mismo índice de tiempo
real_demand = pd.Series(real_demand[:len(predictions)], index=real_data_2024.index[:len(predictions)])
predictions_series = pd.Series(predictions, index=real_data_2024.index[:len(predictions)])

# Crear una lista para almacenar los R-squared de cada mes
r_squared_monthly = []

# Agrupar los datos por mes y calcular el R-squared para cada mes
for month, group in real_demand.groupby(real_demand.index.month):
    # Extraer las predicciones correspondientes para ese mes
    pred_for_month = predictions_series[group.index]

    # Calcular el R-squared
    r_squared = r2_score(group, pred_for_month)

    # Almacenar el resultado
    r_squared_monthly.append((month, r_squared))
    print(f'R-squared para el mes {month}: {r_squared}')

# Crear la figura usando Plotly para una mejor interactividad y presentación
fig = go.Figure()

# Añadir los datos reales a la gráfica
fig.add_trace(go.Scatter(x=real_data_2024.index, y=real_demand, mode='lines', name='Datos Reales', line=dict(color='blue')))

# Añadir las predicciones a la gráfica
fig.add_trace(go.Scatter(x=real_data_2024.index[:len(predictions)], y=predictions, mode='lines', name='Predicciones', line=dict(color='red')))

# Configuración adicional del gráfico
fig.update_layout(
    title='Comparación de Predicciones vs Datos Reales para el periodo 2015-2021',
    xaxis_title='Fecha',
    yaxis_title='Estimación del Precio de Venta del Stock',
    legend_title='Leyenda'
)

# Mostrar la gráfica
fig.show()

# Imprimir los R-squared mensuales
for month, r_squared in r_squared_monthly:
    print(f"R-squared para el mes {month}: {r_squared:.4f}")