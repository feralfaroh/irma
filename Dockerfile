# Usa la imagen base oficial de Azure Functions para Python (en este ejemplo, Python 3.12)
FROM mcr.microsoft.com/azure-functions/python:4-python3.12

# Actualiza los repositorios e instala Chromium (nota: usa el paquete "chromium" en lugar de "chromium-browser")
RUN apt-get update && \
    apt-get install -y chromium && \
    rm -rf /var/lib/apt/lists/*

# Define la variable de entorno para que Selenium encuentre el binario de Chromium
ENV CHROME_BIN=/usr/bin/chromium

# Copia todo el contenido de tu proyecto en el contenedor
COPY . /home/site/wwwroot

# (Opcional) Expone el puerto 80, que es el puerto interno de la Function App
EXPOSE 80
